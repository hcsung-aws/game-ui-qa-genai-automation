"""
QAAutomationController 테스트

Requirements: 1.1, 3.1, 3.8, 5.1, 6.1
"""

import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

from src.qa_automation_controller import QAAutomationController
from src.input_monitor import Action


class TestQAAutomationControllerInit:
    """QAAutomationController 초기화 테스트"""
    
    def test_init_with_default_config_path(self):
        """기본 설정 파일 경로로 초기화"""
        controller = QAAutomationController()
        assert controller.config_path == 'config.json'
        assert controller._initialized is False
    
    def test_init_with_custom_config_path(self):
        """사용자 정의 설정 파일 경로로 초기화"""
        controller = QAAutomationController('custom_config.json')
        assert controller.config_path == 'custom_config.json'


class TestQAAutomationControllerInitialize:
    """QAAutomationController.initialize() 테스트"""
    
    @pytest.fixture
    def temp_dir(self):
        """임시 디렉토리 생성"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)
    
    def test_initialize_creates_default_config_if_not_exists(self, temp_dir):
        """설정 파일이 없으면 기본 설정 생성"""
        config_path = os.path.join(temp_dir, 'config.json')
        controller = QAAutomationController(config_path)
        
        result = controller.initialize()
        
        assert result is True
        assert os.path.exists(config_path)
        assert controller._initialized is True
    
    def test_initialize_loads_existing_config(self, temp_dir):
        """기존 설정 파일 로드"""
        config_path = os.path.join(temp_dir, 'config.json')
        config_data = {
            "aws": {"region": "us-west-2"},
            "game": {"exe_path": "test.exe", "startup_wait": 3},
            "automation": {"screenshot_dir": "shots", "action_delay": 0.3},
            "test_cases": {"directory": "cases"}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        controller = QAAutomationController(config_path)
        result = controller.initialize()
        
        assert result is True
        assert controller.config_manager.get('aws.region') == 'us-west-2'
    
    def test_initialize_creates_directories(self, temp_dir):
        """필요한 디렉토리 생성"""
        config_path = os.path.join(temp_dir, 'config.json')
        controller = QAAutomationController(config_path)
        
        # 현재 디렉토리를 임시 디렉토리로 변경
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            controller.initialize()
            
            # 기본 디렉토리가 생성되었는지 확인
            assert os.path.exists('screenshots')
            assert os.path.exists('test_cases')
        finally:
            os.chdir(original_cwd)
    
    def test_initialize_creates_all_components(self, temp_dir):
        """모든 컴포넌트 초기화"""
        config_path = os.path.join(temp_dir, 'config.json')
        controller = QAAutomationController(config_path)
        
        controller.initialize()
        
        assert controller.game_manager is not None
        assert controller.action_recorder is not None
        assert controller.input_monitor is not None
        assert controller.script_generator is not None


class TestQAAutomationControllerRecording:
    """녹화 기능 테스트"""
    
    @pytest.fixture
    def controller(self, tmp_path):
        """초기화된 컨트롤러"""
        config_path = tmp_path / 'config.json'
        ctrl = QAAutomationController(str(config_path))
        ctrl.initialize()
        return ctrl
    
    def test_start_recording(self, controller):
        """기록 시작 (Requirements 3.1)"""
        controller.start_recording()
        
        assert controller.input_monitor.is_recording is True
    
    def test_stop_recording(self, controller):
        """기록 중지 (Requirements 3.8)"""
        controller.start_recording()
        controller.stop_recording()
        
        assert controller.input_monitor.is_recording is False
    
    def test_get_actions_returns_empty_list_initially(self, controller):
        """초기에는 빈 액션 리스트 반환"""
        actions = controller.get_actions()
        
        assert actions == []
    
    def test_clear_actions_on_start_recording(self, controller):
        """기록 시작 시 이전 액션 초기화"""
        # 수동으로 액션 추가
        test_action = Action(
            timestamp="2025-01-01T00:00:00",
            action_type="click",
            x=100, y=200,
            description="테스트 클릭"
        )
        controller.action_recorder.actions.append(test_action)
        
        # 기록 시작하면 초기화됨
        controller.start_recording()
        
        assert len(controller.get_actions()) == 0


class TestQAAutomationControllerSaveTestCase:
    """테스트 케이스 저장 테스트"""
    
    @pytest.fixture
    def controller_with_actions(self, tmp_path):
        """액션이 있는 컨트롤러"""
        config_path = tmp_path / 'config.json'
        ctrl = QAAutomationController(str(config_path))
        
        # 현재 디렉토리를 임시 디렉토리로 변경
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        ctrl.initialize()
        
        # 테스트 액션 추가
        test_actions = [
            Action(
                timestamp="2025-01-01T00:00:00",
                action_type="click",
                x=100, y=200,
                description="버튼 클릭",
                button="left"
            ),
            Action(
                timestamp="2025-01-01T00:00:01",
                action_type="key_press",
                x=0, y=0,
                description="키 입력: a",
                key="a"
            )
        ]
        ctrl.action_recorder.actions = test_actions
        
        yield ctrl, tmp_path
        
        os.chdir(original_cwd)
    
    def test_save_test_case_creates_script(self, controller_with_actions):
        """테스트 케이스 저장 시 스크립트 생성 (Requirements 5.1)"""
        controller, tmp_path = controller_with_actions
        
        result = controller.save_test_case("test_case_1")
        
        script_path = tmp_path / "test_cases" / "test_case_1.py"
        assert os.path.exists(script_path)
    
    def test_save_test_case_creates_json(self, controller_with_actions):
        """테스트 케이스 저장 시 JSON 파일 생성"""
        controller, tmp_path = controller_with_actions
        
        result = controller.save_test_case("test_case_1")
        
        json_path = tmp_path / "test_cases" / "test_case_1.json"
        assert os.path.exists(json_path)
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['name'] == 'test_case_1'
        assert len(data['actions']) == 2
    
    def test_save_test_case_returns_test_case_data(self, controller_with_actions):
        """저장된 테스트 케이스 정보 반환"""
        controller, tmp_path = controller_with_actions
        
        result = controller.save_test_case("test_case_1")
        
        assert result['name'] == 'test_case_1'
        assert 'created_at' in result
        assert 'script_path' in result
        assert 'json_path' in result
        assert len(result['actions']) == 2
    
    def test_save_test_case_raises_error_when_no_actions(self, tmp_path):
        """액션이 없으면 에러 발생"""
        config_path = tmp_path / 'config.json'
        controller = QAAutomationController(str(config_path))
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            controller.initialize()
            
            with pytest.raises(ValueError, match="저장할 액션이 없습니다"):
                controller.save_test_case("empty_test")
        finally:
            os.chdir(original_cwd)


class TestQAAutomationControllerLoadTestCase:
    """테스트 케이스 로드 테스트"""
    
    @pytest.fixture
    def controller_with_saved_test(self, tmp_path):
        """저장된 테스트 케이스가 있는 컨트롤러"""
        config_path = tmp_path / 'config.json'
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        controller = QAAutomationController(str(config_path))
        controller.initialize()
        
        # 테스트 케이스 JSON 직접 생성
        test_cases_dir = tmp_path / 'test_cases'
        test_cases_dir.mkdir(exist_ok=True)
        
        test_case_data = {
            "name": "saved_test",
            "created_at": "2025-01-01T00:00:00",
            "script_path": str(test_cases_dir / "saved_test.py"),
            "json_path": str(test_cases_dir / "saved_test.json"),
            "actions": [
                {
                    "timestamp": "2025-01-01T00:00:00",
                    "action_type": "click",
                    "x": 100, "y": 200,
                    "description": "테스트 클릭"
                }
            ]
        }
        
        with open(test_cases_dir / "saved_test.json", 'w', encoding='utf-8') as f:
            json.dump(test_case_data, f)
        
        yield controller, tmp_path
        
        os.chdir(original_cwd)
    
    def test_load_test_case_success(self, controller_with_saved_test):
        """테스트 케이스 로드 성공"""
        controller, tmp_path = controller_with_saved_test
        
        result = controller.load_test_case("saved_test")
        
        assert result['name'] == 'saved_test'
        assert len(result['actions']) == 1
        assert controller.current_test_case is not None
    
    def test_load_test_case_not_found(self, controller_with_saved_test):
        """존재하지 않는 테스트 케이스 로드 시 에러"""
        controller, tmp_path = controller_with_saved_test
        
        with pytest.raises(FileNotFoundError):
            controller.load_test_case("nonexistent_test")


class TestQAAutomationControllerListTestCases:
    """테스트 케이스 목록 테스트"""
    
    def test_list_test_cases_empty(self, tmp_path):
        """테스트 케이스가 없을 때 빈 리스트 반환"""
        config_path = tmp_path / 'config.json'
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            controller = QAAutomationController(str(config_path))
            controller.initialize()
            
            result = controller.list_test_cases()
            
            assert result == []
        finally:
            os.chdir(original_cwd)
    
    def test_list_test_cases_returns_all(self, tmp_path):
        """모든 테스트 케이스 반환"""
        config_path = tmp_path / 'config.json'
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            controller = QAAutomationController(str(config_path))
            controller.initialize()
            
            # 테스트 케이스 생성
            test_cases_dir = tmp_path / 'test_cases'
            for i in range(3):
                data = {
                    "name": f"test_{i}",
                    "created_at": f"2025-01-0{i+1}T00:00:00",
                    "actions": []
                }
                with open(test_cases_dir / f"test_{i}.json", 'w', encoding='utf-8') as f:
                    json.dump(data, f)
            
            result = controller.list_test_cases()
            
            assert len(result) == 3
            names = [tc['name'] for tc in result]
            assert 'test_0' in names
            assert 'test_1' in names
            assert 'test_2' in names
        finally:
            os.chdir(original_cwd)


class TestQAAutomationControllerReplay:
    """테스트 케이스 재실행 테스트"""
    
    def test_replay_without_loaded_test_case_raises_error(self, tmp_path):
        """로드된 테스트 케이스 없이 재실행 시 에러"""
        config_path = tmp_path / 'config.json'
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            controller = QAAutomationController(str(config_path))
            controller.initialize()
            
            with pytest.raises(ValueError, match="로드된 테스트 케이스가 없습니다"):
                controller.replay_test_case()
        finally:
            os.chdir(original_cwd)


class TestQAAutomationControllerCleanup:
    """리소스 정리 테스트"""
    
    def test_cleanup_stops_recording(self, tmp_path):
        """cleanup 시 녹화 중지"""
        config_path = tmp_path / 'config.json'
        controller = QAAutomationController(str(config_path))
        controller.initialize()
        
        controller.start_recording()
        controller.cleanup()
        
        assert controller.input_monitor.is_recording is False


class TestQAAutomationControllerStats:
    """실행 이력 및 통계 테스트 (Requirements 15.1, 15.2)"""
    
    @pytest.fixture
    def controller_with_accuracy_data(self, tmp_path):
        """정확도 데이터가 있는 컨트롤러"""
        config_path = tmp_path / 'config.json'
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        controller = QAAutomationController(str(config_path))
        controller.initialize()
        
        # 테스트 케이스 생성
        test_cases_dir = tmp_path / 'test_cases'
        test_cases_dir.mkdir(exist_ok=True)
        
        test_case_data = {
            "name": "stats_test",
            "created_at": "2025-01-01T00:00:00",
            "script_path": str(test_cases_dir / "stats_test.py"),
            "json_path": str(test_cases_dir / "stats_test.json"),
            "actions": []
        }
        
        with open(test_cases_dir / "stats_test.json", 'w', encoding='utf-8') as f:
            json.dump(test_case_data, f)
        
        # 정확도 데이터 생성
        accuracy_dir = tmp_path / 'accuracy_data' / 'stats_test'
        accuracy_dir.mkdir(parents=True, exist_ok=True)
        
        # 세션 1 통계
        stats_data_1 = {
            "test_case_name": "stats_test",
            "session_id": "20251223_100000_000001",
            "timestamp": "2025-12-23T10:00:00",
            "statistics": {
                "total_actions": 10,
                "success_count": 9,
                "failure_count": 1,
                "success_rate": 0.9,
                "direct_match_count": 7,
                "semantic_match_count": 2,
                "manual_match_count": 0,
                "direct_match_rate": 0.78,
                "semantic_match_rate": 0.22,
                "avg_coordinate_change": 15.5,
                "avg_execution_time": 0.5,
                "failure_reasons": {"element_not_found": 1},
                "transition_match_count": 9,
                "transition_mismatch_count": 1
            }
        }
        
        with open(accuracy_dir / "20251223_100000_000001_stats.json", 'w', encoding='utf-8') as f:
            json.dump(stats_data_1, f)
        
        # 세션 2 통계
        stats_data_2 = {
            "test_case_name": "stats_test",
            "session_id": "20251222_150000_000001",
            "timestamp": "2025-12-22T15:00:00",
            "statistics": {
                "total_actions": 10,
                "success_count": 8,
                "failure_count": 2,
                "success_rate": 0.8,
                "direct_match_count": 5,
                "semantic_match_count": 3,
                "manual_match_count": 0,
                "direct_match_rate": 0.625,
                "semantic_match_rate": 0.375,
                "avg_coordinate_change": 20.0,
                "avg_execution_time": 0.6,
                "failure_reasons": {"element_not_found": 2},
                "transition_match_count": 8,
                "transition_mismatch_count": 2
            }
        }
        
        with open(accuracy_dir / "20251222_150000_000001_stats.json", 'w', encoding='utf-8') as f:
            json.dump(stats_data_2, f)
        
        yield controller, tmp_path
        
        os.chdir(original_cwd)
    
    def test_get_execution_history_with_name(self, controller_with_accuracy_data):
        """테스트 케이스 이름으로 실행 이력 조회 (Requirements 15.1)"""
        controller, tmp_path = controller_with_accuracy_data
        
        history = controller.get_execution_history("stats_test")
        
        assert len(history) == 2
        # 최신순 정렬 확인
        assert history[0]["session_id"] == "20251223_100000_000001"
        assert history[1]["session_id"] == "20251222_150000_000001"
    
    def test_get_execution_history_with_loaded_test_case(self, controller_with_accuracy_data):
        """로드된 테스트 케이스로 실행 이력 조회"""
        controller, tmp_path = controller_with_accuracy_data
        
        controller.load_test_case("stats_test")
        history = controller.get_execution_history()
        
        assert len(history) == 2
    
    def test_get_execution_history_no_test_case_raises_error(self, tmp_path):
        """테스트 케이스 미지정 시 에러"""
        config_path = tmp_path / 'config.json'
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            controller = QAAutomationController(str(config_path))
            controller.initialize()
            
            with pytest.raises(ValueError, match="테스트 케이스가 지정되지 않았습니다"):
                controller.get_execution_history()
        finally:
            os.chdir(original_cwd)
    
    def test_get_execution_history_contains_required_fields(self, controller_with_accuracy_data):
        """실행 이력에 필수 필드 포함 확인 (Requirements 15.2)"""
        controller, tmp_path = controller_with_accuracy_data
        
        history = controller.get_execution_history("stats_test")
        
        for session in history:
            # Requirements 15.2: 날짜, 성공률, 오류 수, 의미론적 매칭 사용률
            assert "timestamp" in session  # 날짜
            assert "success_rate" in session  # 성공률
            assert "failure_count" in session  # 오류 수
            assert "semantic_match_rate" in session  # 의미론적 매칭 사용률
    
    def test_get_execution_statistics(self, controller_with_accuracy_data):
        """실행 통계 요약 조회"""
        controller, tmp_path = controller_with_accuracy_data
        
        stats = controller.get_execution_statistics("stats_test")
        
        assert stats["test_case_name"] == "stats_test"
        assert stats["total_executions"] == 2
        assert abs(stats["avg_success_rate"] - 0.85) < 0.001  # (0.9 + 0.8) / 2
        assert stats["total_errors"] == 3  # 1 + 2
        assert abs(stats["avg_semantic_match_rate"] - (0.22 + 0.375) / 2) < 0.001
        assert stats["latest_execution"] is not None
    
    def test_get_execution_statistics_empty(self, tmp_path):
        """실행 이력이 없을 때 통계"""
        config_path = tmp_path / 'config.json'
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            controller = QAAutomationController(str(config_path))
            controller.initialize()
            
            # 빈 테스트 케이스 생성
            test_cases_dir = tmp_path / 'test_cases'
            test_cases_dir.mkdir(exist_ok=True)
            
            test_case_data = {
                "name": "empty_stats_test",
                "created_at": "2025-01-01T00:00:00",
                "actions": []
            }
            
            with open(test_cases_dir / "empty_stats_test.json", 'w', encoding='utf-8') as f:
                json.dump(test_case_data, f)
            
            controller.load_test_case("empty_stats_test")
            stats = controller.get_execution_statistics()
            
            assert stats["total_executions"] == 0
            assert stats["avg_success_rate"] == 0.0
            assert stats["total_errors"] == 0
            assert stats["latest_execution"] is None
        finally:
            os.chdir(original_cwd)
