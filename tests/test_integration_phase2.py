"""
Phase 2 통합 테스트

UI 분석 워크플로우 및 의미론적 정보 저장 검증

Requirements: 2.1-2.7, 11.1-11.6
"""

import pytest
import os
import json
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer
from src.semantic_action_recorder import SemanticAction, SemanticActionRecorder
from src.input_monitor import Action


class TestPhase2UIAnalysisWorkflow:
    """Phase 2 UI 분석 워크플로우 통합 테스트
    
    Requirements: 2.1-2.7
    """
    
    @pytest.fixture
    def ui_analyzer_env(self, tmp_path):
        """UI 분석 테스트 환경 설정"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # 설정 파일 생성
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "max_tokens": 2000,
                "retry_count": 3,
                "retry_delay": 0.01
            },
            "automation": {
                "screenshot_dir": "screenshots",
                "screenshot_on_action": True
            }
        }

        config_path = tmp_path / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        # 스크린샷 디렉토리 생성
        os.makedirs(tmp_path / "screenshots", exist_ok=True)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        yield {
            "config": config,
            "tmp_path": tmp_path,
            "config_path": config_path
        }
        
        os.chdir(original_cwd)
    
    def test_screenshot_capture_and_save(self, ui_analyzer_env):
        """스크린샷 캡처 및 저장 테스트 (Requirements 2.1)"""
        config = ui_analyzer_env["config"]
        tmp_path = ui_analyzer_env["tmp_path"]
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        # 스크린샷 캡처 (pyautogui.screenshot을 Mock)
        mock_image = Image.new('RGB', (1920, 1080), color='blue')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            save_path = str(tmp_path / "screenshots" / "test_capture.png")
            captured = analyzer.capture_screenshot(save_path)
        
        # 캡처된 이미지 검증
        assert captured is not None
        assert captured.size == (1920, 1080)
        
        # 파일 저장 검증
        assert os.path.exists(save_path)
        
        # 저장된 파일 로드 및 검증
        loaded_image = Image.open(save_path)
        assert loaded_image.size == (1920, 1080)

    def test_image_base64_encoding_workflow(self, ui_analyzer_env):
        """이미지 base64 인코딩 워크플로우 테스트 (Requirements 2.2)"""
        config = ui_analyzer_env["config"]
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        # 테스트 이미지 생성
        original_image = Image.new('RGB', (640, 480), color='red')
        
        # 인코딩
        encoded = analyzer.encode_image_to_base64(original_image)
        
        # 인코딩 결과 검증
        assert isinstance(encoded, str)
        assert len(encoded) > 0
        
        # 디코딩
        decoded = analyzer.decode_base64_to_image(encoded)
        
        # Round trip 검증
        assert decoded.size == original_image.size
        assert decoded.mode == original_image.mode
    
    def test_vision_llm_response_parsing(self, ui_analyzer_env):
        """Vision LLM 응답 파싱 테스트 (Requirements 2.4, 2.7)"""
        config = ui_analyzer_env["config"]
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        # 유효한 JSON 응답
        valid_response = json.dumps({
            "buttons": [
                {"text": "시작", "x": 640, "y": 400, "width": 200, "height": 60, "confidence": 0.95}
            ],
            "icons": [
                {"type": "settings", "x": 1200, "y": 50, "confidence": 0.88}
            ],
            "text_fields": [
                {"content": "플레이어 이름", "x": 500, "y": 300, "confidence": 0.92}
            ]
        })
        
        result = analyzer._parse_ui_response(valid_response)
        
        # 구조 검증
        assert 'buttons' in result
        assert 'icons' in result
        assert 'text_fields' in result
        
        # 버튼 검증
        assert len(result['buttons']) == 1
        assert result['buttons'][0]['text'] == '시작'
        assert result['buttons'][0]['x'] == 640
        assert result['buttons'][0]['y'] == 400
        
        # 아이콘 검증
        assert len(result['icons']) == 1
        assert result['icons'][0]['type'] == 'settings'
        
        # 텍스트 필드 검증
        assert len(result['text_fields']) == 1
        assert result['text_fields'][0]['content'] == '플레이어 이름'

    def test_vision_llm_response_with_code_block(self, ui_analyzer_env):
        """코드 블록으로 감싼 Vision LLM 응답 파싱 (Requirements 2.4)"""
        config = ui_analyzer_env["config"]
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        # 코드 블록으로 감싼 응답
        response_with_block = '''```json
{
    "buttons": [{"text": "확인", "x": 100, "y": 200, "width": 80, "height": 40}],
    "icons": [],
    "text_fields": []
}
```'''
        
        result = analyzer._parse_ui_response(response_with_block)
        
        assert len(result['buttons']) == 1
        assert result['buttons'][0]['text'] == '확인'
    
    def test_vision_llm_retry_with_exponential_backoff(self, ui_analyzer_env):
        """Vision LLM 재시도 지수 백오프 테스트 (Requirements 2.5)"""
        config = ui_analyzer_env["config"]
        
        # Mock Bedrock 클라이언트 - 항상 실패
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("API Error")
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
        
        sleep_calls = []
        
        def mock_sleep(duration):
            sleep_calls.append(duration)
        
        with patch('time.sleep', side_effect=mock_sleep):
            with patch.object(analyzer, 'analyze_with_ocr', return_value=[]):
                test_image = Image.new('RGB', (100, 100), color='white')
                result = analyzer.analyze_with_retry(test_image, retry_count=3)
        
        # 3회 재시도 시 2번의 sleep 호출
        assert len(sleep_calls) == 2
        
        # 지수 백오프 패턴 검증 (0.01 * 2^0, 0.01 * 2^1)
        base_delay = 0.01
        assert abs(sleep_calls[0] - base_delay) < 0.001
        assert abs(sleep_calls[1] - base_delay * 2) < 0.001
        
        # 실패 결과 검증
        assert result.get('source') in ['ocr_fallback', 'failed']

    def test_vision_llm_success_on_retry(self, ui_analyzer_env):
        """Vision LLM 재시도 후 성공 테스트 (Requirements 2.5)"""
        config = ui_analyzer_env["config"]
        
        # Mock 응답 생성
        mock_response = {
            "content": [{"text": json.dumps({
                "buttons": [{"text": "테스트", "x": 100, "y": 100}],
                "icons": [],
                "text_fields": []
            })}]
        }
        
        # Mock Bedrock 클라이언트 - 2번째 시도에서 성공
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = [
            Exception("First failure"),
            {'body': io.BytesIO(json.dumps(mock_response).encode())}
        ]
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
        
        with patch('time.sleep'):
            test_image = Image.new('RGB', (100, 100), color='white')
            result = analyzer.analyze_with_retry(test_image, retry_count=3)
        
        # 성공 결과 검증
        assert result.get('source') == 'vision_llm'
        assert len(result['buttons']) == 1
        assert mock_bedrock.invoke_model.call_count == 2
    
    def test_ocr_fallback_after_vision_llm_failure(self, ui_analyzer_env):
        """Vision LLM 실패 후 OCR 폴백 테스트 (Requirements 2.6)"""
        config = ui_analyzer_env["config"]
        
        # Mock Bedrock 클라이언트 - 항상 실패
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("API Error")
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
        
        # OCR 결과 Mock
        mock_ocr_results = [
            {"text": "OCR 텍스트", "confidence": 0.9, "bbox": [], "x": 50, "y": 50}
        ]
        
        with patch('time.sleep'):
            with patch.object(analyzer, 'analyze_with_ocr', return_value=mock_ocr_results):
                test_image = Image.new('RGB', (100, 100), color='white')
                result = analyzer.analyze_with_retry(test_image, retry_count=3)
        
        # OCR 폴백 결과 검증
        assert result.get('source') == 'ocr_fallback'
        assert len(result['text_fields']) == 1
        assert result['text_fields'][0]['content'] == 'OCR 텍스트'

    def test_full_ui_analysis_workflow(self, ui_analyzer_env):
        """전체 UI 분석 워크플로우 테스트 (Requirements 2.1-2.7)"""
        config = ui_analyzer_env["config"]
        tmp_path = ui_analyzer_env["tmp_path"]
        
        # Mock 응답 생성
        mock_response = {
            "content": [{"text": json.dumps({
                "buttons": [
                    {"text": "시작", "x": 640, "y": 400, "width": 200, "height": 60, "confidence": 0.95},
                    {"text": "설정", "x": 640, "y": 500, "width": 200, "height": 60, "confidence": 0.92}
                ],
                "icons": [
                    {"type": "close", "x": 1200, "y": 50, "confidence": 0.88}
                ],
                "text_fields": [
                    {"content": "게임 타이틀", "x": 640, "y": 200, "confidence": 0.98}
                ]
            })}]
        }
        
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = {
            'body': io.BytesIO(json.dumps(mock_response).encode())
        }
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
        
        # 스크린샷 캡처 Mock
        mock_image = Image.new('RGB', (1920, 1080), color='gray')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            result = analyzer.analyze(save_screenshot=True)
        
        # 결과 검증
        assert result.get('source') == 'vision_llm'
        assert len(result['buttons']) == 2
        assert len(result['icons']) == 1
        assert len(result['text_fields']) == 1
        
        # 버튼 정보 검증
        button_texts = [b['text'] for b in result['buttons']]
        assert '시작' in button_texts
        assert '설정' in button_texts


class TestPhase2SemanticActionRecording:
    """Phase 2 의미론적 액션 기록 통합 테스트
    
    Requirements: 11.1-11.6
    """
    
    @pytest.fixture
    def semantic_recorder_env(self, tmp_path):
        """의미론적 액션 기록 테스트 환경 설정"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # 설정 파일 생성
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "retry_delay": 0.01
            },
            "automation": {
                "screenshot_dir": str(tmp_path / "screenshots"),
                "screenshot_on_action": True
            }
        }
        
        config_path = tmp_path / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        os.makedirs(tmp_path / "screenshots", exist_ok=True)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        yield {
            "config": config,
            "tmp_path": tmp_path
        }
        
        os.chdir(original_cwd)

    def test_click_action_captures_screenshot(self, semantic_recorder_env):
        """클릭 액션 시 스크린샷 캡처 테스트 (Requirements 11.1)"""
        config = semantic_recorder_env["config"]
        tmp_path = semantic_recorder_env["tmp_path"]
        
        # Mock UIAnalyzer 생성
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": "테스트 버튼", "x": 100, "y": 100, "width": 80, "height": 30}],
            "icons": [],
            "text_fields": []
        }
        
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # 클릭 액션 생성
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,
            description='버튼 클릭',
            button='left'
        )
        
        # Mock 스크린샷
        mock_image = Image.new('RGB', (100, 100), color='red')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            semantic_action = recorder.record_semantic_action(
                action, 
                capture_screenshots=True,
                analyze_ui=False
            )
        
        # 스크린샷 경로 검증
        assert semantic_action.screenshot_after_path is not None
        assert os.path.exists(semantic_action.screenshot_after_path)
        
        # UI 상태 해시 검증
        assert semantic_action.ui_state_hash_after is not None
    
    def test_semantic_info_extraction(self, semantic_recorder_env):
        """의미론적 정보 추출 테스트 (Requirements 11.2, 11.3)"""
        config = semantic_recorder_env["config"]
        
        # Mock UIAnalyzer - 버튼 정보 반환
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [
                {"text": "시작", "x": 100, "y": 100, "width": 80, "height": 30, "confidence": 0.95}
            ],
            "icons": [],
            "text_fields": []
        }
        
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # 클릭 액션 생성
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=105, y=105,  # 버튼 근처
            description='시작 버튼 클릭',
            button='left'
        )
        
        mock_image = Image.new('RGB', (200, 200), color='blue')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            semantic_action = recorder.record_semantic_action(
                action,
                capture_screenshots=True,
                analyze_ui=True
            )
        
        # 의미론적 정보 검증
        assert semantic_action.semantic_info is not None
        assert 'intent' in semantic_action.semantic_info
        assert 'target_element' in semantic_action.semantic_info
        assert 'context' in semantic_action.semantic_info
        
        # 의도 추론 검증 (시작 버튼이므로 start_game)
        assert semantic_action.semantic_info['intent'] == 'start_game'
        
        # 타겟 요소 검증
        target = semantic_action.semantic_info['target_element']
        assert target['type'] == 'button'
        assert target['text'] == '시작'

    def test_keyboard_input_semantic_info(self, semantic_recorder_env):
        """키보드 입력 의미론적 정보 테스트 (Requirements 11.5)"""
        config = semantic_recorder_env["config"]
        
        mock_analyzer = Mock()
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # 키보드 입력 액션
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='key_press',
            x=0, y=0,
            description='키 입력: a',
            key='a'
        )
        
        mock_image = Image.new('RGB', (100, 100), color='white')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            semantic_action = recorder.record_semantic_action(
                action,
                capture_screenshots=False,
                analyze_ui=False
            )
        
        # 키보드 입력 의미론적 정보 검증
        assert semantic_action.semantic_info['intent'] == 'text_input'
        assert semantic_action.semantic_info['target_element']['type'] == 'input_field'
        assert semantic_action.semantic_info['target_element']['text'] == 'a'
    
    def test_scroll_action_semantic_info(self, semantic_recorder_env):
        """스크롤 액션 의미론적 정보 테스트 (Requirements 11.6)"""
        config = semantic_recorder_env["config"]
        
        mock_analyzer = Mock()
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # 스크롤 액션
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='scroll',
            x=500, y=300,
            description='스크롤 (0, -3)',
            scroll_dx=0,
            scroll_dy=-3
        )
        
        mock_image = Image.new('RGB', (100, 100), color='green')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            semantic_action = recorder.record_semantic_action(
                action,
                capture_screenshots=False,
                analyze_ui=False
            )
        
        # 스크롤 의미론적 정보 검증
        assert semantic_action.semantic_info['intent'] == 'scroll_content'
        assert semantic_action.semantic_info['target_element']['type'] == 'scrollable_area'
        assert 'down' in semantic_action.semantic_info['target_element']['description']
    
    def test_screen_transition_detection(self, semantic_recorder_env):
        """화면 전환 감지 테스트 (Requirements 11.4)"""
        config = semantic_recorder_env["config"]
        
        mock_analyzer = Mock()
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # 서로 다른 패턴의 이미지로 화면 전환 시뮬레이션
        # 단색 이미지는 해시가 동일할 수 있으므로 패턴이 다른 이미지 사용
        image_before = Image.new('RGB', (100, 100), color='blue')
        image_after = Image.new('RGB', (100, 100), color='white')
        
        # 이미지에 다른 패턴 추가하여 해시 차이 발생시킴
        from PIL import ImageDraw
        draw_before = ImageDraw.Draw(image_before)
        draw_before.rectangle([0, 0, 50, 50], fill='black')
        
        draw_after = ImageDraw.Draw(image_after)
        draw_after.rectangle([50, 50, 100, 100], fill='black')
        
        # 해시 계산
        import imagehash
        hash_before = str(imagehash.average_hash(image_before))
        hash_after = str(imagehash.average_hash(image_after))
        
        # 화면 전환 분석
        transition = recorder._analyze_screen_transition(
            hash_before, hash_after, image_before, image_after
        )
        
        # 전환 정보 검증
        assert 'transition_type' in transition
        assert 'hash_difference' in transition
        assert transition['hash_difference'] > 0  # 다른 패턴이므로 차이가 있어야 함

    def test_semantic_action_serialization_round_trip(self, semantic_recorder_env):
        """의미론적 액션 직렬화 round trip 테스트 (Requirements 11.6)"""
        config = semantic_recorder_env["config"]
        
        mock_analyzer = Mock()
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # 여러 타입의 액션 기록
        actions = [
            Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=100, y=200,
                description='버튼 클릭',
                button='left'
            ),
            Action(
                timestamp=datetime.now().isoformat(),
                action_type='key_press',
                x=0, y=0,
                description='키 입력: test',
                key='t'
            ),
            Action(
                timestamp=datetime.now().isoformat(),
                action_type='scroll',
                x=300, y=400,
                description='스크롤 (0, -5)',
                scroll_dx=0,
                scroll_dy=-5
            )
        ]
        
        mock_image = Image.new('RGB', (100, 100), color='gray')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            for action in actions:
                recorder.record_semantic_action(
                    action,
                    capture_screenshots=False,
                    analyze_ui=False
                )
        
        # 직렬화
        serialized = recorder.to_dict_list()
        
        # 직렬화 결과 검증
        assert len(serialized) == 3
        assert serialized[0]['action_type'] == 'click'
        assert serialized[1]['action_type'] == 'key_press'
        assert serialized[2]['action_type'] == 'scroll'
        
        # 역직렬화
        restored_recorder = SemanticActionRecorder.from_dict_list(serialized, config)
        restored_actions = restored_recorder.get_semantic_actions()
        
        # Round trip 검증
        assert len(restored_actions) == 3
        
        # 각 액션의 필수 필드 검증
        for i, restored in enumerate(restored_actions):
            original = serialized[i]
            assert restored.action_type == original['action_type']
            assert restored.x == original['x']
            assert restored.y == original['y']
            assert restored.description == original['description']
            # semantic_info의 핵심 필드만 비교 (from_dict에서 표준화된 구조로 변환됨)
            if original.get('semantic_info'):
                assert restored.semantic_info.get('intent') == original['semantic_info'].get('intent')
                orig_target = original['semantic_info'].get('target_element', {})
                rest_target = restored.semantic_info.get('target_element', {})
                assert rest_target.get('type') == orig_target.get('type')
                assert rest_target.get('text') == orig_target.get('text')
                assert rest_target.get('description') == orig_target.get('description')

    def test_full_semantic_recording_workflow(self, semantic_recorder_env):
        """전체 의미론적 기록 워크플로우 테스트 (Requirements 11.1-11.6)"""
        config = semantic_recorder_env["config"]
        tmp_path = semantic_recorder_env["tmp_path"]
        
        # Mock UIAnalyzer - 다양한 UI 요소 반환
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [
                {"text": "시작", "x": 100, "y": 100, "width": 80, "height": 30, "confidence": 0.95},
                {"text": "설정", "x": 200, "y": 100, "width": 80, "height": 30, "confidence": 0.90}
            ],
            "icons": [
                {"type": "close", "x": 300, "y": 50, "confidence": 0.85}
            ],
            "text_fields": [
                {"content": "플레이어 이름", "x": 150, "y": 200, "confidence": 0.92}
            ]
        }
        
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # 시나리오: 게임 시작 버튼 클릭 → 이름 입력 → 확인
        mock_image = Image.new('RGB', (400, 300), color='blue')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            # 1. 시작 버튼 클릭
            click_action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=100, y=100,
                description='시작 버튼 클릭',
                button='left'
            )
            semantic_click = recorder.record_semantic_action(
                click_action,
                capture_screenshots=True,
                analyze_ui=True
            )
            
            # 2. 이름 입력
            key_action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='key_press',
                x=0, y=0,
                description='키 입력: Player1',
                key='P'
            )
            semantic_key = recorder.record_semantic_action(
                key_action,
                capture_screenshots=False,
                analyze_ui=False
            )
            
            # 3. 스크롤
            scroll_action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='scroll',
                x=200, y=150,
                description='스크롤 (0, -3)',
                scroll_dx=0,
                scroll_dy=-3
            )
            semantic_scroll = recorder.record_semantic_action(
                scroll_action,
                capture_screenshots=False,
                analyze_ui=False
            )
        
        # 기록된 액션 검증
        all_actions = recorder.get_semantic_actions()
        assert len(all_actions) == 3
        
        # 클릭 액션 검증 (Requirements 11.1, 11.2, 11.3)
        assert semantic_click.action_type == 'click'
        assert semantic_click.semantic_info['intent'] == 'start_game'
        assert semantic_click.semantic_info['target_element']['type'] == 'button'
        assert semantic_click.screenshot_after_path is not None
        
        # 키보드 액션 검증 (Requirements 11.5)
        assert semantic_key.action_type == 'key_press'
        assert semantic_key.semantic_info['intent'] == 'text_input'
        
        # 스크롤 액션 검증 (Requirements 11.6)
        assert semantic_scroll.action_type == 'scroll'
        assert semantic_scroll.semantic_info['intent'] == 'scroll_content'
        
        # JSON 저장 테스트
        json_path = tmp_path / "test_semantic_actions.json"
        serialized = recorder.to_dict_list()
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(serialized, f, ensure_ascii=False, indent=2)
        
        # 저장된 파일 검증
        assert os.path.exists(json_path)
        
        with open(json_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 3
        assert loaded[0]['semantic_info']['intent'] == 'start_game'

    def test_semantic_action_completeness(self, semantic_recorder_env):
        """의미론적 액션 완전성 테스트 - 물리적/의미론적 정보 모두 포함 (Requirements 11.6)"""
        config = semantic_recorder_env["config"]
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": "확인", "x": 150, "y": 150, "width": 60, "height": 25}],
            "icons": [],
            "text_fields": []
        }
        
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=150, y=150,
            description='확인 버튼 클릭',
            button='left'
        )
        
        mock_image = Image.new('RGB', (300, 300), color='white')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            semantic_action = recorder.record_semantic_action(
                action,
                capture_screenshots=True,
                analyze_ui=True
            )
        
        # 물리적 정보 검증
        assert semantic_action.x == 150
        assert semantic_action.y == 150
        assert semantic_action.action_type == 'click'
        assert semantic_action.button == 'left'
        assert semantic_action.timestamp is not None
        
        # 의미론적 정보 검증
        assert 'intent' in semantic_action.semantic_info
        assert 'target_element' in semantic_action.semantic_info
        assert 'context' in semantic_action.semantic_info
        
        # 타겟 요소 상세 검증
        target = semantic_action.semantic_info['target_element']
        assert 'type' in target
        assert 'text' in target
        assert 'description' in target
        
        # 컨텍스트 검증
        context = semantic_action.semantic_info['context']
        assert 'screen_state' in context
        assert 'expected_result' in context
