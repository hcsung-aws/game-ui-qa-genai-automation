"""
GameProcessManager - 게임 프로세스 관리

Requirements: 1.1, 1.2
"""

import subprocess
import time
import os
from typing import Optional


class GameProcessManager:
    """게임 프로세스 관리"""
    
    def __init__(self, config):
        """
        Args:
            config: ConfigManager 인스턴스
        """
        self.config = config
        self.process: Optional[subprocess.Popen] = None
    
    def start_game(self) -> bool:
        """게임 실행
        
        Returns:
            성공 여부
            
        Raises:
            FileNotFoundError: 게임 실행 파일이 없을 때
            subprocess.SubprocessError: 프로세스 실행 실패 시
        """
        exe_path = self.config.get('game.exe_path')
        startup_wait = self.config.get('game.startup_wait', 5)
        
        if not exe_path:
            raise ValueError("게임 실행 파일 경로가 설정되지 않았습니다")
        
        if not os.path.exists(exe_path):
            raise FileNotFoundError(f"게임 실행 파일을 찾을 수 없습니다: {exe_path}")
        
        try:
            # 게임 프로세스 실행
            self.process = subprocess.Popen(
                [exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 시작 지연 시간 대기 (Requirements 1.2)
            print(f"게임 시작 중... {startup_wait}초 대기")
            time.sleep(startup_wait)
            
            # 프로세스가 정상적으로 실행 중인지 확인
            if self.process.poll() is not None:
                # 프로세스가 이미 종료됨
                raise subprocess.SubprocessError(
                    f"게임 프로세스가 시작 직후 종료되었습니다 (exit code: {self.process.returncode})"
                )
            
            print(f"✓ 게임 실행 완료 (PID: {self.process.pid})")
            return True
            
        except FileNotFoundError:
            raise
        except Exception as e:
            raise subprocess.SubprocessError(f"게임 실행 실패: {str(e)}")
    
    def is_game_running(self) -> bool:
        """게임 실행 중인지 확인
        
        Returns:
            실행 중이면 True
        """
        if self.process is None:
            return False
        
        # poll()이 None이면 프로세스가 아직 실행 중
        return self.process.poll() is None
    
    def stop_game(self) -> None:
        """게임 프로세스 종료"""
        if self.process is None:
            return
        
        if self.is_game_running():
            print("게임 프로세스 종료 중...")
            self.process.terminate()
            
            # 정상 종료를 위해 잠시 대기
            try:
                self.process.wait(timeout=5)
                print("✓ 게임 프로세스 정상 종료")
            except subprocess.TimeoutExpired:
                # 강제 종료
                print("⚠ 게임 프로세스 강제 종료")
                self.process.kill()
                self.process.wait()
        
        self.process = None
    
    def get_process_id(self) -> Optional[int]:
        """게임 프로세스 ID 반환
        
        Returns:
            프로세스 ID 또는 None
        """
        if self.process is None:
            return None
        return self.process.pid
