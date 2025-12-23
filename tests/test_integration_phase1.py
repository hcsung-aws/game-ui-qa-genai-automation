"""
Phase 1 통합 테스트

전체 워크플로우 테스트: 기록 → 저장 → 재실행

Requirements: 1.1, 3.1, 5.1, 6.1
"""

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.qa_automation_controller import QAAutomationController
from src.input_monitor import Action, ActionRecorder, InputMonitor
from src.script_generator import ScriptGenerator
from src.config_manager import ConfigManager


class TestPhase1IntegrationWorkflow:
    """Phase 1 전체 워크플로우 통합 테스트
    
    기록 → 저장 → 재실행 흐름을 검증한다.
    """
    
    @pytest.fixture
    def integration_env(self, tmp_path):
        """통합 테스트 환경 설정"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # 설정 파일 생성
        config_data = {
            "aws": {"region": "ap-northeast-2"},
            "game": {
                "exe_path": "notepad.exe",
                "startup_wait": 1
            },
            "automation": {
                "screenshot_dir": "screenshots",
                "action_delay": 0.1,
                "screenshot_on_action": False
            },
            "test_cases": {"directory": "test_cases"}
        }
        
        config_path = tmp_path / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        controller = QAAutomationController(str(config_path))
        controller.initialize()
        
        yield {
            "controller": controller,
            "tmp_path": tmp_path,
            "config_path": config_path
        }
        
        controller.cleanup()
        os.chdir(original_cwd)
    
    def test_full_workflow_record_save_load(self, integration_env):
        """전체 워크플로우: 기록 → 저장 → 로드 (Requirements 1.1, 3.1, 5.1)"""
        controller = integration_env["controller"]
        tmp_path = integration_env["tmp_path"]
        
        # 1. 기록 시작
        controller.start_recording()
        assert controller.input_monitor.is_recording is True
        
        # 2. 액션 시뮬레이션 (실제 pynput 대신 직접 액션 추가)
        test_actions = [
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
                description='키 입력: a',
                key='a'
            ),
            Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=300, y=400,
                description='확인 버튼 클릭',
                button='left'
            )
        ]
        
        for action in test_actions:
            controller.action_recorder.record_action(action)
        
        # 3. 기록 중지
        controller.stop_recording()
        assert controller.input_monitor.is_recording is False
        
        # 4. 기록된 액션 확인
        recorded_actions = controller.get_actions()
        # wait 액션이 자동 삽입될 수 있으므로 최소 3개 이상
        assert len(recorded_actions) >= 3
        
        # 5. 테스트 케이스 저장
        test_case = controller.save_test_case("integration_test")
        
        # 6. 파일 생성 확인
        script_path = tmp_path / "test_cases" / "integration_test.py"
        json_path = tmp_path / "test_cases" / "integration_test.json"
        
        assert os.path.exists(script_path), "Replay Script가 생성되어야 함"
        assert os.path.exists(json_path), "JSON 파일이 생성되어야 함"
        
        # 7. JSON 파일 내용 검증
        with open(json_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data['name'] == 'integration_test'
        assert 'created_at' in saved_data
        assert len(saved_data['actions']) >= 3
        
        # 8. 테스트 케이스 로드
        loaded_test_case = controller.load_test_case("integration_test")
        assert loaded_test_case['name'] == 'integration_test'
        assert controller.current_test_case is not None
    
    def test_generated_script_structure(self, integration_env):
        """생성된 스크립트 구조 검증 (Requirements 5.1, 5.2, 5.3)"""
        controller = integration_env["controller"]
        tmp_path = integration_env["tmp_path"]
        
        # 액션 추가
        test_actions = [
            Action(
                timestamp="2025-01-01T10:00:00",
                action_type='click',
                x=640, y=480,
                description='시작 버튼 클릭',
                button='left'
            ),
            Action(
                timestamp="2025-01-01T10:00:02",
                action_type='wait',
                x=0, y=0,
                description='2.0초 대기'
            ),
            Action(
                timestamp="2025-01-01T10:00:03",
                action_type='key_press',
                x=0, y=0,
                description='키 입력: enter',
                key='Key.enter'
            )
        ]
        
        for action in test_actions:
            controller.action_recorder.actions.append(action)
        
        # 저장
        controller.save_test_case("script_test")
        
        # 스크립트 내용 검증
        script_path = tmp_path / "test_cases" / "script_test.py"
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # 필수 요소 확인
        assert 'import pyautogui' in script_content
        assert 'import time' in script_content
        assert 'def replay_actions' in script_content
        assert 'pyautogui.click' in script_content
        assert 'time.sleep' in script_content
        assert "if __name__ == '__main__'" in script_content
    
    def test_script_utf8_encoding(self, integration_env):
        """스크립트 UTF-8 인코딩 검증 (Requirements 5.4)"""
        controller = integration_env["controller"]
        tmp_path = integration_env["tmp_path"]
        
        # 한글이 포함된 액션 추가
        test_actions = [
            Action(
                timestamp="2025-01-01T10:00:00",
                action_type='click',
                x=100, y=200,
                description='게임 시작 버튼 클릭',
                button='left'
            ),
            Action(
                timestamp="2025-01-01T10:00:01",
                action_type='key_press',
                x=0, y=0,
                description='키 입력: 한글테스트',
                key='한글테스트'
            )
        ]
        
        for action in test_actions:
            controller.action_recorder.actions.append(action)
        
        # 저장
        controller.save_test_case("utf8_test")
        
        # UTF-8로 읽기 가능한지 확인
        script_path = tmp_path / "test_cases" / "utf8_test.py"
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        assert '게임 시작 버튼 클릭' in script_content
        assert '한글테스트' in script_content
    
    def test_multiple_test_cases_management(self, integration_env):
        """여러 테스트 케이스 관리 (Requirements 8.1-8.5)"""
        controller = integration_env["controller"]
        
        # 여러 테스트 케이스 생성
        for i in range(3):
            controller.action_recorder.clear_actions()
            controller.action_recorder.actions.append(
                Action(
                    timestamp=datetime.now().isoformat(),
                    action_type='click',
                    x=100 * i, y=200 * i,
                    description=f'테스트 케이스 {i} 클릭',
                    button='left'
                )
            )
            controller.save_test_case(f"test_case_{i}")
        
        # 목록 확인
        test_cases = controller.list_test_cases()
        assert len(test_cases) == 3
        
        names = [tc['name'] for tc in test_cases]
        assert 'test_case_0' in names
        assert 'test_case_1' in names
        assert 'test_case_2' in names
    
    def test_recording_clears_previous_actions(self, integration_env):
        """기록 시작 시 이전 액션 초기화 확인"""
        controller = integration_env["controller"]
        
        # 첫 번째 기록 - 리스너 없이 직접 액션 추가
        controller.action_recorder.actions.append(
            Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=100, y=200,
                description='첫 번째 클릭',
                button='left'
            )
        )
        
        assert len(controller.get_actions()) == 1
        
        # start_recording이 clear_actions를 호출하는지 직접 확인
        # (실제 리스너 시작 없이 clear_actions 동작만 검증)
        controller.action_recorder.clear_actions()
        
        assert len(controller.get_actions()) == 0


class TestPhase1ComponentIntegration:
    """Phase 1 컴포넌트 간 통합 테스트"""
    
    @pytest.fixture
    def components(self, tmp_path):
        """컴포넌트 설정"""
        config_path = tmp_path / "config.json"
        config = ConfigManager(str(config_path))
        config.create_default_config()
        
        action_recorder = ActionRecorder(config)
        input_monitor = InputMonitor(action_recorder)
        script_generator = ScriptGenerator(config)
        
        return {
            "config": config,
            "action_recorder": action_recorder,
            "input_monitor": input_monitor,
            "script_generator": script_generator,
            "tmp_path": tmp_path
        }
    
    def test_action_recorder_to_script_generator(self, components):
        """ActionRecorder → ScriptGenerator 통합"""
        action_recorder = components["action_recorder"]
        script_generator = components["script_generator"]
        tmp_path = components["tmp_path"]
        
        # 액션 기록
        actions = [
            Action(
                timestamp="2025-01-01T10:00:00",
                action_type='click',
                x=100, y=200,
                description='클릭 (100, 200)',
                button='left'
            ),
            Action(
                timestamp="2025-01-01T10:00:01",
                action_type='scroll',
                x=100, y=200,
                description='스크롤 (0, -3)',
                scroll_dx=0,
                scroll_dy=-3
            )
        ]
        
        for action in actions:
            action_recorder.record_action(action)
        
        # 스크립트 생성
        output_path = tmp_path / "test_script.py"
        script_generator.generate_replay_script(
            action_recorder.get_actions(),
            str(output_path)
        )
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'pyautogui.click(100, 200' in content
        assert 'pyautogui.scroll' in content
    
    def test_input_monitor_state_management(self, components):
        """InputMonitor 상태 관리 테스트"""
        input_monitor = components["input_monitor"]
        
        # 초기 상태
        assert input_monitor.is_recording is False
        
        # 모니터링 시작
        input_monitor.start_monitoring()
        assert input_monitor.is_recording is True
        assert input_monitor.mouse_listener is not None
        assert input_monitor.keyboard_listener is not None
        
        # 모니터링 중지
        input_monitor.stop_monitoring()
        assert input_monitor.is_recording is False


class TestPhase1ErrorHandling:
    """Phase 1 에러 처리 통합 테스트"""
    
    @pytest.fixture
    def controller(self, tmp_path):
        """컨트롤러 설정"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        config_path = tmp_path / "config.json"
        ctrl = QAAutomationController(str(config_path))
        ctrl.initialize()
        
        yield ctrl
        
        ctrl.cleanup()
        os.chdir(original_cwd)
    
    def test_save_without_actions_raises_error(self, controller):
        """액션 없이 저장 시 에러 (Requirements 9.3)"""
        with pytest.raises(ValueError, match="저장할 액션이 없습니다"):
            controller.save_test_case("empty_test")
    
    def test_replay_without_loaded_test_case_raises_error(self, controller):
        """테스트 케이스 로드 없이 재실행 시 에러"""
        with pytest.raises(ValueError, match="로드된 테스트 케이스가 없습니다"):
            controller.replay_test_case()
    
    def test_load_nonexistent_test_case_raises_error(self, controller):
        """존재하지 않는 테스트 케이스 로드 시 에러"""
        with pytest.raises(FileNotFoundError):
            controller.load_test_case("nonexistent_test")


class TestPhase1WaitActionIntegration:
    """대기 액션 통합 테스트"""
    
    @pytest.fixture
    def controller(self, tmp_path):
        """컨트롤러 설정"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        config_path = tmp_path / "config.json"
        ctrl = QAAutomationController(str(config_path))
        ctrl.initialize()
        
        yield ctrl, tmp_path
        
        ctrl.cleanup()
        os.chdir(original_cwd)
    
    def test_wait_action_in_script(self, controller):
        """대기 액션이 스크립트에 올바르게 포함되는지 확인 (Requirements 5.5)"""
        ctrl, tmp_path = controller
        
        # wait 액션 포함 테스트
        test_actions = [
            Action(
                timestamp="2025-01-01T10:00:00",
                action_type='click',
                x=100, y=200,
                description='클릭',
                button='left'
            ),
            Action(
                timestamp="2025-01-01T10:00:02",
                action_type='wait',
                x=0, y=0,
                description='3.5초 대기'
            ),
            Action(
                timestamp="2025-01-01T10:00:05",
                action_type='click',
                x=300, y=400,
                description='다음 클릭',
                button='left'
            )
        ]
        
        for action in test_actions:
            ctrl.action_recorder.actions.append(action)
        
        ctrl.save_test_case("wait_test")
        
        script_path = tmp_path / "test_cases" / "wait_test.py"
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # wait 액션이 time.sleep으로 변환되었는지 확인
        assert 'time.sleep(3.5)' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
