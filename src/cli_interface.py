"""
CLIInterface - 커맨드라인 인터페이스

사용자와 상호작용하는 CLI 인터페이스를 제공한다.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.9, 4.10, 4.11, 15.1, 15.2
"""

from typing import List, Optional


class CLIInterface:
    """CLI 인터페이스
    
    사용자가 명령어를 입력하여 게임 QA 자동화 시스템을 제어할 수 있게 한다.
    """
    
    def __init__(self, controller):
        """
        Args:
            controller: QAAutomationController 인스턴스
        """
        self.controller = controller
    
    def start_interactive_session(self):
        """대화형 세션 시작 (Requirements 4.1)
        
        사용 가능한 명령어를 표시하고 사용자 입력을 대기한다.
        """
        print("=" * 50)
        print("       게임 QA 자동화 시스템")
        print("=" * 50)
        self.display_help()
        print()
        
        while True:
            try:
                user_input = input("\n> ").strip()
                if not user_input:
                    continue
                
                cmd = user_input.split()
                if not self.handle_command(cmd):
                    break
                    
            except KeyboardInterrupt:
                print("\n\n✓ 사용자에 의해 종료되었습니다.")
                break
            except EOFError:
                print("\n\n✓ 세션이 종료되었습니다.")
                break
    
    def display_help(self):
        """도움말 표시 (Requirements 4.1)
        
        사용 가능한 명령어 목록을 표시한다.
        """
        help_text = """
사용 가능한 명령어:
  start              - 게임 실행
  record             - 입력 기록 시작 (사용자가 직접 게임 플레이)
  stop               - 입력 기록 중지
  save <name>        - 기록된 액션을 테스트 케이스로 저장
  replay             - 로드된 테스트 케이스 재실행
  stats [name]       - 테스트 케이스 실행 이력 및 통계 표시
  help               - 도움말 표시
  quit               - 종료
"""
        print(help_text)
    
    def handle_command(self, command: List[str]) -> bool:
        """명령어 처리
        
        Args:
            command: 사용자 입력 명령어 (리스트)
            
        Returns:
            계속 실행 여부 (False면 종료)
        """
        if not command:
            return True
        
        cmd = command[0].lower()
        args = command[1:] if len(command) > 1 else []
        
        # 명령어별 처리
        if cmd == "start":
            self._handle_start()
        elif cmd == "record":
            self._handle_record()
        elif cmd == "stop":
            self._handle_stop()
        elif cmd == "save":
            self._handle_save(args)
        elif cmd == "replay":
            self._handle_replay()
        elif cmd == "stats":
            self._handle_stats(args)
        elif cmd == "help":
            self.display_help()
        elif cmd == "quit" or cmd == "exit":
            print("✓ 게임 QA 자동화 시스템을 종료합니다.")
            return False
        else:
            print(f"❌ 알 수 없는 명령어: {cmd}")
            print("'help' 명령어로 사용 가능한 명령어를 확인하세요.")
        
        return True
    
    def _handle_start(self):
        """start 명령어 처리 (Requirements 4.2)
        
        게임 프로세스를 실행한다.
        """
        try:
            print("게임을 시작합니다...")
            result = self.controller.start_game()
            if result:
                print("✓ 게임이 성공적으로 시작되었습니다.")
            else:
                print("❌ 게임 시작에 실패했습니다.")
        except FileNotFoundError as e:
            print(f"❌ 오류: {e}")
            print("config.json에서 game.exe_path 설정을 확인하세요.")
        except Exception as e:
            print(f"❌ 게임 시작 중 오류 발생: {e}")
    
    def _handle_record(self):
        """record 명령어 처리 (Requirements 4.3)
        
        입력 모니터링을 시작한다.
        5초 대기 후 기록을 시작하여 사용자가 게임 창을 활성화할 시간을 준다.
        """
        import time
        try:
            print("✓ 5초 후 입력 기록을 시작합니다. 게임 창을 활성화하세요...")
            for i in range(5, 0, -1):
                print(f"  {i}...")
                time.sleep(1)
            
            self.controller.start_recording()
            print("✓ 입력 기록을 시작합니다!")
            print("  게임을 플레이하세요. 모든 마우스/키보드 입력이 기록됩니다.")
            print("  'stop' 명령으로 기록을 중지하세요.")
        except Exception as e:
            print(f"❌ 기록 시작 중 오류 발생: {e}")
    
    def _handle_stop(self):
        """stop 명령어 처리 (Requirements 4.4)
        
        입력 모니터링을 중지하고 기록된 액션 수를 표시한다.
        """
        try:
            self.controller.stop_recording()
            actions = self.controller.get_actions()
            action_count = len(actions)
            print(f"✓ 입력 기록을 중지했습니다. {action_count}개의 액션이 기록되었습니다.")
            
            if action_count > 0:
                print("  'save <이름>' 명령으로 테스트 케이스를 저장하세요.")
        except Exception as e:
            print(f"❌ 기록 중지 중 오류 발생: {e}")
    
    def _handle_save(self, args: List[str]):
        """save 명령어 처리 (Requirements 4.6)
        
        기록된 액션으로부터 Replay Script를 생성하고 테스트 케이스로 저장한다.
        
        Args:
            args: 명령어 인자 (테스트 케이스 이름)
        """
        if not args:
            print("❌ 사용법: save <테스트_케이스_이름>")
            print("  예: save login_test")
            return
        
        name = args[0]
        
        try:
            self.controller.save_test_case(name)
            print(f"✓ 테스트 케이스 '{name}'이(가) 저장되었습니다.")
            print(f"  스크립트: test_cases/{name}.py")
            print(f"  데이터: test_cases/{name}.json")
        except Exception as e:
            print(f"❌ 테스트 케이스 저장 중 오류 발생: {e}")
    
    def _handle_replay(self):
        """replay 명령어 처리 (Requirements 4.9)
        
        로드된 테스트 케이스를 재실행한다.
        """
        try:
            print("테스트 케이스를 재실행합니다...")
            self.controller.replay_test_case()
            print("✓ 재실행이 완료되었습니다.")
        except ValueError as e:
            print(f"❌ 오류: {e}")
            print("  먼저 'load <이름>' 명령으로 테스트 케이스를 로드하세요.")
        except Exception as e:
            print(f"❌ 재실행 중 오류 발생: {e}")
    
    def _handle_stats(self, args: List[str]):
        """stats 명령어 처리 (Requirements 15.1, 15.2)
        
        테스트 케이스의 실행 이력과 통계를 표시한다.
        
        Args:
            args: 명령어 인자 (테스트 케이스 이름, 선택사항)
        """
        try:
            # 테스트 케이스 이름 결정
            test_case_name = args[0] if args else None
            
            # 실행 이력 조회
            history = self.controller.get_execution_history(test_case_name)
            
            # 테스트 케이스 이름 표시
            display_name = test_case_name
            if display_name is None and self.controller.current_test_case:
                display_name = self.controller.current_test_case.get('name', 'Unknown')
            
            print()
            print("=" * 60)
            print(f"  테스트 케이스: {display_name}")
            print("=" * 60)
            
            if not history:
                print("\n  실행 이력이 없습니다.")
                print("  'replay' 명령으로 테스트를 실행하면 이력이 기록됩니다.")
                return
            
            # 실행 이력 표시 (Requirements 15.1)
            print("\n[실행 이력]")
            print("-" * 60)
            print(f"{'날짜/시간':<22} {'성공률':>8} {'오류':>6} {'의미론적 매칭':>12}")
            print("-" * 60)
            
            for session in history:
                timestamp = session.get("timestamp", "")
                # ISO 형식 타임스탬프를 읽기 쉬운 형식으로 변환
                if timestamp:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamp_display = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        timestamp_display = timestamp[:19]
                else:
                    timestamp_display = "Unknown"
                
                success_rate = session.get("success_rate", 0.0) * 100
                failure_count = session.get("failure_count", 0)
                semantic_rate = session.get("semantic_match_rate", 0.0) * 100
                
                print(f"{timestamp_display:<22} {success_rate:>7.1f}% {failure_count:>6} {semantic_rate:>11.1f}%")
            
            print("-" * 60)
            
            # 통계 요약 표시 (Requirements 15.2)
            stats = self.controller.get_execution_statistics(test_case_name)
            
            print("\n[통계 요약]")
            print(f"  총 실행 횟수: {stats.get('total_executions', 0)}회")
            print(f"  평균 성공률: {stats.get('avg_success_rate', 0.0) * 100:.1f}%")
            print(f"  총 오류 수: {stats.get('total_errors', 0)}개")
            print(f"  평균 의미론적 매칭률: {stats.get('avg_semantic_match_rate', 0.0) * 100:.1f}%")
            
            # 최근 실행 정보
            latest = stats.get('latest_execution')
            if latest:
                print(f"\n[최근 실행]")
                latest_timestamp = latest.get("timestamp", "")
                if latest_timestamp:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
                        latest_display = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        latest_display = latest_timestamp[:19]
                else:
                    latest_display = "Unknown"
                print(f"  시간: {latest_display}")
                print(f"  성공률: {latest.get('success_rate', 0.0) * 100:.1f}%")
                print(f"  성공: {latest.get('success_count', 0)}개 / 실패: {latest.get('failure_count', 0)}개")
            
            print()
            
        except ValueError as e:
            print(f"❌ 오류: {e}")
            print("  사용법: stats [테스트_케이스_이름]")
            print("  테스트 케이스 이름을 지정하거나, 먼저 'load <이름>' 명령으로 테스트 케이스를 로드하세요.")
        except Exception as e:
            print(f"❌ 통계 조회 중 오류 발생: {e}")


if __name__ == '__main__':
    # 간단한 테스트용 Mock Controller
    class MockController:
        def __init__(self):
            self.current_test_case = None
        
        def start_game(self):
            print("[Mock] 게임 시작")
            return True
        
        def start_recording(self):
            print("[Mock] 기록 시작")
        
        def stop_recording(self):
            print("[Mock] 기록 중지")
        
        def get_actions(self):
            return [1, 2, 3]  # 3개의 더미 액션
        
        def save_test_case(self, name):
            print(f"[Mock] 테스트 케이스 저장: {name}")
        
        def replay_test_case(self):
            print("[Mock] 테스트 케이스 재실행")
        
        def get_execution_history(self, test_case_name=None):
            # Mock 실행 이력 반환
            return [
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
        
        def get_execution_statistics(self, test_case_name=None):
            return {
                "test_case_name": test_case_name or "mock_test",
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
    
    # CLI 테스트 실행
    cli = CLIInterface(MockController())
    cli.start_interactive_session()
