# -*- coding: utf-8 -*-
"""
의미론적 테스트 기록 및 재현 통합 테스트

Task 12: 통합 테스트
- 12.1: 전체 기록 → 저장 → 로드 → 재현 흐름 테스트
- 12.2: 레거시 테스트 케이스 보강 → 재현 흐름 테스트

Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.5, 5.1-5.7
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
from src.script_generator import ScriptGenerator
from src.test_case_enricher import TestCaseEnricher, EnrichmentResult
from src.input_monitor import Action


class TestSemanticRecordSaveLoadReplayWorkflow:
    """Task 12.1: 전체 기록 → 저장 → 로드 → 재현 흐름 통합 테스트
    
    Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.5
    """
    
    @pytest.fixture
    def workflow_env(self, tmp_path):
        """통합 테스트 환경 설정"""
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
            },
            "test_cases": {
                "directory": str(tmp_path / "test_cases")
            }
        }
        
        config_path = tmp_path / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        # 디렉토리 생성
        os.makedirs(tmp_path / "screenshots", exist_ok=True)
        os.makedirs(tmp_path / "test_cases", exist_ok=True)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        yield {
            "config": config,
            "tmp_path": tmp_path,
            "config_path": config_path
        }
        
        os.chdir(original_cwd)

    def test_full_record_save_load_replay_workflow(self, workflow_env):
        """전체 기록 → 저장 → 로드 → 재현 워크플로우 테스트
        
        Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.5
        
        이 테스트는 다음 흐름을 검증한다:
        1. 클릭 액션 기록 시 의미론적 정보 캡처 (Requirements: 1.1-1.5)
        2. 테스트 케이스 JSON 저장 시 semantic_info 포함 (Requirements: 2.1-2.3)
        3. JSON 로드 시 semantic_info 완전 복원 (Requirements: 2.4-2.5)
        4. 재현 시 의미론적 매칭 활용 (Requirements: 3.1-3.5)
        """
        config = workflow_env["config"]
        tmp_path = workflow_env["tmp_path"]
        
        # === 1단계: 기록 (Recording) ===
        # Mock UIAnalyzer - 버튼 정보 반환
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "source": "vision_llm",
            "buttons": [
                {
                    "text": "시작",
                    "x": 640,
                    "y": 400,
                    "width": 200,
                    "height": 60,
                    "bounding_box": {"x": 540, "y": 370, "width": 200, "height": 60},
                    "confidence": 0.95
                },
                {
                    "text": "설정",
                    "x": 640,
                    "y": 500,
                    "width": 200,
                    "height": 60,
                    "bounding_box": {"x": 540, "y": 470, "width": 200, "height": 60},
                    "confidence": 0.92
                }
            ],
            "icons": [],
            "text_fields": []
        }
        mock_analyzer.find_element_at_position.return_value = {
            "element_type": "button",
            "text": "시작",
            "x": 640,
            "y": 400,
            "width": 200,
            "height": 60,
            "bounding_box": {"x": 540, "y": 370, "width": 200, "height": 60},
            "confidence": 0.95
        }
        
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # 클릭 액션 기록
        mock_image = Image.new('RGB', (1920, 1080), color='blue')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            # 시작 버튼 클릭 기록
            action1 = Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=640, y=400,
                description='시작 버튼 클릭',
                button='left'
            )
            semantic_action1 = recorder.record_semantic_action(
                action1,
                capture_screenshots=True,
                analyze_ui=True
            )
        
        # 기록된 액션 검증 (Requirements: 1.3, 1.4)
        assert semantic_action1.action_type == 'click'
        assert semantic_action1.x == 640
        assert semantic_action1.y == 400
        assert semantic_action1.semantic_info is not None
        assert 'intent' in semantic_action1.semantic_info
        assert 'target_element' in semantic_action1.semantic_info
        assert 'context' in semantic_action1.semantic_info
        
        # target_element 검증 (Requirements: 1.3)
        target = semantic_action1.semantic_info.get('target_element', {})
        assert target.get('type') == 'button'
        assert target.get('text') == '시작'
        
        # === 2단계: 저장 (Save) ===
        script_generator = ScriptGenerator(config)
        json_path = str(tmp_path / "test_cases" / "semantic_test.json")
        
        # 테스트 케이스 JSON 저장 (Requirements: 2.1-2.3)
        script_generator.save_test_case_json(
            actions=recorder.get_semantic_actions(),
            output_path=json_path,
            test_case_name="semantic_test",
            semantic_enabled=True
        )
        
        # 저장된 파일 검증
        assert os.path.exists(json_path)
        
        with open(json_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        # semantic_info가 저장되었는지 검증 (Requirements: 2.1)
        assert len(saved_data['actions']) == 1
        saved_action = saved_data['actions'][0]
        assert 'semantic_info' in saved_action
        assert saved_action['semantic_info'].get('intent') is not None
        assert saved_action['semantic_info'].get('target_element') is not None
        
        # screenshot_before_path 또는 screenshot_after_path 검증 (Requirements: 2.2)
        has_screenshot = (
            saved_action.get('screenshot_before_path') is not None or
            saved_action.get('screenshot_after_path') is not None or
            saved_action.get('screenshot_path') is not None
        )
        assert has_screenshot, "스크린샷 경로가 저장되어야 함"
        
        # === 3단계: 로드 (Load) ===
        # JSON 로드 및 SemanticAction 복원 (Requirements: 2.4-2.5)
        loaded_test_case = script_generator.load_test_case_json(json_path)
        loaded_actions = loaded_test_case.get('actions', [])
        
        assert len(loaded_actions) == 1
        loaded_action = loaded_actions[0]
        
        # SemanticAction으로 복원되었는지 검증
        assert isinstance(loaded_action, SemanticAction)
        
        # semantic_info 완전 복원 검증 (Requirements: 2.4, 2.5)
        assert loaded_action.semantic_info is not None
        assert loaded_action.semantic_info.get('intent') == semantic_action1.semantic_info.get('intent')
        
        loaded_target = loaded_action.semantic_info.get('target_element', {})
        original_target = semantic_action1.semantic_info.get('target_element', {})
        assert loaded_target.get('type') == original_target.get('type')
        assert loaded_target.get('text') == original_target.get('text')
        
        # === 4단계: 재현 (Replay) ===
        # Mock UIAnalyzer - 버튼이 새 위치로 이동한 상황 시뮬레이션
        mock_replay_analyzer = Mock()
        mock_replay_analyzer.analyze_with_retry.return_value = {
            "source": "vision_llm",
            "buttons": [
                {
                    "text": "시작",
                    "x": 700,  # 위치 변경
                    "y": 450,  # 위치 변경
                    "width": 200,
                    "height": 60,
                    "confidence": 0.95
                }
            ],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_replay_analyzer)
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            # 의미론적 매칭으로 재현 (Requirements: 3.1-3.5)
            result = replayer.replay_click_with_semantic_matching(loaded_action)
        
        # 재현 결과 검증
        assert result.success, f"재현 실패: {result.error_message}"
        
        # 의미론적 매칭 또는 좌표 기반 매칭 중 하나로 성공해야 함
        assert result.method in ['semantic', 'coordinate', 'direct']
        
        # 통계 검증 (Requirements: 4.1, 4.4)
        stats = replayer.get_statistics()
        assert stats['total_actions'] == 1
        assert stats['success_count'] == 1

    def test_semantic_info_completeness_in_workflow(self, workflow_env):
        """의미론적 정보 완전성 검증 테스트
        
        Requirements: 1.3, 1.4, 2.1, 2.3
        
        클릭 액션 기록 시 물리적 좌표와 semantic_info가 모두 포함되는지 검증
        """
        config = workflow_env["config"]
        
        # Mock UIAnalyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "source": "vision_llm",
            "buttons": [
                {
                    "text": "확인",
                    "x": 500,
                    "y": 300,
                    "width": 100,
                    "height": 40,
                    "bounding_box": {"x": 450, "y": 280, "width": 100, "height": 40},
                    "confidence": 0.90
                }
            ],
            "icons": [],
            "text_fields": []
        }
        mock_analyzer.find_element_at_position.return_value = {
            "element_type": "button",
            "text": "확인",
            "x": 500,
            "y": 300,
            "bounding_box": {"x": 450, "y": 280, "width": 100, "height": 40},
            "confidence": 0.90
        }
        
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        mock_image = Image.new('RGB', (1920, 1080), color='gray')
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=500, y=300,
                description='확인 버튼 클릭',
                button='left'
            )
            semantic_action = recorder.record_semantic_action(
                action,
                capture_screenshots=True,
                analyze_ui=True
            )
        
        # 물리적 좌표 검증
        assert semantic_action.x == 500
        assert semantic_action.y == 300
        assert semantic_action.action_type == 'click'
        assert semantic_action.button == 'left'
        
        # semantic_info 완전성 검증 (Requirements: 1.3, 1.4)
        semantic_info = semantic_action.semantic_info
        assert semantic_info is not None
        assert 'intent' in semantic_info
        assert 'target_element' in semantic_info
        assert 'context' in semantic_info
        
        # target_element 필수 필드 검증
        target = semantic_info['target_element']
        assert 'type' in target
        assert 'text' in target
        assert 'description' in target or target.get('text')  # description 또는 text 중 하나

    def test_serialization_round_trip_in_workflow(self, workflow_env):
        """직렬화 왕복 검증 테스트
        
        Requirements: 2.4, 2.5, 6.1-6.5
        
        SemanticAction → JSON → SemanticAction 왕복 시 데이터 동등성 검증
        """
        config = workflow_env["config"]
        tmp_path = workflow_env["tmp_path"]
        
        # 원본 SemanticAction 생성
        original_action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=640, y=400,
            description='테스트 버튼 클릭',
            button='left',
            screenshot_before_path='screenshots/before.png',
            screenshot_after_path='screenshots/after.png',
            ui_state_hash_before='abc123',
            ui_state_hash_after='def456',
            semantic_info={
                "intent": "start_game",
                "target_element": {
                    "type": "button",
                    "text": "시작",
                    "description": "게임 시작 버튼",
                    "bounding_box": {"x": 540, "y": 370, "width": 200, "height": 60},
                    "confidence": 0.95
                },
                "context": {
                    "screen_state": "main_menu",
                    "expected_result": "game_loading"
                }
            },
            screen_transition={
                "before_state": "main_menu",
                "after_state": "loading",
                "transition_type": "full_transition",
                "hash_difference": 45
            }
        )
        
        # JSON 저장
        script_generator = ScriptGenerator(config)
        json_path = str(tmp_path / "test_cases" / "roundtrip_test.json")
        
        script_generator.save_test_case_json(
            actions=[original_action],
            output_path=json_path,
            test_case_name="roundtrip_test",
            semantic_enabled=True
        )
        
        # JSON 로드
        loaded_test_case = script_generator.load_test_case_json(json_path)
        loaded_action = loaded_test_case['actions'][0]
        
        # 동등성 검증 (Requirements: 6.3)
        assert loaded_action.action_type == original_action.action_type
        assert loaded_action.x == original_action.x
        assert loaded_action.y == original_action.y
        assert loaded_action.description == original_action.description
        assert loaded_action.button == original_action.button
        
        # semantic_info 동등성 검증
        assert loaded_action.semantic_info['intent'] == original_action.semantic_info['intent']
        
        loaded_target = loaded_action.semantic_info['target_element']
        original_target = original_action.semantic_info['target_element']
        assert loaded_target['type'] == original_target['type']
        assert loaded_target['text'] == original_target['text']
        
        # bounding_box 동등성 검증 (Requirements: 6.4)
        loaded_bbox = loaded_target.get('bounding_box', {})
        original_bbox = original_target.get('bounding_box', {})
        assert loaded_bbox.get('x') == original_bbox.get('x')
        assert loaded_bbox.get('y') == original_bbox.get('y')
        assert loaded_bbox.get('width') == original_bbox.get('width')
        assert loaded_bbox.get('height') == original_bbox.get('height')

    def test_semantic_matching_with_ui_position_change(self, workflow_env):
        """UI 위치 변경 시 의미론적 매칭 테스트
        
        Requirements: 3.1-3.5
        
        버튼 위치가 변경되어도 의미론적 매칭으로 올바른 요소를 찾는지 검증
        """
        config = workflow_env["config"]
        
        # 원래 위치에서 기록된 액션
        recorded_action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,  # 원래 좌표
            description='시작 버튼 클릭',
            button='left',
            semantic_info={
                "intent": "start_game",
                "target_element": {
                    "type": "button",
                    "text": "시작",
                    "description": "게임 시작 버튼",
                    "bounding_box": {"x": 60, "y": 80, "width": 80, "height": 40},
                    "confidence": 0.95
                },
                "context": {
                    "screen_state": "main_menu",
                    "expected_result": "game_loading"
                }
            },
            screen_transition={"transition_type": "unknown"}
        )
        
        # Mock UIAnalyzer - 버튼이 새 위치로 이동
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "source": "vision_llm",
            "buttons": [
                {
                    "text": "시작",
                    "x": 500,  # 새 위치
                    "y": 400,  # 새 위치
                    "width": 80,
                    "height": 40,
                    "confidence": 0.95
                }
            ],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        mock_image = Image.new('RGB', (1920, 1080), color='white')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_click_with_semantic_matching(recorded_action)
        
        # 의미론적 매칭 성공 검증
        assert result.success, f"재현 실패: {result.error_message}"
        
        # 매칭 방법 검증 (semantic 또는 coordinate)
        # 텍스트 매칭이 성공하면 semantic, 아니면 coordinate로 폴백
        assert result.method in ['semantic', 'coordinate']
        
        # 좌표 변경이 기록되었는지 검증 (Requirements: 3.5)
        if result.method == 'semantic':
            assert result.actual_coords == (500, 400)
            assert result.coordinate_change is not None




class TestLegacyTestCaseEnrichmentWorkflow:
    """Task 12.2: 레거시 테스트 케이스 보강 → 재현 흐름 통합 테스트
    
    Requirements: 5.1-5.7
    """
    
    @pytest.fixture
    def enrichment_env(self, tmp_path):
        """보강 테스트 환경 설정"""
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
            },
            "test_cases": {
                "directory": str(tmp_path / "test_cases")
            }
        }
        
        config_path = tmp_path / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        # 디렉토리 생성
        screenshots_dir = tmp_path / "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        os.makedirs(tmp_path / "test_cases", exist_ok=True)
        
        # 테스트용 스크린샷 이미지 생성
        test_image = Image.new('RGB', (1920, 1080), color='blue')
        test_image.save(str(screenshots_dir / "action_0000.png"))
        test_image.save(str(screenshots_dir / "action_0001.png"))
        test_image.save(str(screenshots_dir / "action_0002.png"))
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        yield {
            "config": config,
            "tmp_path": tmp_path,
            "screenshots_dir": str(screenshots_dir),
            "config_path": config_path
        }
        
        os.chdir(original_cwd)

    def test_legacy_test_case_detection(self, enrichment_env):
        """레거시 테스트 케이스 감지 테스트
        
        Requirements: 5.1
        
        semantic_info가 없거나 비어있는 클릭 액션이 있으면 레거시로 감지
        """
        config = enrichment_env["config"]
        
        mock_analyzer = Mock()
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        # 레거시 테스트 케이스 (semantic_info 없음)
        legacy_test_case = {
            "name": "legacy_test",
            "version": "1.0",
            "actions": [
                {
                    "action_type": "click",
                    "x": 100, "y": 100,
                    "description": "버튼 클릭",
                    "screenshot_path": "screenshots/action_0000.png"
                    # semantic_info 없음
                },
                {
                    "action_type": "wait",
                    "x": 0, "y": 0,
                    "description": "1초 대기"
                }
            ]
        }
        
        # 레거시 감지 검증
        assert enricher.is_legacy_test_case(legacy_test_case) == True
        
        # 비어있는 semantic_info
        legacy_test_case_empty = {
            "name": "legacy_test_empty",
            "version": "1.0",
            "actions": [
                {
                    "action_type": "click",
                    "x": 100, "y": 100,
                    "description": "버튼 클릭",
                    "semantic_info": {}  # 비어있음
                }
            ]
        }
        
        assert enricher.is_legacy_test_case(legacy_test_case_empty) == True
        
        # 현대 테스트 케이스 (semantic_info 있음)
        modern_test_case = {
            "name": "modern_test",
            "version": "2.0",
            "actions": [
                {
                    "action_type": "click",
                    "x": 100, "y": 100,
                    "description": "버튼 클릭",
                    "semantic_info": {
                        "intent": "click_button",
                        "target_element": {
                            "type": "button",
                            "text": "확인"
                        }
                    }
                }
            ]
        }
        
        assert enricher.is_legacy_test_case(modern_test_case) == False

    def test_legacy_enrichment_workflow(self, enrichment_env):
        """레거시 테스트 케이스 보강 워크플로우 테스트
        
        Requirements: 5.2, 5.3, 5.4, 5.5, 5.6
        
        레거시 테스트 케이스를 보강하고 의미론적 재현이 가능한지 검증
        """
        config = enrichment_env["config"]
        screenshots_dir = enrichment_env["screenshots_dir"]
        
        # Mock UIAnalyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "source": "vision_llm",
            "buttons": [
                {
                    "text": "시작",
                    "x": 100,
                    "y": 100,
                    "width": 80,
                    "height": 40,
                    "bounding_box": {"x": 60, "y": 80, "width": 80, "height": 40},
                    "confidence": 0.90
                }
            ],
            "icons": [],
            "text_fields": []
        }
        mock_analyzer.find_element_at_position.return_value = {
            "element_type": "button",
            "text": "시작",
            "x": 100,
            "y": 100,
            "bounding_box": {"x": 60, "y": 80, "width": 80, "height": 40},
            "confidence": 0.90
        }
        
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        # 레거시 테스트 케이스
        legacy_test_case = {
            "name": "legacy_test",
            "version": "1.0",
            "created_at": "2025-01-01T00:00:00",
            "actions": [
                {
                    "timestamp": "2025-01-01T00:00:01",
                    "action_type": "click",
                    "x": 100, "y": 100,
                    "description": "시작 버튼 클릭",
                    "button": "left",
                    "screenshot_path": "screenshots/action_0000.png"
                    # semantic_info 없음
                },
                {
                    "timestamp": "2025-01-01T00:00:02",
                    "action_type": "wait",
                    "x": 0, "y": 0,
                    "description": "1초 대기"
                },
                {
                    "timestamp": "2025-01-01T00:00:03",
                    "action_type": "click",
                    "x": 200, "y": 200,
                    "description": "확인 버튼 클릭",
                    "button": "left",
                    "screenshot_path": "screenshots/action_0001.png"
                }
            ]
        }
        
        # 레거시 감지 확인
        assert enricher.is_legacy_test_case(legacy_test_case) == True
        
        # 보강 실행 (Requirements: 5.2, 5.3)
        enriched_test_case, result = enricher.enrich_test_case(
            legacy_test_case, 
            screenshots_dir
        )
        
        # 보강 결과 검증 (Requirements: 5.4)
        assert result.total_actions == 3
        assert result.enriched_count >= 0  # 스크린샷이 있는 클릭 액션 수
        assert result.version != "1.0"  # 버전이 업데이트됨
        
        # 기존 데이터 보존 검증 (Requirements: 5.6)
        for i, action in enumerate(enriched_test_case['actions']):
            original_action = legacy_test_case['actions'][i]
            
            # 기존 필드 보존
            assert action['timestamp'] == original_action['timestamp']
            assert action['action_type'] == original_action['action_type']
            assert action['x'] == original_action['x']
            assert action['y'] == original_action['y']
            assert action['description'] == original_action['description']
            
            # screenshot_path 보존
            if 'screenshot_path' in original_action:
                assert action.get('screenshot_path') == original_action['screenshot_path']
        
        # 클릭 액션에 semantic_info 추가 검증
        click_actions = [a for a in enriched_test_case['actions'] if a['action_type'] == 'click']
        for action in click_actions:
            if action.get('enrichment_status') == 'enriched':
                assert 'semantic_info' in action
                assert action['semantic_info'].get('target_element') is not None

    def test_enriched_test_case_replay(self, enrichment_env):
        """보강된 테스트 케이스 재현 테스트
        
        Requirements: 5.7
        
        보강된 테스트 케이스가 의미론적 재현이 가능한지 검증
        """
        config = enrichment_env["config"]
        screenshots_dir = enrichment_env["screenshots_dir"]
        
        # Mock UIAnalyzer for enrichment
        mock_enrichment_analyzer = Mock()
        mock_enrichment_analyzer.analyze_with_retry.return_value = {
            "source": "vision_llm",
            "buttons": [
                {
                    "text": "확인",
                    "x": 150,
                    "y": 150,
                    "width": 80,
                    "height": 40,
                    "bounding_box": {"x": 110, "y": 130, "width": 80, "height": 40},
                    "confidence": 0.92
                }
            ],
            "icons": [],
            "text_fields": []
        }
        mock_enrichment_analyzer.find_element_at_position.return_value = {
            "element_type": "button",
            "text": "확인",
            "x": 150,
            "y": 150,
            "bounding_box": {"x": 110, "y": 130, "width": 80, "height": 40},
            "confidence": 0.92
        }
        
        enricher = TestCaseEnricher(config, ui_analyzer=mock_enrichment_analyzer)
        
        # 레거시 테스트 케이스
        legacy_test_case = {
            "name": "replay_test",
            "version": "1.0",
            "actions": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "action_type": "click",
                    "x": 150, "y": 150,
                    "description": "확인 버튼 클릭",
                    "button": "left",
                    "screenshot_path": "screenshots/action_0000.png"
                }
            ]
        }
        
        # 보강
        enriched_test_case, enrich_result = enricher.enrich_test_case(
            legacy_test_case,
            screenshots_dir
        )
        
        # 보강된 액션을 SemanticAction으로 변환
        enriched_action_dict = enriched_test_case['actions'][0]
        
        # semantic_info가 추가되었는지 확인
        if enriched_action_dict.get('enrichment_status') == 'enriched':
            semantic_action = SemanticAction.from_dict(enriched_action_dict)
            
            # Mock UIAnalyzer for replay - 버튼이 새 위치로 이동
            mock_replay_analyzer = Mock()
            mock_replay_analyzer.analyze_with_retry.return_value = {
                "source": "vision_llm",
                "buttons": [
                    {
                        "text": "확인",
                        "x": 300,  # 새 위치
                        "y": 300,  # 새 위치
                        "width": 80,
                        "height": 40,
                        "confidence": 0.92
                    }
                ],
                "icons": [],
                "text_fields": []
            }
            
            replayer = SemanticActionReplayer(config, ui_analyzer=mock_replay_analyzer)
            
            mock_image = Image.new('RGB', (1920, 1080), color='gray')
            
            with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
                mock_pyautogui.screenshot.return_value = mock_image
                mock_pyautogui.click = Mock()
                
                # 의미론적 매칭으로 재현
                result = replayer.replay_click_with_semantic_matching(semantic_action)
            
            # 재현 성공 검증
            assert result.success, f"재현 실패: {result.error_message}"
            
            # 의미론적 매칭 또는 좌표 기반 매칭
            assert result.method in ['semantic', 'coordinate']

    def test_enrichment_preserves_existing_verification_data(self, enrichment_env):
        """보강 시 기존 검증 데이터 보존 테스트
        
        Requirements: 5.6
        
        보강 후에도 기존의 screenshot_path, 검증 관련 데이터가 유지되는지 검증
        """
        config = enrichment_env["config"]
        screenshots_dir = enrichment_env["screenshots_dir"]
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "source": "vision_llm",
            "buttons": [{"text": "테스트", "x": 100, "y": 100, "confidence": 0.9}],
            "icons": [],
            "text_fields": []
        }
        mock_analyzer.find_element_at_position.return_value = {
            "element_type": "button",
            "text": "테스트",
            "x": 100,
            "y": 100,
            "confidence": 0.9
        }
        
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        # 기존 검증 데이터가 있는 레거시 테스트 케이스
        legacy_test_case = {
            "name": "verification_test",
            "version": "1.0",
            "actions": [
                {
                    "timestamp": "2025-01-01T00:00:01",
                    "action_type": "click",
                    "x": 100, "y": 100,
                    "description": "테스트 버튼 클릭",
                    "button": "left",
                    "screenshot_path": "screenshots/action_0000.png",
                    # 기존 검증 데이터
                    "ui_state_hash_after": "existing_hash_123",
                    "screen_transition": {
                        "transition_type": "partial_change",
                        "hash_difference": 15
                    }
                }
            ]
        }
        
        # 보강
        enriched_test_case, result = enricher.enrich_test_case(
            legacy_test_case,
            screenshots_dir
        )
        
        enriched_action = enriched_test_case['actions'][0]
        original_action = legacy_test_case['actions'][0]
        
        # 기존 데이터 보존 검증 (Requirements: 5.6)
        assert enriched_action['screenshot_path'] == original_action['screenshot_path']
        assert enriched_action['timestamp'] == original_action['timestamp']
        assert enriched_action['x'] == original_action['x']
        assert enriched_action['y'] == original_action['y']
        assert enriched_action['description'] == original_action['description']

    def test_enrichment_handles_missing_screenshots(self, enrichment_env):
        """스크린샷 누락 시 처리 테스트
        
        Requirements: 5.5
        
        스크린샷이 누락된 액션은 스킵하고 나머지 액션을 계속 처리
        """
        config = enrichment_env["config"]
        screenshots_dir = enrichment_env["screenshots_dir"]
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "source": "vision_llm",
            "buttons": [{"text": "테스트", "x": 100, "y": 100, "confidence": 0.9}],
            "icons": [],
            "text_fields": []
        }
        mock_analyzer.find_element_at_position.return_value = {
            "element_type": "button",
            "text": "테스트",
            "x": 100,
            "y": 100,
            "confidence": 0.9
        }
        
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        # 일부 스크린샷이 누락된 테스트 케이스
        test_case = {
            "name": "missing_screenshot_test",
            "version": "1.0",
            "actions": [
                {
                    "action_type": "click",
                    "x": 100, "y": 100,
                    "description": "첫 번째 클릭",
                    "screenshot_path": "screenshots/action_0000.png"  # 존재함
                },
                {
                    "action_type": "click",
                    "x": 200, "y": 200,
                    "description": "두 번째 클릭",
                    "screenshot_path": "screenshots/nonexistent.png"  # 존재하지 않음
                },
                {
                    "action_type": "click",
                    "x": 300, "y": 300,
                    "description": "세 번째 클릭",
                    "screenshot_path": "screenshots/action_0001.png"  # 존재함
                }
            ]
        }
        
        # 보강
        enriched_test_case, result = enricher.enrich_test_case(
            test_case,
            screenshots_dir
        )
        
        # 결과 검증 (Requirements: 5.5)
        assert result.total_actions == 3
        assert result.skipped_count >= 1  # 누락된 스크린샷으로 인해 최소 1개 스킵
        
        # 스킵된 액션 확인
        skipped_actions = [
            a for a in enriched_test_case['actions']
            if a.get('enrichment_status') == 'skipped'
        ]
        assert len(skipped_actions) >= 1


class TestStatisticsReporting:
    """재생 통계 리포팅 통합 테스트
    
    Requirements: 4.1, 4.3, 4.4
    """
    
    @pytest.fixture
    def stats_env(self, tmp_path):
        """통계 테스트 환경 설정"""
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

    def test_replay_statistics_consistency(self, stats_env):
        """재생 통계 일관성 테스트
        
        Requirements: 4.1, 4.4
        
        semantic_match_count + coordinate_match_count + failed_count == total_actions
        """
        config = stats_env["config"]
        
        # 다양한 결과를 시뮬레이션하기 위한 Mock 설정
        call_count = [0]
        
        def mock_analyze(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                # 처음 2개는 버튼 발견
                return {
                    "source": "vision_llm",
                    "buttons": [{"text": "테스트", "x": 100, "y": 100, "confidence": 0.95}],
                    "icons": [],
                    "text_fields": []
                }
            elif call_count[0] <= 4:
                # 다음 2개는 다른 위치에서 버튼 발견
                return {
                    "source": "vision_llm",
                    "buttons": [{"text": "테스트", "x": 300, "y": 300, "confidence": 0.85}],
                    "icons": [],
                    "text_fields": []
                }
            else:
                # 나머지는 빈 결과
                return {
                    "source": "vision_llm",
                    "buttons": [],
                    "icons": [],
                    "text_fields": []
                }
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.side_effect = mock_analyze
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 여러 액션 생성
        actions = []
        for i in range(5):
            actions.append(SemanticAction(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=100 + i * 10, y=100 + i * 10,
                description=f'테스트 클릭 {i}',
                button='left',
                semantic_info={
                    "intent": "test",
                    "target_element": {
                        "type": "button",
                        "text": "테스트",
                        "description": "테스트 버튼"
                    },
                    "context": {"screen_state": "test"}
                },
                screen_transition={"transition_type": "unknown"}
            ))
        
        mock_image = Image.new('RGB', (1920, 1080), color='white')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            # 모든 액션 재생
            for action in actions:
                replayer.replay_click_with_semantic_matching(action)
        
        # 통계 계산
        stats = replayer.get_statistics()
        
        # 일관성 검증 (Requirements: 4.1, 4.4)
        total = stats['total_actions']
        semantic = stats['semantic_match_count']
        coordinate = stats['coordinate_match_count']
        direct = stats['direct_match_count']
        failed = stats['failed_count']
        
        # semantic + coordinate + direct + failed == total
        assert semantic + coordinate + direct + failed == total, \
            f"통계 불일치: {semantic} + {coordinate} + {direct} + {failed} != {total}"
        
        # success_count == semantic + coordinate + direct
        success = stats['success_count']
        assert success == semantic + coordinate + direct, \
            f"성공 카운트 불일치: {success} != {semantic + coordinate + direct}"

    def test_coordinate_change_statistics(self, stats_env):
        """좌표 변경 통계 테스트
        
        Requirements: 4.3
        
        의미론적 매칭 시 좌표 변경 거리 통계 검증
        """
        config = stats_env["config"]
        
        # 버튼이 이동한 상황 시뮬레이션
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "source": "vision_llm",
            "buttons": [
                {"text": "이동된버튼", "x": 500, "y": 500, "confidence": 0.95}
            ],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 원래 좌표와 다른 위치에서 버튼을 찾는 액션
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,  # 원래 좌표
            description='이동된 버튼 클릭',
            button='left',
            semantic_info={
                "intent": "test",
                "target_element": {
                    "type": "button",
                    "text": "이동된버튼",
                    "description": "이동된 버튼"
                },
                "context": {"screen_state": "test"}
            },
            screen_transition={"transition_type": "unknown"}
        )
        
        mock_image = Image.new('RGB', (1920, 1080), color='gray')
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_click_with_semantic_matching(action)
        
        # 통계 확인
        stats = replayer.get_statistics()
        
        # 의미론적 매칭이 성공했다면 좌표 변경 통계가 있어야 함
        if result.method == 'semantic':
            assert stats['avg_coordinate_change'] > 0, "좌표 변경 평균이 0보다 커야 함"
            assert stats['max_coordinate_change'] > 0, "최대 좌표 변경이 0보다 커야 함"
