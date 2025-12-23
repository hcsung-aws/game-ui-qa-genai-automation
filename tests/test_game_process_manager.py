"""
GameProcessManager 테스트

Requirements: 1.1, 9.1
"""

import pytest
import subprocess
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from src.game_process_manager import GameProcessManager
from src.config_manager import ConfigManager


class TestGameProcessManager:
    """GameProcessManager 테스트"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager 생성"""
        config = Mock(spec=ConfigManager)
        config.get = Mock(side_effect=lambda key, default=None: {
            'game.exe_path': 'C:/fake/game.exe',
            'game.startup_wait': 0.1  # 테스트 속도를 위해 짧게 설정
        }.get(key, default))
        return config
    
    @pytest.fixture
    def manager(self, mock_config):
        """GameProcessManager 인스턴스 생성"""
        return GameProcessManager(mock_config)
    
    def test_init(self, mock_config):
        """초기화 테스트"""
        manager = GameProcessManager(mock_config)
        assert manager.config == mock_config
        assert manager.process is None
    
    def test_start_game_success(self, manager, mock_config):
        """게임 실행 성공 케이스 (Requirements 1.1)"""
        # 실제 실행 가능한 프로그램으로 테스트 (Python 인터프리터 사용)
        import sys
        python_exe = sys.executable
        
        # 설정을 실제 Python 실행 파일로 변경
        mock_config.get = Mock(side_effect=lambda key, default=None: {
            'game.exe_path': python_exe,
            'game.startup_wait': 0.1
        }.get(key, default))
        
        # 간단한 Python 스크립트를 임시 파일로 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('import time; time.sleep(10)')  # 10초 동안 실행
            temp_script = f.name
        
        try:
            # 설정을 Python 스크립트 실행으로 변경
            mock_config.get = Mock(side_effect=lambda key, default=None: {
                'game.exe_path': python_exe,
                'game.startup_wait': 0.1
            }.get(key, default))
            
            # subprocess.Popen을 mock하여 실제 프로세스 시작
            with patch('subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_process.poll.return_value = None  # 실행 중
                mock_process.pid = 12345
                mock_popen.return_value = mock_process
                
                result = manager.start_game()
                
                assert result is True
                assert manager.process is not None
                assert manager.process.pid == 12345
                
                # Popen이 올바른 인자로 호출되었는지 확인
                mock_popen.assert_called_once()
                call_args = mock_popen.call_args
                assert call_args[0][0] == [python_exe]
        finally:
            # 임시 파일 정리
            if os.path.exists(temp_script):
                os.unlink(temp_script)
    
    def test_start_game_file_not_found(self, manager, mock_config):
        """실행 파일 없음 에러 처리 (Requirements 9.1)"""
        # 존재하지 않는 파일 경로 설정
        mock_config.get = Mock(side_effect=lambda key, default=None: {
            'game.exe_path': 'C:/nonexistent/game.exe',
            'game.startup_wait': 0.1
        }.get(key, default))
        
        # FileNotFoundError가 발생해야 함
        with pytest.raises(FileNotFoundError) as exc_info:
            manager.start_game()
        
        assert '게임 실행 파일을 찾을 수 없습니다' in str(exc_info.value)
        assert 'C:/nonexistent/game.exe' in str(exc_info.value)
    
    def test_start_game_no_exe_path_configured(self, manager, mock_config):
        """실행 파일 경로가 설정되지 않은 경우"""
        mock_config.get = Mock(side_effect=lambda key, default=None: {
            'game.exe_path': None,
            'game.startup_wait': 0.1
        }.get(key, default))
        
        with pytest.raises(ValueError) as exc_info:
            manager.start_game()
        
        assert '게임 실행 파일 경로가 설정되지 않았습니다' in str(exc_info.value)
    
    def test_start_game_process_exits_immediately(self, manager, mock_config):
        """프로세스가 시작 직후 종료되는 경우"""
        import sys
        python_exe = sys.executable
        
        mock_config.get = Mock(side_effect=lambda key, default=None: {
            'game.exe_path': python_exe,
            'game.startup_wait': 0.1
        }.get(key, default))
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.poll.return_value = 1  # 이미 종료됨
            mock_process.returncode = 1
            mock_popen.return_value = mock_process
            
            with pytest.raises(subprocess.SubprocessError) as exc_info:
                manager.start_game()
            
            assert '게임 프로세스가 시작 직후 종료되었습니다' in str(exc_info.value)
    
    def test_is_game_running_no_process(self, manager):
        """프로세스가 없을 때 is_game_running"""
        assert manager.is_game_running() is False
    
    def test_is_game_running_process_running(self, manager):
        """프로세스가 실행 중일 때 is_game_running"""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # 실행 중
        manager.process = mock_process
        
        assert manager.is_game_running() is True
    
    def test_is_game_running_process_stopped(self, manager):
        """프로세스가 종료되었을 때 is_game_running"""
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # 종료됨
        manager.process = mock_process
        
        assert manager.is_game_running() is False
    
    def test_stop_game_no_process(self, manager):
        """프로세스가 없을 때 stop_game"""
        # 예외가 발생하지 않아야 함
        manager.stop_game()
        assert manager.process is None
    
    def test_stop_game_running_process(self, manager):
        """실행 중인 프로세스 종료"""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # 실행 중
        mock_process.wait = MagicMock()
        manager.process = mock_process
        
        manager.stop_game()
        
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert manager.process is None
    
    def test_stop_game_timeout_force_kill(self, manager):
        """종료 타임아웃 시 강제 종료"""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # 실행 중
        mock_process.wait.side_effect = [subprocess.TimeoutExpired('cmd', 5), None]
        manager.process = mock_process
        
        manager.stop_game()
        
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        assert manager.process is None
    
    def test_get_process_id_no_process(self, manager):
        """프로세스가 없을 때 get_process_id"""
        assert manager.get_process_id() is None
    
    def test_get_process_id_with_process(self, manager):
        """프로세스가 있을 때 get_process_id"""
        mock_process = MagicMock()
        mock_process.pid = 12345
        manager.process = mock_process
        
        assert manager.get_process_id() == 12345
