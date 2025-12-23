"""
Phase 3 통합 테스트

UI 변경 시나리오 테스트 및 의미론적 매칭 성공 검증

Requirements: 12.1-12.7
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
from src.semantic_action_replayer import SemanticActionReplayer, ReplayResult
from src.input_monitor import Action


class TestPhase3UIChangeScenarios:
    """Phase 3 UI 변경 시나리오 통합 테스트
    
    Requirements: 12.1-12.7
    """
    
    @pytest.fixture
    def replayer_env(self, tmp_path):
        """의미론적 재실행 테스트 환경 설정"""
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
                "action_delay": 0.01,
                "screenshot_dir": str(tmp_path / "screenshots"),
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
    
    def test_direct_match_when_element_at_original_position(self, replayer_env):
        """원래 좌표에 요소가 있을 때 직접 매칭 테스트 (Requirements 12.1)"""
        config = replayer_env["config"]
        
        # Mock UIAnalyzer - 원래 좌표에 버튼이 있음
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": "시작", "x": 100, "y": 100, "width": 80, "height": 30, "confidence": 0.95}],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 원래 좌표에서 기록된 액션
        semantic_info = {
            "intent": "start_game",
            "target_element": {
                "type": "button",
                "text": "시작",
                "description": "게임 시작 버튼",
                "visual_features": {}
            },
            "context": {"screen_state": "main_menu", "expected_result": "game_start"}
        }
        
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,
            description='시작 버튼 클릭',
            button='left',
            semantic_info=semantic_info,
            screen_transition={"transition_type": "unknown"}
        )
        
        mock_image = Image.new('RGB', (1920, 1080), color='gray')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_action(action)
        
        # 직접 매칭 검증
        assert result.success, f"액션 실패: {result.error_message}"
        assert result.method == 'direct', f"직접 매칭이어야 하는데 {result.method}입니다"
        assert result.actual_coords == (100, 100)
        assert result.coordinate_change is None  # 좌표 변경 없음

    def test_semantic_matching_when_button_moved(self, replayer_env):
        """버튼 위치 변경 시 의미론적 매칭 테스트 (Requirements 12.2, 12.4)"""
        config = replayer_env["config"]
        
        # Mock UIAnalyzer - 버튼이 새 위치로 이동
        # 원래 좌표(100, 100)에는 없고, 새 좌표(300, 200)에 있음
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": "시작", "x": 300, "y": 200, "width": 80, "height": 30, "confidence": 0.95}],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 원래 좌표에서 기록된 액션
        semantic_info = {
            "intent": "start_game",
            "target_element": {
                "type": "button",
                "text": "시작",
                "description": "게임 시작 버튼",
                "visual_features": {}
            },
            "context": {"screen_state": "main_menu", "expected_result": "game_start"}
        }
        
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,  # 원래 좌표
            description='시작 버튼 클릭',
            button='left',
            semantic_info=semantic_info,
            screen_transition={"transition_type": "unknown"}
        )
        
        mock_image = Image.new('RGB', (1920, 1080), color='gray')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_action(action)
        
        # 의미론적 매칭 검증
        assert result.success, f"액션 실패: {result.error_message}"
        assert result.method == 'semantic', f"의미론적 매칭이어야 하는데 {result.method}입니다"
        assert result.actual_coords == (300, 200), f"새 좌표로 실행되어야 함: {result.actual_coords}"
        assert result.coordinate_change == (200, 100), f"좌표 변경 기록 불일치: {result.coordinate_change}"

    def test_semantic_matching_finds_correct_button_among_multiple(self, replayer_env):
        """여러 버튼 중 올바른 버튼 찾기 테스트 (Requirements 12.3, 12.4)"""
        config = replayer_env["config"]
        
        # Mock UIAnalyzer - 여러 버튼이 있는 화면
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [
                {"text": "취소", "x": 100, "y": 100, "width": 80, "height": 30, "confidence": 0.90},
                {"text": "시작", "x": 400, "y": 300, "width": 80, "height": 30, "confidence": 0.95},
                {"text": "설정", "x": 200, "y": 200, "width": 80, "height": 30, "confidence": 0.88}
            ],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # "시작" 버튼을 찾아야 함
        semantic_info = {
            "intent": "start_game",
            "target_element": {
                "type": "button",
                "text": "시작",
                "description": "게임 시작 버튼",
                "visual_features": {}
            },
            "context": {"screen_state": "main_menu", "expected_result": "game_start"}
        }
        
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=50, y=50,  # 원래 좌표 (버튼이 없는 위치)
            description='시작 버튼 클릭',
            button='left',
            semantic_info=semantic_info,
            screen_transition={"transition_type": "unknown"}
        )
        
        mock_image = Image.new('RGB', (1920, 1080), color='white')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_action(action)
        
        # 올바른 버튼(시작)을 찾았는지 검증
        assert result.success, f"액션 실패: {result.error_message}"
        assert result.method == 'semantic'
        assert result.actual_coords == (400, 300), f"'시작' 버튼 좌표로 실행되어야 함: {result.actual_coords}"


    def test_screen_transition_verification_success(self, replayer_env):
        """화면 전환 검증 성공 테스트 (Requirements 12.6)"""
        config = replayer_env["config"]
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": "시작", "x": 100, "y": 100, "width": 80, "height": 30}],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 화면 전환 정보가 있는 액션
        semantic_info = {
            "intent": "start_game",
            "target_element": {"type": "button", "text": "시작", "description": "", "visual_features": {}},
            "context": {"screen_state": "main_menu", "expected_result": "loading"}
        }
        
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,
            description='시작 버튼 클릭',
            button='left',
            semantic_info=semantic_info,
            screen_transition={"transition_type": "unknown"}  # unknown은 항상 verified
        )
        
        mock_image = Image.new('RGB', (100, 100), color='blue')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_action(action)
        
        # 화면 전환 검증
        assert result.success
        assert result.screen_transition_verified == True
        assert result.expected_transition == "unknown"

    def test_screen_transition_mismatch_warning(self, replayer_env):
        """화면 전환 불일치 시 경고 테스트 (Requirements 12.7)"""
        config = replayer_env["config"]
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": "시작", "x": 100, "y": 100, "width": 80, "height": 30}],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 'none' 전환을 예상하지만 실제로는 다른 전환 발생
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,
            description='시작 버튼 클릭',
            button='left',
            semantic_info={
                "intent": "click_button",
                "target_element": {"type": "button", "text": "시작", "description": "", "visual_features": {}},
                "context": {"screen_state": "main", "expected_result": "none"}
            },
            screen_transition={"transition_type": "none"}
        )
        
        mock_image = Image.new('RGB', (100, 100), color='red')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui, \
             patch('src.semantic_action_replayer.imagehash') as mock_imagehash:
            
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            # 큰 해시 차이 (full_transition)
            mock_hash = Mock()
            mock_hash.__sub__ = Mock(return_value=50)
            mock_imagehash.average_hash.return_value = mock_hash
            mock_imagehash.hex_to_hash.return_value = mock_hash
            
            result = replayer.replay_action(action)
        
        # 성공했지만 전환 불일치
        assert result.success
        assert result.expected_transition == "none"
        # 실제 전환이 none이 아니면 verified가 False
        if result.actual_transition not in ['none', 'unknown', 'capture_failed', 'error']:
            assert result.screen_transition_verified == False


class TestPhase3SemanticMatchingWorkflow:
    """Phase 3 의미론적 매칭 워크플로우 통합 테스트
    
    Requirements: 12.1-12.7
    """
    
    @pytest.fixture
    def workflow_env(self, tmp_path):
        """워크플로우 테스트 환경 설정"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "retry_delay": 0.01
            },
            "automation": {
                "action_delay": 0.01,
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

    def test_multiple_actions_replay_with_ui_changes(self, workflow_env):
        """여러 액션 재실행 중 UI 변경 시나리오 테스트 (Requirements 12.1-12.4)"""
        config = workflow_env["config"]
        
        # UI가 변경되는 시나리오 시뮬레이션
        # 첫 번째 호출: 버튼이 원래 위치에 있음
        # 두 번째 호출: 버튼이 이동함
        call_count = [0]
        
        def mock_analyze(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:  # 첫 번째 액션
                return {
                    "buttons": [{"text": "다음", "x": 100, "y": 100, "width": 80, "height": 30, "confidence": 0.95}],
                    "icons": [],
                    "text_fields": []
                }
            else:  # 두 번째 액션 - 버튼 이동
                return {
                    "buttons": [{"text": "확인", "x": 500, "y": 400, "width": 80, "height": 30, "confidence": 0.95}],
                    "icons": [],
                    "text_fields": []
                }
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.side_effect = mock_analyze
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 두 개의 액션 생성
        actions = [
            SemanticAction(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=100, y=100,
                description='다음 버튼 클릭',
                button='left',
                semantic_info={
                    "intent": "navigate",
                    "target_element": {"type": "button", "text": "다음", "description": "", "visual_features": {}},
                    "context": {"screen_state": "step1", "expected_result": "step2"}
                },
                screen_transition={"transition_type": "unknown"}
            ),
            SemanticAction(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=200, y=200,  # 원래 좌표 (버튼이 이동함)
                description='확인 버튼 클릭',
                button='left',
                semantic_info={
                    "intent": "confirm",
                    "target_element": {"type": "button", "text": "확인", "description": "", "visual_features": {}},
                    "context": {"screen_state": "step2", "expected_result": "complete"}
                },
                screen_transition={"transition_type": "unknown"}
            )
        ]
        
        mock_image = Image.new('RGB', (1920, 1080), color='gray')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            results = replayer.replay_actions(actions)
        
        # 결과 검증
        assert len(results) == 2
        
        # 첫 번째 액션: 직접 매칭
        assert results[0].success
        assert results[0].method == 'direct'
        
        # 두 번째 액션: 의미론적 매칭 (버튼이 이동했으므로)
        assert results[1].success
        assert results[1].method == 'semantic'
        assert results[1].actual_coords == (500, 400)

    def test_statistics_after_replay(self, workflow_env):
        """재실행 후 통계 계산 테스트 (Requirements 12.7)"""
        config = workflow_env["config"]
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": "테스트", "x": 300, "y": 300, "width": 80, "height": 30, "confidence": 0.95}],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 여러 액션 재실행
        actions = []
        for i in range(5):
            actions.append(SemanticAction(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=100 + i * 10, y=100 + i * 10,
                description=f'버튼 클릭 {i}',
                button='left',
                semantic_info={
                    "intent": "click",
                    "target_element": {"type": "button", "text": "테스트", "description": "", "visual_features": {}},
                    "context": {"screen_state": "test", "expected_result": "action"}
                },
                screen_transition={"transition_type": "unknown"}
            ))
        
        mock_image = Image.new('RGB', (1920, 1080), color='white')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            replayer.replay_actions(actions)
        
        # 통계 계산
        stats = replayer.get_statistics()
        
        # 통계 검증
        assert stats['total_actions'] == 5
        assert stats['success_count'] == 5
        assert stats['success_rate'] == 1.0
        assert 'semantic_match_count' in stats
        assert 'direct_match_count' in stats
        assert 'avg_coordinate_change' in stats

    def test_full_semantic_replay_workflow(self, workflow_env):
        """전체 의미론적 재실행 워크플로우 테스트 (Requirements 12.1-12.7)"""
        config = workflow_env["config"]
        tmp_path = workflow_env["tmp_path"]
        
        # 시나리오: 게임 메뉴에서 버튼 클릭 → UI 변경 → 새 위치에서 버튼 찾기
        
        # Mock UIAnalyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
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
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 기록된 액션 (원래 좌표와 다른 위치에서 버튼을 찾아야 함)
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,  # 원래 좌표 (버튼이 없는 위치)
            description='시작 버튼 클릭',
            button='left',
            semantic_info={
                "intent": "start_game",
                "target_element": {
                    "type": "button",
                    "text": "시작",
                    "description": "게임 시작 버튼",
                    "visual_features": {"color": "blue", "shape": "rectangle"}
                },
                "context": {
                    "screen_state": "main_menu",
                    "expected_result": "game_loading"
                }
            },
            screen_transition={
                "before_state": "main_menu",
                "after_state": "loading",
                "transition_type": "unknown"
            }
        )
        
        mock_image = Image.new('RGB', (1920, 1080), color='blue')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_action(action)
        
        # 전체 워크플로우 검증
        assert result.success, f"액션 실패: {result.error_message}"
        
        # 의미론적 매칭으로 새 위치 찾음
        assert result.method == 'semantic'
        assert result.actual_coords == (640, 400)  # "시작" 버튼의 새 위치
        
        # 좌표 변경 기록
        assert result.coordinate_change == (540, 300)
        
        # 원래 좌표 기록
        assert result.original_coords == (100, 100)
        
        # 화면 전환 검증
        assert result.screen_transition_verified == True  # unknown은 항상 True


class TestPhase3EdgeCases:
    """Phase 3 엣지 케이스 테스트
    
    Requirements: 12.5
    """
    
    @pytest.fixture
    def edge_case_env(self, tmp_path):
        """엣지 케이스 테스트 환경 설정"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "retry_delay": 0.01
            },
            "automation": {
                "action_delay": 0.01,
                "screenshot_dir": str(tmp_path / "screenshots")
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

    def test_element_not_found_failure(self, edge_case_env):
        """요소를 찾지 못했을 때 실패 처리 테스트 (Requirements 12.5)"""
        config = edge_case_env["config"]
        
        # Mock UIAnalyzer - 빈 결과 반환
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 찾을 수 없는 버튼
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,
            description='존재하지 않는 버튼 클릭',
            button='left',
            semantic_info={
                "intent": "click",
                "target_element": {"type": "button", "text": "없는버튼", "description": "", "visual_features": {}},
                "context": {"screen_state": "test", "expected_result": "none"}
            },
            screen_transition={"transition_type": "unknown"}
        )
        
        mock_image = Image.new('RGB', (100, 100), color='white')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_action(action)
        
        # 실패 검증
        assert result.success == False
        assert result.method == 'failed'
        assert "찾을 수 없음" in result.error_message or "실패" in result.error_message

    def test_keyboard_action_replay(self, edge_case_env):
        """키보드 액션 재실행 테스트"""
        config = edge_case_env["config"]
        
        mock_analyzer = Mock()
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='key_press',
            x=0, y=0,
            description='키 입력: enter',
            key='enter',
            semantic_info={
                "intent": "confirm",
                "target_element": {"type": "keyboard", "text": "enter", "description": "", "visual_features": {}},
                "context": {"screen_state": "dialog", "expected_result": "submit"}
            },
            screen_transition={"transition_type": "unknown"}
        )
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.press = Mock()
            
            result = replayer.replay_action(action)
        
        # 키보드 액션 성공 검증
        assert result.success
        assert result.method == 'direct'
        mock_pyautogui.press.assert_called_once_with('enter')

    def test_scroll_action_replay(self, edge_case_env):
        """스크롤 액션 재실행 테스트"""
        config = edge_case_env["config"]
        
        mock_analyzer = Mock()
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='scroll',
            x=500, y=300,
            description='스크롤 (0, -3)',
            scroll_dx=0,
            scroll_dy=-3,
            semantic_info={
                "intent": "scroll",
                "target_element": {"type": "scrollable", "text": "", "description": "", "visual_features": {}},
                "context": {"screen_state": "list", "expected_result": "scroll_down"}
            },
            screen_transition={"transition_type": "unknown"}
        )
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.scroll = Mock()
            
            result = replayer.replay_action(action)
        
        # 스크롤 액션 성공 검증
        assert result.success
        assert result.method == 'direct'
        mock_pyautogui.scroll.assert_called_once_with(-3, x=500, y=300)

    def test_wait_action_replay(self, edge_case_env):
        """대기 액션 재실행 테스트"""
        config = edge_case_env["config"]
        
        mock_analyzer = Mock()
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='wait',
            x=0, y=0,
            description='0.1초 대기',
            semantic_info={},
            screen_transition={}
        )
        
        with patch('time.sleep') as mock_sleep:
            result = replayer.replay_action(action)
        
        # 대기 액션 성공 검증
        assert result.success
        assert result.method == 'direct'
        mock_sleep.assert_called()

    def test_clear_results(self, edge_case_env):
        """결과 초기화 테스트"""
        config = edge_case_env["config"]
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": "테스트", "x": 100, "y": 100, "width": 80, "height": 30}],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 액션 실행
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,
            description='테스트 클릭',
            button='left',
            semantic_info={
                "intent": "test",
                "target_element": {"type": "button", "text": "테스트", "description": "", "visual_features": {}},
                "context": {"screen_state": "test", "expected_result": "test"}
            },
            screen_transition={"transition_type": "unknown"}
        )
        
        mock_image = Image.new('RGB', (100, 100), color='gray')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            replayer.replay_action(action)
        
        # 결과 확인
        assert len(replayer.get_results()) == 1
        
        # 결과 초기화
        replayer.clear_results()
        
        # 초기화 확인
        assert len(replayer.get_results()) == 0
        stats = replayer.get_statistics()
        assert stats['total_actions'] == 0
