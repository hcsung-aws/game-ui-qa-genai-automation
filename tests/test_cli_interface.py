"""
CLIInterface 테스트

Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.9, 4.10, 4.11, 15.1, 15.2
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from io import StringIO
from src.cli_interface import CLIInterface


class TestCLIInterface:
    """CLIInterface 테스트"""
    
    @pytest.fixture
    def mock_controller(self):
        """Mock QAAutomationController 생성"""
        controller = Mock()
        controller.start_game = Mock(return_value=True)
        controller.start_recording = Mock()
        controller.stop_recording = Mock()
        controller.get_actions = Mock(return_value=[])
        controller.save_test_case = Mock()
        controller.load_test_case = Mock()
        controller.replay_test_case = Mock()
        controller.list_test_cases = Mock(return_value=[])
        controller.current_test_case = None
        controller.get_execution_history = Mock(return_value=[])
        controller.get_execution_statistics = Mock(return_value={
            "test_case_name": "test",
            "total_executions": 0,
            "avg_success_rate": 0.0,
            "total_errors": 0,
            "avg_semantic_match_rate": 0.0,
            "latest_execution": None
        })
        return controller
    
    @pytest.fixture
    def cli(self, mock_controller):
        """CLIInterface 인스턴스 생성"""
        return CLIInterface(mock_controller)
    
    def test_init(self, mock_controller):
        """초기화 테스트"""
        cli = CLIInterface(mock_controller)
        assert cli.controller == mock_controller
    
    # ===== 명령어 처리 테스트 (Requirements 4.2, 4.3, 4.4, 4.6, 4.9, 4.10) =====
    
    def test_handle_command_start(self, cli, mock_controller):
        """start 명령어 처리 (Requirements 4.2)"""
        result = cli.handle_command(['start'])
        
        assert result is True
        mock_controller.start_game.assert_called_once()
    
    def test_handle_command_record(self, cli, mock_controller):
        """record 명령어 처리 (Requirements 4.3)"""
        result = cli.handle_command(['record'])
        
        assert result is True
        mock_controller.start_recording.assert_called_once()
    
    def test_handle_command_stop(self, cli, mock_controller):
        """stop 명령어 처리 (Requirements 4.4)"""
        mock_controller.get_actions.return_value = [Mock(), Mock(), Mock()]
        
        result = cli.handle_command(['stop'])
        
        assert result is True
        mock_controller.stop_recording.assert_called_once()
    
    def test_handle_command_save_with_name(self, cli, mock_controller):
        """save 명령어 처리 - 이름 제공 (Requirements 4.6)"""
        result = cli.handle_command(['save', 'test_case_1'])
        
        assert result is True
        mock_controller.save_test_case.assert_called_once_with('test_case_1')
    
    def test_handle_command_save_without_name(self, cli, mock_controller, capsys):
        """save 명령어 처리 - 이름 미제공"""
        result = cli.handle_command(['save'])
        
        assert result is True
        mock_controller.save_test_case.assert_not_called()
        
        captured = capsys.readouterr()
        assert '사용법' in captured.out or 'save' in captured.out
    
    def test_handle_command_replay(self, cli, mock_controller):
        """replay 명령어 처리 (Requirements 4.9)"""
        result = cli.handle_command(['replay'])
        
        assert result is True
        mock_controller.replay_test_case.assert_called_once()
    
    def test_handle_command_quit(self, cli, mock_controller):
        """quit 명령어 처리 (Requirements 4.10)"""
        result = cli.handle_command(['quit'])
        
        assert result is False  # 세션 종료
    
    # ===== 유효하지 않은 명령 처리 테스트 (Requirements 4.11) =====
    
    def test_handle_command_invalid(self, cli, mock_controller, capsys):
        """유효하지 않은 명령어 처리 (Requirements 4.11)"""
        result = cli.handle_command(['invalid_command'])
        
        assert result is True  # 세션은 계속
        
        captured = capsys.readouterr()
        # 오류 메시지와 사용 가능한 명령어 표시
        assert '알 수 없는 명령어' in captured.out or 'invalid_command' in captured.out
    
    def test_handle_command_empty(self, cli, mock_controller):
        """빈 명령어 처리"""
        result = cli.handle_command([])
        
        assert result is True  # 세션은 계속
    
    # ===== 도움말 표시 테스트 (Requirements 4.1) =====
    
    def test_display_help(self, cli, capsys):
        """도움말 표시 테스트 (Requirements 4.1)"""
        cli.display_help()
        
        captured = capsys.readouterr()
        
        # 필수 명령어들이 도움말에 포함되어야 함
        assert 'start' in captured.out
        assert 'record' in captured.out
        assert 'stop' in captured.out
        assert 'save' in captured.out
        assert 'replay' in captured.out
        assert 'quit' in captured.out
    
    def test_handle_command_help(self, cli, mock_controller, capsys):
        """help 명령어 처리"""
        result = cli.handle_command(['help'])
        
        assert result is True
        
        captured = capsys.readouterr()
        # 도움말이 표시되어야 함
        assert 'start' in captured.out or '명령어' in captured.out
    
    # ===== 명령어 대소문자 처리 테스트 =====
    
    def test_handle_command_case_insensitive(self, cli, mock_controller):
        """명령어 대소문자 무시 테스트"""
        result = cli.handle_command(['START'])
        
        assert result is True
        mock_controller.start_game.assert_called_once()
    
    def test_handle_command_mixed_case(self, cli, mock_controller):
        """명령어 혼합 대소문자 테스트"""
        result = cli.handle_command(['Record'])
        
        assert result is True
        mock_controller.start_recording.assert_called_once()
    
    # ===== 에러 처리 테스트 =====
    
    def test_handle_command_start_error(self, cli, mock_controller, capsys):
        """start 명령어 에러 처리"""
        mock_controller.start_game.side_effect = FileNotFoundError("게임 파일 없음")
        
        result = cli.handle_command(['start'])
        
        assert result is True  # 세션은 계속
        
        captured = capsys.readouterr()
        assert '오류' in captured.out or '실패' in captured.out or '에러' in captured.out or '게임' in captured.out
    
    def test_handle_command_replay_no_test_case(self, cli, mock_controller, capsys):
        """replay 명령어 - 로드된 테스트 케이스 없음"""
        mock_controller.replay_test_case.side_effect = ValueError("로드된 테스트 케이스가 없습니다")
        
        result = cli.handle_command(['replay'])
        
        assert result is True  # 세션은 계속
        
        captured = capsys.readouterr()
        assert '테스트 케이스' in captured.out or '로드' in captured.out or '오류' in captured.out
    
    # ===== stats 명령어 테스트 (Requirements 15.1, 15.2) =====
    
    def test_handle_command_stats_with_name(self, cli, mock_controller, capsys):
        """stats 명령어 처리 - 테스트 케이스 이름 제공 (Requirements 15.1)"""
        mock_controller.get_execution_history.return_value = [
            {
                "session_id": "20251223_100000",
                "timestamp": "2025-12-23T10:00:00",
                "total_actions": 10,
                "success_rate": 0.9,
                "success_count": 9,
                "failure_count": 1,
                "semantic_match_rate": 0.2
            }
        ]
        mock_controller.get_execution_statistics.return_value = {
            "test_case_name": "my_test",
            "total_executions": 1,
            "avg_success_rate": 0.9,
            "total_errors": 1,
            "avg_semantic_match_rate": 0.2,
            "latest_execution": {
                "timestamp": "2025-12-23T10:00:00",
                "success_rate": 0.9,
                "success_count": 9,
                "failure_count": 1
            }
        }
        
        result = cli.handle_command(['stats', 'my_test'])
        
        assert result is True
        mock_controller.get_execution_history.assert_called_once_with('my_test')
        
        captured = capsys.readouterr()
        # 실행 이력 표시 확인
        assert '실행 이력' in captured.out or '통계' in captured.out
    
    def test_handle_command_stats_without_name(self, cli, mock_controller, capsys):
        """stats 명령어 처리 - 테스트 케이스 이름 미제공 (현재 로드된 테스트 케이스 사용)"""
        mock_controller.current_test_case = {"name": "loaded_test"}
        mock_controller.get_execution_history.return_value = []
        
        result = cli.handle_command(['stats'])
        
        assert result is True
        mock_controller.get_execution_history.assert_called_once_with(None)
    
    def test_handle_command_stats_no_history(self, cli, mock_controller, capsys):
        """stats 명령어 처리 - 실행 이력 없음"""
        mock_controller.current_test_case = {"name": "empty_test"}
        mock_controller.get_execution_history.return_value = []
        
        result = cli.handle_command(['stats'])
        
        assert result is True
        
        captured = capsys.readouterr()
        assert '실행 이력이 없습니다' in captured.out or '이력' in captured.out
    
    def test_handle_command_stats_with_history(self, cli, mock_controller, capsys):
        """stats 명령어 처리 - 실행 이력 있음 (Requirements 15.2)"""
        mock_controller.current_test_case = {"name": "test_with_history"}
        mock_controller.get_execution_history.return_value = [
            {
                "session_id": "20251223_100000",
                "timestamp": "2025-12-23T10:00:00",
                "total_actions": 10,
                "success_rate": 0.9,
                "success_count": 9,
                "failure_count": 1,
                "semantic_match_rate": 0.2
            },
            {
                "session_id": "20251222_150000",
                "timestamp": "2025-12-22T15:00:00",
                "total_actions": 10,
                "success_rate": 0.8,
                "success_count": 8,
                "failure_count": 2,
                "semantic_match_rate": 0.3
            }
        ]
        mock_controller.get_execution_statistics.return_value = {
            "test_case_name": "test_with_history",
            "total_executions": 2,
            "avg_success_rate": 0.85,
            "total_errors": 3,
            "avg_semantic_match_rate": 0.25,
            "latest_execution": {
                "timestamp": "2025-12-23T10:00:00",
                "success_rate": 0.9,
                "success_count": 9,
                "failure_count": 1
            }
        }
        
        result = cli.handle_command(['stats'])
        
        assert result is True
        
        captured = capsys.readouterr()
        # Requirements 15.2: 날짜, 성공률, 오류 수, 의미론적 매칭 사용률 포함 확인
        assert '성공률' in captured.out or '90' in captured.out or '85' in captured.out
        assert '오류' in captured.out or '실패' in captured.out
        assert '의미론적' in captured.out or 'semantic' in captured.out.lower()
    
    def test_handle_command_stats_error(self, cli, mock_controller, capsys):
        """stats 명령어 처리 - 에러 발생"""
        mock_controller.get_execution_history.side_effect = ValueError("테스트 케이스가 지정되지 않았습니다")
        
        result = cli.handle_command(['stats'])
        
        assert result is True  # 세션은 계속
        
        captured = capsys.readouterr()
        assert '오류' in captured.out or '사용법' in captured.out
    
    def test_display_help_includes_stats(self, cli, capsys):
        """도움말에 stats 명령어 포함 확인"""
        cli.display_help()
        
        captured = capsys.readouterr()
        assert 'stats' in captured.out

