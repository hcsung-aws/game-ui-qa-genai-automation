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
  replay [options]   - 로드된 테스트 케이스 재실행
                       --verify: 검증 모드 활성화
                       --report-dir <dir>: 보고서 저장 디렉토리 (기본: reports)
  enrich <name>      - 기존 테스트 케이스에 의미론적 정보 추가
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
            return self._handle_replay_with_args(args)
        elif cmd == "enrich":
            self._handle_enrich(args)
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
        테스트 케이스 이름을 먼저 입력받아 스크린샷 디렉토리를 구분한다.
        5초 대기 후 기록을 시작하여 사용자가 게임 창을 활성화할 시간을 준다.
        """
        import time
        try:
            # 테스트 케이스 이름 입력받기
            print("테스트 케이스 이름을 입력하세요 (스크린샷 저장 디렉토리로 사용됩니다):")
            test_case_name = input("  이름: ").strip()
            
            if not test_case_name:
                print("❌ 테스트 케이스 이름이 필요합니다.")
                return
            
            print(f"✓ 테스트 케이스: {test_case_name}")
            print(f"  스크린샷 저장 경로: screenshots/{test_case_name}/")
            print()
            print("✓ 5초 후 입력 기록을 시작합니다. 게임 창을 활성화하세요...")
            for i in range(5, 0, -1):
                print(f"  {i}...")
                time.sleep(1)
            
            self.controller.start_recording(test_case_name)
            print("✓ 입력 기록을 시작합니다!")
            print("  게임을 플레이하세요. 모든 마우스/키보드 입력이 기록됩니다.")
            print("  'stop' 명령으로 기록을 중지하세요.")
        except Exception as e:
            print(f"❌ 기록 시작 중 오류 발생: {e}")
    
    def _handle_stop(self):
        """stop 명령어 처리 (Requirements 4.4)
        
        입력 모니터링을 중지하고 기록된 액션을 자동 저장한다.
        """
        try:
            test_case_name = self.controller.stop_recording()
            actions = self.controller.get_actions()
            action_count = len(actions)
            print(f"✓ 입력 기록을 중지했습니다. {action_count}개의 액션이 기록되었습니다.")
            
            if action_count > 0 and test_case_name:
                # 자동 저장
                self.controller.save_test_case(test_case_name)
                print(f"✓ 테스트 케이스 '{test_case_name}'이(가) 자동 저장되었습니다.")
                print(f"  스크립트: test_cases/{test_case_name}.py")
                print(f"  데이터: test_cases/{test_case_name}.json")
                print(f"  스크린샷: screenshots/{test_case_name}/")
            elif action_count > 0:
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
            
            # 매칭 통계 출력 (Requirements 4.1, 4.3, 4.4)
            self._display_matching_statistics()
            
        except ValueError as e:
            print(f"❌ 오류: {e}")
            print("  먼저 'load <이름>' 명령으로 테스트 케이스를 로드하세요.")
        except Exception as e:
            print(f"❌ 재실행 중 오류 발생: {e}")
    
    def _handle_replay_with_args(self, args: List[str]) -> bool:
        """replay 명령어 처리 (인자 포함) (Requirements 5.1, 5.2, 5.3, 5.4, 5.5)
        
        --verify 옵션으로 검증 모드를 활성화하고,
        --report-dir 옵션으로 보고서 저장 디렉토리를 지정할 수 있다.
        
        Args:
            args: 명령어 인자 (--verify, --report-dir 등)
            
        Returns:
            계속 실행 여부 (항상 True)
        """
        # 인자 파싱
        verify = False
        report_dir = "reports"
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--verify":
                verify = True
            elif arg == "--report-dir":
                if i + 1 < len(args):
                    report_dir = args[i + 1]
                    i += 1
                else:
                    print("❌ --report-dir 옵션에 디렉토리 경로가 필요합니다.")
                    return True
            i += 1
        
        # 검증 모드가 아니면 기존 방식으로 실행
        if not verify:
            self._handle_replay()
            return True
        
        # 검증 모드로 실행 (Requirements 5.1)
        try:
            if not self.controller.current_test_case:
                print("❌ 로드된 테스트 케이스가 없습니다.")
                print("  먼저 'load <이름>' 명령으로 테스트 케이스를 로드하세요.")
                return True
            
            print("테스트 케이스를 검증 모드로 재실행합니다...")
            print(f"  보고서 저장 디렉토리: {report_dir}")
            
            # ScriptGenerator를 사용하여 검증 모드로 실행
            test_passed, report = self.controller.script_generator.replay_with_verification(
                self.controller.current_test_case,
                verify=True,
                report_dir=report_dir
            )
            
            # 테스트 결과 요약 출력 (Requirements 5.2)
            self._display_verification_summary(test_passed, report)
            
            # 종료 코드 저장 (CLI 종료 시 사용)
            self._last_test_result = test_passed
            
        except ValueError as e:
            print(f"❌ 오류: {e}")
            print("  먼저 'load <이름>' 명령으로 테스트 케이스를 로드하세요.")
            self._last_test_result = False
        except Exception as e:
            print(f"❌ 재실행 중 오류 발생: {e}")
            self._last_test_result = False
        
        return True
    
    def _display_verification_summary(self, test_passed: bool, report):
        """검증 결과 요약 출력 (Requirements 5.2)
        
        Args:
            test_passed: 테스트 성공 여부
            report: ReplayReport 객체
        """
        print()
        print("=" * 50)
        print("       검증 결과 요약")
        print("=" * 50)
        
        if report:
            print(f"  테스트 케이스: {report.test_case_name}")
            print(f"  전체 액션 수: {report.total_actions}")
            print("-" * 50)
            print(f"  성공 (pass): {report.passed_count}")
            print(f"  경고 (warning): {report.warning_count}")
            print(f"  실패 (fail): {report.failed_count}")
            print("-" * 50)
            print(f"  성공률: {report.success_rate * 100:.1f}%")
        
        print()
        if test_passed:
            print("✓ 테스트 성공")
        else:
            print("✗ 테스트 실패")
        print("=" * 50)
    
    def get_last_test_result(self) -> bool:
        """마지막 테스트 결과 반환 (Requirements 5.3, 5.4)
        
        Returns:
            테스트 성공 여부 (True: 성공, False: 실패)
        """
        return getattr(self, '_last_test_result', True)
    
    def _display_matching_statistics(self):
        """재생 결과의 매칭 통계 출력 (Requirements 4.1, 4.3, 4.4)
        
        가장 최근 리포트 파일에서 통계를 읽어 출력한다.
        """
        import os
        import json
        import glob
        
        try:
            # 현재 테스트 케이스 이름 가져오기
            test_case_name = None
            if self.controller.current_test_case:
                test_case_name = self.controller.current_test_case.get('name')
            
            if not test_case_name:
                return
            
            # 리포트 디렉토리에서 가장 최근 리포트 파일 찾기
            reports_dir = 'reports'
            if not os.path.exists(reports_dir):
                return
            
            # 테스트 케이스 이름으로 시작하는 semantic_report.json 파일 찾기
            pattern = os.path.join(reports_dir, f"{test_case_name}_*_semantic_report.json")
            report_files = glob.glob(pattern)
            
            if not report_files:
                return
            
            # 가장 최근 파일 선택 (파일명에 타임스탬프 포함)
            latest_report = max(report_files, key=os.path.getmtime)
            
            with open(latest_report, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # 통계 출력
            total = report_data.get('total_actions', 0)
            success = report_data.get('success_count', 0)
            semantic = report_data.get('semantic_match_count', 0)
            coordinate = report_data.get('coordinate_match_count', 0)
            failed = report_data.get('failed_count', 0)
            
            if total == 0:
                return
            
            print()
            print("=" * 50)
            print("       매칭 통계")
            print("=" * 50)
            print(f"  전체 액션 수: {total}")
            print(f"  성공: {success} ({success/total*100:.1f}%)")
            print("-" * 50)
            print(f"  의미론적 매칭: {semantic} ({semantic/total*100:.1f}%)")
            print(f"  좌표 기반 매칭: {coordinate} ({coordinate/total*100:.1f}%)")
            print(f"  실패: {failed} ({failed/total*100:.1f}%)")
            
            # 좌표 변위 통계 계산 (Requirements 4.3)
            results = report_data.get('results', [])
            coord_changes = []
            confidences = []
            
            for r in results:
                change = r.get('coordinate_change')
                if change and isinstance(change, (list, tuple)) and len(change) >= 2:
                    dx, dy = change[0], change[1]
                    distance = (dx ** 2 + dy ** 2) ** 0.5
                    coord_changes.append(distance)
                
                conf = r.get('match_confidence', 0)
                if conf > 0:
                    confidences.append(conf)
            
            if coord_changes:
                avg_change = sum(coord_changes) / len(coord_changes)
                max_change = max(coord_changes)
                print("-" * 50)
                print(f"  평균 좌표 변위: {avg_change:.1f}px")
                print(f"  최대 좌표 변위: {max_change:.1f}px")
            
            if confidences:
                avg_conf = sum(confidences) / len(confidences)
                print(f"  평균 매칭 신뢰도: {avg_conf:.2f}")
            
            print("=" * 50)
            print()
            
        except Exception as e:
            # 통계 출력 실패는 무시 (재생 자체는 성공)
            pass
    
    def _handle_enrich(self, args: List[str]):
        """enrich 명령어 처리 (Requirements 5.2, 5.4)
        
        기존 테스트 케이스에 의미론적 정보를 추가한다.
        
        Args:
            args: 명령어 인자 (테스트 케이스 이름)
        """
        if not args:
            print("❌ 사용법: enrich <테스트_케이스_이름>")
            print("  예: enrich login_test")
            return
        
        name = args[0]
        
        try:
            # 레거시 테스트 케이스 여부 확인
            print(f"테스트 케이스 '{name}'을(를) 분석합니다...")
            
            is_legacy = self.controller.is_legacy_test_case(name)
            if not is_legacy:
                print(f"ℹ 테스트 케이스 '{name}'은(는) 이미 의미론적 정보를 포함하고 있습니다.")
                print("  계속 보강하시겠습니까? (y/n): ", end="")
                response = input().strip().lower()
                if response != 'y':
                    print("  보강을 취소했습니다.")
                    return
            
            # 보강 수행
            print("의미론적 정보를 추가하는 중...")
            enriched_test_case, result = self.controller.enrich_test_case(name)
            
            # 결과 출력
            print()
            print("=" * 50)
            print("       보강 결과")
            print("=" * 50)
            print(f"  테스트 케이스: {name}")
            print(f"  버전: {result.version}")
            print("-" * 50)
            print(f"  전체 액션 수: {result.total_actions}")
            print(f"  보강 성공: {result.enriched_count}")
            print(f"  스킵됨: {result.skipped_count}")
            print(f"  실패: {result.failed_count}")
            print("-" * 50)
            
            # 성공률 계산
            if result.total_actions > 0:
                success_rate = (result.enriched_count / result.total_actions) * 100
                print(f"  보강 성공률: {success_rate:.1f}%")
            
            print()
            print(f"✓ 테스트 케이스 '{name}'이(가) 보강되었습니다.")
            
        except FileNotFoundError:
            print(f"❌ 테스트 케이스를 찾을 수 없습니다: {name}")
            print("  test_cases 디렉토리에 해당 파일이 있는지 확인하세요.")
        except Exception as e:
            print(f"❌ 보강 중 오류 발생: {e}")
    
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
        
        def start_recording(self, test_case_name=None):
            print(f"[Mock] 기록 시작 (테스트 케이스: {test_case_name})")
        
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
        
        def is_legacy_test_case(self, name):
            print(f"[Mock] 레거시 테스트 케이스 확인: {name}")
            return True
        
        def enrich_test_case(self, name):
            print(f"[Mock] 테스트 케이스 보강: {name}")
            # Mock EnrichmentResult 반환
            from dataclasses import dataclass
            
            @dataclass
            class MockEnrichmentResult:
                total_actions: int = 10
                enriched_count: int = 8
                skipped_count: int = 1
                failed_count: int = 1
                version: str = "2.0"
            
            return {"name": name}, MockEnrichmentResult()
    
    # CLI 테스트 실행
    cli = CLIInterface(MockController())
    cli.start_interactive_session()
