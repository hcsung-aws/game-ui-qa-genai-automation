# -*- coding: utf-8 -*-
"""
Phase 4 통합 테스트

여러 세션 실행 및 통계 검증

Requirements: 13.1-13.6, 15.1, 15.2
"""

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import time

from src.config_manager import ConfigManager
from src.accuracy_tracker import AccuracyTracker, ActionExecutionResult, AccuracyStatistics
from src.qa_automation_controller import QAAutomationController
from src.cli_interface import CLIInterface


class TestPhase4AccuracyTracking:
    """Phase 4 정확도 추적 통합 테스트
    
    Requirements: 13.1-13.6
    """
    
    @pytest.fixture
    def tracker_env(self, tmp_path):
        """정확도 추적 테스트 환경 설정"""
        data_dir = tmp_path / "accuracy_data"
        os.makedirs(data_dir, exist_ok=True)
        
        yield {
            "data_dir": str(data_dir),
            "tmp_path": tmp_path
        }

    def test_new_session_creation(self, tracker_env):
        """새 실행 세션 생성 테스트 (Requirements 13.1)"""
        data_dir = tracker_env["data_dir"]
        
        tracker = AccuracyTracker("test_case_1", data_dir=data_dir)
        
        # 세션 ID 확인
        session_id = tracker.get_session_id()
        assert session_id is not None
        assert len(session_id) > 0
        
        # 새 세션 시작
        new_session_id = tracker.start_session()
        assert new_session_id != session_id
        
        # 결과가 초기화되었는지 확인
        assert len(tracker.get_results()) == 0
    
    def test_action_success_failure_recording(self, tracker_env):
        """액션 성공/실패 기록 테스트 (Requirements 13.2)"""
        data_dir = tracker_env["data_dir"]
        
        tracker = AccuracyTracker("test_case_2", data_dir=data_dir)
        
        # 성공 기록
        success_result = tracker.record_success(
            action_id="action_001",
            method='direct',
            original_coords=(100, 200),
            actual_coords=(100, 200),
            execution_time=0.5
        )
        
        assert success_result.success == True
        assert success_result.method == 'direct'
        assert success_result.action_id == "action_001"
        
        # 실패 기록
        failure_result = tracker.record_failure(
            action_id="action_002",
            reason='element_not_found',
            original_coords=(300, 400),
            execution_time=1.0
        )
        
        assert failure_result.success == False
        assert failure_result.method == 'failed'
        assert failure_result.failure_reason == 'element_not_found'
        
        # 결과 목록 확인
        results = tracker.get_results()
        assert len(results) == 2

    def test_semantic_matching_coordinate_change_recording(self, tracker_env):
        """의미론적 매칭 시 좌표 변경 기록 테스트 (Requirements 13.3)"""
        data_dir = tracker_env["data_dir"]
        
        tracker = AccuracyTracker("test_case_3", data_dir=data_dir)
        
        # 의미론적 매칭으로 좌표가 변경된 경우
        result = tracker.record_success(
            action_id="action_semantic",
            method='semantic',
            original_coords=(100, 100),
            actual_coords=(300, 250),
            execution_time=1.5
        )
        
        # 좌표 변경 기록 확인
        assert result.coordinate_change == (200, 150)
        assert result.original_coords == (100, 100)
        assert result.actual_coords == (300, 250)
    
    def test_screen_transition_verification_recording(self, tracker_env):
        """화면 전환 검증 기록 테스트 (Requirements 13.4)"""
        data_dir = tracker_env["data_dir"]
        
        tracker = AccuracyTracker("test_case_4", data_dir=data_dir)
        
        # 화면 전환 일치
        result_match = tracker.record_success(
            action_id="action_match",
            method='direct',
            original_coords=(100, 100),
            actual_coords=(100, 100),
            screen_transition_matched=True
        )
        assert result_match.screen_transition_matched == True
        
        # 화면 전환 불일치
        result_mismatch = tracker.record_success(
            action_id="action_mismatch",
            method='semantic',
            original_coords=(100, 100),
            actual_coords=(200, 200),
            screen_transition_matched=False
        )
        assert result_mismatch.screen_transition_matched == False

    def test_statistics_calculation_after_replay(self, tracker_env):
        """재실행 완료 후 통계 계산 테스트 (Requirements 13.5, 13.6)"""
        data_dir = tracker_env["data_dir"]
        
        tracker = AccuracyTracker("test_case_5", data_dir=data_dir)
        
        # 다양한 결과 기록
        # 직접 매칭 성공 3개
        for i in range(3):
            tracker.record_success(
                action_id=f"direct_{i}",
                method='direct',
                original_coords=(100 + i*10, 100 + i*10),
                actual_coords=(100 + i*10, 100 + i*10),
                execution_time=0.3
            )
        
        # 의미론적 매칭 성공 2개
        for i in range(2):
            tracker.record_success(
                action_id=f"semantic_{i}",
                method='semantic',
                original_coords=(200 + i*10, 200 + i*10),
                actual_coords=(250 + i*10, 250 + i*10),
                execution_time=1.0
            )
        
        # 실패 2개
        tracker.record_failure(
            action_id="fail_1",
            reason='element_not_found',
            original_coords=(300, 300),
            execution_time=0.5
        )
        tracker.record_failure(
            action_id="fail_2",
            reason='timeout',
            original_coords=(400, 400),
            execution_time=2.0
        )
        
        # 통계 계산
        stats = tracker.calculate_statistics()
        
        # 통계 검증
        assert stats.total_actions == 7
        assert stats.success_count == 5
        assert stats.failure_count == 2
        assert abs(stats.success_rate - 5/7) < 0.001
        
        # 매칭 방법 비율 검증
        assert stats.direct_match_count == 3
        assert stats.semantic_match_count == 2
        assert abs(stats.direct_match_rate - 3/5) < 0.001
        assert abs(stats.semantic_match_rate - 2/5) < 0.001
        
        # 평균 좌표 변경 거리 검증 (의미론적 매칭에서만)
        assert stats.avg_coordinate_change > 0
        
        # 실패 원인 분포 검증
        assert 'element_not_found' in stats.failure_reasons
        assert 'timeout' in stats.failure_reasons
        assert stats.failure_reasons['element_not_found'] == 1
        assert stats.failure_reasons['timeout'] == 1


class TestPhase4MultipleSessionsWorkflow:
    """Phase 4 여러 세션 실행 워크플로우 테스트
    
    Requirements: 13.1-13.6, 15.1, 15.2
    """
    
    @pytest.fixture
    def multi_session_env(self, tmp_path):
        """여러 세션 테스트 환경 설정"""
        data_dir = tmp_path / "accuracy_data"
        os.makedirs(data_dir, exist_ok=True)
        
        yield {
            "data_dir": str(data_dir),
            "tmp_path": tmp_path
        }
    
    def test_multiple_sessions_execution_and_history(self, multi_session_env):
        """여러 세션 실행 및 이력 조회 테스트 (Requirements 13.1, 15.1)"""
        data_dir = multi_session_env["data_dir"]
        test_case_name = "multi_session_test"
        
        # 3개의 세션 실행
        session_ids = []
        for session_num in range(3):
            tracker = AccuracyTracker(test_case_name, data_dir=data_dir)
            tracker.start_session()
            session_ids.append(tracker.get_session_id())
            
            # 각 세션마다 다른 결과 기록
            success_count = 5 + session_num  # 5, 6, 7
            failure_count = 2 - session_num if session_num < 2 else 0  # 2, 1, 0
            
            for i in range(success_count):
                tracker.record_success(
                    action_id=f"action_{i}",
                    method='direct' if i % 2 == 0 else 'semantic',
                    original_coords=(100 + i*10, 100 + i*10),
                    actual_coords=(100 + i*10 + (i % 2) * 50, 100 + i*10 + (i % 2) * 50),
                    execution_time=0.5
                )
            
            for i in range(failure_count):
                tracker.record_failure(
                    action_id=f"fail_{i}",
                    reason='element_not_found',
                    original_coords=(500 + i*10, 500 + i*10),
                    execution_time=1.0
                )
            
            tracker.save_session()
            time.sleep(0.02)  # 세션 ID 중복 방지
        
        # 세션 목록 조회
        tracker = AccuracyTracker(test_case_name, data_dir=data_dir)
        sessions = tracker.list_sessions()
        
        # 3개의 세션이 있어야 함
        assert len(sessions) == 3
        
        # 각 세션에 필요한 정보가 있어야 함
        for session in sessions:
            assert 'session_id' in session
            assert 'timestamp' in session
            assert 'total_actions' in session
            assert 'success_rate' in session
            assert 'success_count' in session
            assert 'failure_count' in session
            assert 'semantic_match_rate' in session

    def test_session_save_and_load_roundtrip(self, multi_session_env):
        """세션 저장 및 로드 라운드트립 테스트 (Requirements 13.1)"""
        data_dir = multi_session_env["data_dir"]
        test_case_name = "roundtrip_test"
        
        # 세션 생성 및 결과 기록
        tracker1 = AccuracyTracker(test_case_name, data_dir=data_dir)
        session_id = tracker1.get_session_id()
        
        tracker1.record_success(
            action_id="action_1",
            method='direct',
            original_coords=(100, 100),
            actual_coords=(100, 100),
            execution_time=0.5
        )
        tracker1.record_success(
            action_id="action_2",
            method='semantic',
            original_coords=(200, 200),
            actual_coords=(300, 300),
            execution_time=1.0
        )
        tracker1.record_failure(
            action_id="action_3",
            reason='timeout',
            original_coords=(400, 400),
            execution_time=2.0
        )
        
        # 세션 저장
        saved_path = tracker1.save_session()
        assert os.path.exists(saved_path)
        
        # 새 트래커로 세션 로드
        tracker2 = AccuracyTracker(test_case_name, data_dir=data_dir)
        load_success = tracker2.load_session(session_id)
        assert load_success
        
        # 결과 비교
        results1 = tracker1.get_results()
        results2 = tracker2.get_results()
        
        assert len(results1) == len(results2)
        
        for r1, r2 in zip(results1, results2):
            assert r1.action_id == r2.action_id
            assert r1.success == r2.success
            assert r1.method == r2.method
            assert r1.original_coords == r2.original_coords
            assert r1.failure_reason == r2.failure_reason
    
    def test_action_failure_rate_calculation(self, multi_session_env):
        """액션별 실패율 계산 테스트 (Requirements 13.2)"""
        data_dir = multi_session_env["data_dir"]
        test_case_name = "failure_rate_test"
        
        # 여러 세션에서 같은 액션 실행
        for session_num in range(5):
            tracker = AccuracyTracker(test_case_name, data_dir=data_dir)
            tracker.start_session()
            
            # action_1: 항상 성공 (실패율 0%)
            tracker.record_success(
                action_id="action_1",
                method='direct',
                original_coords=(100, 100),
                actual_coords=(100, 100),
                execution_time=0.5
            )
            
            # action_2: 50% 실패 (세션 0, 2, 4에서 성공, 1, 3에서 실패)
            if session_num % 2 == 0:
                tracker.record_success(
                    action_id="action_2",
                    method='semantic',
                    original_coords=(200, 200),
                    actual_coords=(250, 250),
                    execution_time=1.0
                )
            else:
                tracker.record_failure(
                    action_id="action_2",
                    reason='element_not_found',
                    original_coords=(200, 200),
                    execution_time=1.0
                )
            
            # action_3: 항상 실패 (실패율 100%)
            tracker.record_failure(
                action_id="action_3",
                reason='timeout',
                original_coords=(300, 300),
                execution_time=2.0
            )
            
            tracker.save_session()
            time.sleep(0.02)
        
        # 실패율 계산
        tracker = AccuracyTracker(test_case_name, data_dir=data_dir)
        failure_rates = tracker.get_failure_rate_by_action()
        
        # 실패율 검증
        assert failure_rates.get("action_1", 0.0) == 0.0  # 항상 성공
        assert abs(failure_rates.get("action_2", 0.0) - 0.4) < 0.01  # 2/5 실패
        assert failure_rates.get("action_3", 0.0) == 1.0  # 항상 실패


class TestPhase4ControllerIntegration:
    """Phase 4 컨트롤러 통합 테스트
    
    Requirements: 15.1, 15.2
    """
    
    @pytest.fixture
    def controller_env(self, tmp_path):
        """컨트롤러 테스트 환경 설정"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # 설정 파일 생성
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0"
            },
            "game": {
                "exe_path": "notepad.exe",
                "startup_wait": 0.1
            },
            "automation": {
                "action_delay": 0.01,
                "screenshot_dir": str(tmp_path / "screenshots"),
                "screenshot_on_action": False
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
        os.makedirs(tmp_path / "accuracy_data", exist_ok=True)
        
        yield {
            "config_path": str(config_path),
            "tmp_path": tmp_path
        }
        
        os.chdir(original_cwd)
    
    def test_controller_get_execution_history(self, controller_env):
        """컨트롤러 실행 이력 조회 테스트 (Requirements 15.1)"""
        tmp_path = controller_env["tmp_path"]
        
        # 테스트 데이터 생성
        test_case_name = "history_test"
        data_dir = tmp_path / "accuracy_data"
        os.makedirs(data_dir, exist_ok=True)
        
        # 세션 데이터 생성
        for i in range(3):
            tracker = AccuracyTracker(test_case_name, data_dir=str(data_dir))
            tracker.start_session()
            
            for j in range(5):
                if j < 4:
                    tracker.record_success(
                        action_id=f"action_{j}",
                        method='direct' if j % 2 == 0 else 'semantic',
                        original_coords=(100, 100),
                        actual_coords=(100 + j*10, 100 + j*10),
                        execution_time=0.5
                    )
                else:
                    tracker.record_failure(
                        action_id=f"action_{j}",
                        reason='element_not_found',
                        original_coords=(100, 100),
                        execution_time=1.0
                    )
            
            tracker.save_session()
            time.sleep(0.02)
        
        # 컨트롤러로 이력 조회
        controller = QAAutomationController(controller_env["config_path"])
        controller.initialize()
        
        # 테스트 케이스 로드 (current_test_case 설정)
        controller.current_test_case = {"name": test_case_name}
        
        # 이력 조회
        history = controller.get_execution_history(test_case_name)
        
        assert len(history) == 3
        for session in history:
            assert 'session_id' in session
            assert 'timestamp' in session
            assert 'success_rate' in session

    def test_controller_get_execution_statistics(self, controller_env):
        """컨트롤러 실행 통계 조회 테스트 (Requirements 15.2)"""
        tmp_path = controller_env["tmp_path"]
        
        # 테스트 데이터 생성
        test_case_name = "stats_test"
        data_dir = tmp_path / "accuracy_data"
        os.makedirs(data_dir, exist_ok=True)
        
        # 세션 데이터 생성 (다양한 성공률)
        success_rates = [0.8, 0.9, 0.7]  # 평균 0.8
        
        for i, target_rate in enumerate(success_rates):
            tracker = AccuracyTracker(test_case_name, data_dir=str(data_dir))
            tracker.start_session()
            
            total_actions = 10
            success_count = int(total_actions * target_rate)
            
            for j in range(success_count):
                tracker.record_success(
                    action_id=f"action_{j}",
                    method='direct' if j % 2 == 0 else 'semantic',
                    original_coords=(100, 100),
                    actual_coords=(100, 100),
                    execution_time=0.5
                )
            
            for j in range(total_actions - success_count):
                tracker.record_failure(
                    action_id=f"fail_{j}",
                    reason='element_not_found',
                    original_coords=(100, 100),
                    execution_time=1.0
                )
            
            tracker.save_session()
            time.sleep(0.02)
        
        # 컨트롤러로 통계 조회
        controller = QAAutomationController(controller_env["config_path"])
        controller.initialize()
        controller.current_test_case = {"name": test_case_name}
        
        stats = controller.get_execution_statistics(test_case_name)
        
        # 통계 검증
        assert stats['test_case_name'] == test_case_name
        assert stats['total_executions'] == 3
        assert stats['total_errors'] > 0
        assert 0.0 <= stats['avg_success_rate'] <= 1.0
        assert stats['latest_execution'] is not None


class TestPhase4CLIStatsCommand:
    """Phase 4 CLI stats 명령어 테스트
    
    Requirements: 15.1, 15.2
    """
    
    @pytest.fixture
    def cli_env(self, tmp_path):
        """CLI 테스트 환경 설정"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # 디렉토리 생성
        os.makedirs(tmp_path / "accuracy_data", exist_ok=True)
        
        yield {
            "tmp_path": tmp_path
        }
        
        os.chdir(original_cwd)
    
    def test_stats_command_with_history(self, cli_env, capsys):
        """stats 명령어 실행 이력 표시 테스트 (Requirements 15.1)"""
        tmp_path = cli_env["tmp_path"]
        test_case_name = "cli_stats_test"
        
        # 테스트 데이터 생성
        data_dir = tmp_path / "accuracy_data"
        
        for i in range(2):
            tracker = AccuracyTracker(test_case_name, data_dir=str(data_dir))
            tracker.start_session()
            
            tracker.record_success(
                action_id="action_1",
                method='direct',
                original_coords=(100, 100),
                actual_coords=(100, 100),
                execution_time=0.5
            )
            tracker.record_success(
                action_id="action_2",
                method='semantic',
                original_coords=(200, 200),
                actual_coords=(250, 250),
                execution_time=1.0
            )
            
            tracker.save_session()
            time.sleep(0.02)
        
        # Mock 컨트롤러 생성
        mock_controller = Mock()
        mock_controller.current_test_case = {"name": test_case_name}
        
        # 실제 AccuracyTracker 사용
        def mock_get_history(name=None):
            tracker = AccuracyTracker(name or test_case_name, data_dir=str(data_dir))
            return tracker.list_sessions()
        
        def mock_get_stats(name=None):
            sessions = mock_get_history(name)
            if not sessions:
                return {
                    "test_case_name": name or test_case_name,
                    "total_executions": 0,
                    "avg_success_rate": 0.0,
                    "total_errors": 0,
                    "avg_semantic_match_rate": 0.0,
                    "latest_execution": None
                }
            
            total = len(sessions)
            return {
                "test_case_name": name or test_case_name,
                "total_executions": total,
                "avg_success_rate": sum(s.get("success_rate", 0) for s in sessions) / total,
                "total_errors": sum(s.get("failure_count", 0) for s in sessions),
                "avg_semantic_match_rate": sum(s.get("semantic_match_rate", 0) for s in sessions) / total,
                "latest_execution": sessions[0] if sessions else None
            }
        
        mock_controller.get_execution_history = mock_get_history
        mock_controller.get_execution_statistics = mock_get_stats
        
        # CLI 인터페이스 생성 및 stats 명령 실행
        cli = CLIInterface(mock_controller)
        cli._handle_stats([test_case_name])
        
        # 출력 확인
        captured = capsys.readouterr()
        assert test_case_name in captured.out
        assert "실행 이력" in captured.out or "통계" in captured.out

    def test_stats_command_no_history(self, cli_env, capsys):
        """stats 명령어 이력 없음 처리 테스트"""
        tmp_path = cli_env["tmp_path"]
        test_case_name = "empty_stats_test"
        
        # Mock 컨트롤러 생성
        mock_controller = Mock()
        mock_controller.current_test_case = {"name": test_case_name}
        mock_controller.get_execution_history = Mock(return_value=[])
        mock_controller.get_execution_statistics = Mock(return_value={
            "test_case_name": test_case_name,
            "total_executions": 0,
            "avg_success_rate": 0.0,
            "total_errors": 0,
            "avg_semantic_match_rate": 0.0,
            "latest_execution": None
        })
        
        # CLI 인터페이스 생성 및 stats 명령 실행
        cli = CLIInterface(mock_controller)
        cli._handle_stats([test_case_name])
        
        # 출력 확인
        captured = capsys.readouterr()
        assert "이력이 없습니다" in captured.out or "0" in captured.out


class TestPhase4FullWorkflow:
    """Phase 4 전체 워크플로우 통합 테스트
    
    Requirements: 13.1-13.6, 15.1, 15.2
    """
    
    @pytest.fixture
    def workflow_env(self, tmp_path):
        """전체 워크플로우 테스트 환경 설정"""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        # 디렉토리 생성
        os.makedirs(tmp_path / "accuracy_data", exist_ok=True)
        os.makedirs(tmp_path / "test_cases", exist_ok=True)
        
        yield {
            "tmp_path": tmp_path
        }
        
        os.chdir(original_cwd)
    
    def test_full_accuracy_tracking_workflow(self, workflow_env):
        """전체 정확도 추적 워크플로우 테스트"""
        tmp_path = workflow_env["tmp_path"]
        test_case_name = "full_workflow_test"
        data_dir = tmp_path / "accuracy_data"
        
        # 1. 첫 번째 세션: 높은 성공률
        tracker1 = AccuracyTracker(test_case_name, data_dir=str(data_dir))
        session1_id = tracker1.start_session()
        
        for i in range(8):
            tracker1.record_success(
                action_id=f"action_{i}",
                method='direct' if i < 6 else 'semantic',
                original_coords=(100 + i*10, 100 + i*10),
                actual_coords=(100 + i*10, 100 + i*10) if i < 6 else (150 + i*10, 150 + i*10),
                execution_time=0.5,
                screen_transition_matched=True
            )
        
        for i in range(2):
            tracker1.record_failure(
                action_id=f"fail_{i}",
                reason='element_not_found',
                original_coords=(500 + i*10, 500 + i*10),
                execution_time=1.0
            )
        
        tracker1.save_session()
        
        # 2. 두 번째 세션: 낮은 성공률
        time.sleep(0.02)
        tracker2 = AccuracyTracker(test_case_name, data_dir=str(data_dir))
        session2_id = tracker2.start_session()
        
        for i in range(5):
            tracker2.record_success(
                action_id=f"action_{i}",
                method='semantic',
                original_coords=(100 + i*10, 100 + i*10),
                actual_coords=(200 + i*10, 200 + i*10),
                execution_time=1.0,
                screen_transition_matched=i < 3
            )
        
        for i in range(5):
            tracker2.record_failure(
                action_id=f"fail_{i}",
                reason='timeout' if i % 2 == 0 else 'element_not_found',
                original_coords=(500 + i*10, 500 + i*10),
                execution_time=2.0
            )
        
        tracker2.save_session()
        
        # 3. 세션 목록 조회
        tracker = AccuracyTracker(test_case_name, data_dir=str(data_dir))
        sessions = tracker.list_sessions()
        
        assert len(sessions) == 2
        
        # 4. 각 세션의 통계 검증
        # 첫 번째 세션: 80% 성공률
        session1_stats = next((s for s in sessions if s['session_id'] == session1_id), None)
        assert session1_stats is not None
        assert abs(session1_stats['success_rate'] - 0.8) < 0.01
        
        # 두 번째 세션: 50% 성공률
        session2_stats = next((s for s in sessions if s['session_id'] == session2_id), None)
        assert session2_stats is not None
        assert abs(session2_stats['success_rate'] - 0.5) < 0.01
        
        # 5. 액션별 실패율 조회
        failure_rates = tracker.get_failure_rate_by_action()
        
        # fail_0, fail_1 등은 항상 실패
        for key in failure_rates:
            if key.startswith('fail_'):
                assert failure_rates[key] == 1.0
        
        # 6. 특정 액션의 이력 조회
        action_history = tracker.get_action_history("action_0")
        assert len(action_history) == 2  # 두 세션에서 각각 실행됨

    def test_statistics_completeness_validation(self, workflow_env):
        """통계 완전성 검증 테스트 (Requirements 13.6)"""
        tmp_path = workflow_env["tmp_path"]
        test_case_name = "completeness_test"
        data_dir = tmp_path / "accuracy_data"
        
        tracker = AccuracyTracker(test_case_name, data_dir=str(data_dir))
        
        # 다양한 시나리오의 결과 기록
        # 직접 매칭 성공
        tracker.record_success(
            action_id="direct_success",
            method='direct',
            original_coords=(100, 100),
            actual_coords=(100, 100),
            execution_time=0.3,
            screen_transition_matched=True
        )
        
        # 의미론적 매칭 성공 (좌표 변경)
        tracker.record_success(
            action_id="semantic_success",
            method='semantic',
            original_coords=(200, 200),
            actual_coords=(350, 400),
            execution_time=1.5,
            screen_transition_matched=True
        )
        
        # 수동 매칭 성공
        tracker.record_success(
            action_id="manual_success",
            method='manual',
            original_coords=(300, 300),
            actual_coords=(320, 320),
            execution_time=5.0,
            screen_transition_matched=False
        )
        
        # 실패
        tracker.record_failure(
            action_id="failure",
            reason='element_not_found',
            original_coords=(400, 400),
            execution_time=2.0
        )
        
        # 통계 계산
        stats = tracker.calculate_statistics()
        
        # 필수 필드 검증 (Requirements 13.6)
        assert hasattr(stats, 'total_actions')
        assert hasattr(stats, 'success_count')
        assert hasattr(stats, 'failure_count')
        assert hasattr(stats, 'success_rate')
        assert hasattr(stats, 'direct_match_count')
        assert hasattr(stats, 'semantic_match_count')
        assert hasattr(stats, 'manual_match_count')
        assert hasattr(stats, 'direct_match_rate')
        assert hasattr(stats, 'semantic_match_rate')
        assert hasattr(stats, 'avg_coordinate_change')
        assert hasattr(stats, 'avg_execution_time')
        assert hasattr(stats, 'failure_reasons')
        assert hasattr(stats, 'transition_match_count')
        assert hasattr(stats, 'transition_mismatch_count')
        
        # 값 검증
        assert stats.total_actions == 4
        assert stats.success_count == 3
        assert stats.failure_count == 1
        assert abs(stats.success_rate - 0.75) < 0.01
        
        assert stats.direct_match_count == 1
        assert stats.semantic_match_count == 1
        assert stats.manual_match_count == 1
        
        # 평균 좌표 변경 거리 (의미론적 + 수동 매칭에서 계산)
        assert stats.avg_coordinate_change > 0
        
        # 평균 실행 시간
        assert stats.avg_execution_time > 0
        
        # 실패 원인
        assert 'element_not_found' in stats.failure_reasons
        
        # 화면 전환 일치/불일치
        assert stats.transition_match_count == 2  # direct, semantic
        assert stats.transition_mismatch_count == 2  # manual, failure


class TestPhase4EdgeCases:
    """Phase 4 엣지 케이스 테스트"""
    
    @pytest.fixture
    def edge_env(self, tmp_path):
        """엣지 케이스 테스트 환경 설정"""
        data_dir = tmp_path / "accuracy_data"
        os.makedirs(data_dir, exist_ok=True)
        
        yield {
            "data_dir": str(data_dir),
            "tmp_path": tmp_path
        }
    
    def test_empty_tracker_statistics(self, edge_env):
        """빈 트래커 통계 테스트"""
        data_dir = edge_env["data_dir"]
        
        tracker = AccuracyTracker("empty_test", data_dir=data_dir)
        stats = tracker.calculate_statistics()
        
        assert stats.total_actions == 0
        assert stats.success_count == 0
        assert stats.failure_count == 0
        assert stats.success_rate == 0.0
        assert stats.avg_coordinate_change == 0.0
    
    def test_all_success_statistics(self, edge_env):
        """모두 성공 통계 테스트"""
        data_dir = edge_env["data_dir"]
        
        tracker = AccuracyTracker("all_success_test", data_dir=data_dir)
        
        for i in range(10):
            tracker.record_success(
                action_id=f"action_{i}",
                method='direct',
                original_coords=(100, 100),
                actual_coords=(100, 100),
                execution_time=0.5
            )
        
        stats = tracker.calculate_statistics()
        
        assert stats.success_rate == 1.0
        assert stats.failure_count == 0
        assert len(stats.failure_reasons) == 0
    
    def test_all_failure_statistics(self, edge_env):
        """모두 실패 통계 테스트"""
        data_dir = edge_env["data_dir"]
        
        tracker = AccuracyTracker("all_failure_test", data_dir=data_dir)
        
        for i in range(10):
            tracker.record_failure(
                action_id=f"action_{i}",
                reason='element_not_found',
                original_coords=(100, 100),
                execution_time=1.0
            )
        
        stats = tracker.calculate_statistics()
        
        assert stats.success_rate == 0.0
        assert stats.success_count == 0
        assert stats.direct_match_rate == 0.0
        assert stats.semantic_match_rate == 0.0
    
    def test_load_nonexistent_session(self, edge_env):
        """존재하지 않는 세션 로드 테스트"""
        data_dir = edge_env["data_dir"]
        
        tracker = AccuracyTracker("nonexistent_test", data_dir=data_dir)
        result = tracker.load_session("nonexistent_session_id")
        
        assert result == False
    
    def test_clear_results(self, edge_env):
        """결과 초기화 테스트"""
        data_dir = edge_env["data_dir"]
        
        tracker = AccuracyTracker("clear_test", data_dir=data_dir)
        
        # 결과 기록
        tracker.record_success(
            action_id="action_1",
            method='direct',
            original_coords=(100, 100),
            actual_coords=(100, 100),
            execution_time=0.5
        )
        
        assert len(tracker.get_results()) == 1
        
        # 결과 초기화
        tracker.clear_results()
        
        assert len(tracker.get_results()) == 0
