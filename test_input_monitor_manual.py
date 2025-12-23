"""
InputMonitor 수동 테스트 스크립트

이 스크립트를 실행하면 입력을 모니터링하고 기록된 액션을 출력한다.
사용자가 직접 테스트 시간을 조절할 수 있다.
"""

import time
import sys
import os

# src 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from input_monitor import InputMonitor, ActionRecorder
from config_manager import ConfigManager


def print_banner():
    """테스트 배너 출력"""
    print("=" * 60)
    print("   InputMonitor 수동 테스트 (Task 3 검증)")
    print("=" * 60)
    print()
    print("이 테스트는 다음을 검증합니다:")
    print("  ✓ Requirements 3.2: 마우스 클릭 캡처 (좌표, 버튼 정보)")
    print("  ✓ Requirements 3.3: 키보드 입력 캡처 (키 정보)")
    print()


def print_instructions():
    """테스트 지침 출력"""
    print("테스트 방법:")
    print("  1. 마우스 왼쪽/오른쪽 버튼을 여러 위치에서 클릭해보세요")
    print("  2. 키보드로 문자를 입력해보세요 (a, b, c 등)")
    print("  3. 특수 키를 눌러보세요 (Enter, Space, Shift 등)")
    print("  4. 마우스 스크롤을 해보세요")
    print()


def print_action_summary(actions):
    """액션 요약 통계 출력"""
    click_count = sum(1 for a in actions if a.action_type == 'click')
    key_count = sum(1 for a in actions if a.action_type == 'key_press')
    scroll_count = sum(1 for a in actions if a.action_type == 'scroll')
    wait_count = sum(1 for a in actions if a.action_type == 'wait')
    
    print("\n" + "=" * 60)
    print("   테스트 결과 요약")
    print("=" * 60)
    print(f"총 기록된 액션: {len(actions)}개")
    print(f"  - 클릭: {click_count}개")
    print(f"  - 키 입력: {key_count}개")
    print(f"  - 스크롤: {scroll_count}개")
    print(f"  - 대기: {wait_count}개")
    print()


def print_action_details(actions):
    """액션 상세 정보 출력"""
    print("=" * 60)
    print("   기록된 액션 상세 목록")
    print("=" * 60)
    
    for i, action in enumerate(actions, 1):
        print(f"\n[{i}] {action.action_type.upper()}")
        print(f"    설명: {action.description}")
        print(f"    시간: {action.timestamp}")
        
        if action.action_type == 'click':
            print(f"    좌표: ({action.x}, {action.y})")
            print(f"    버튼: {action.button}")
        elif action.action_type == 'key_press':
            print(f"    키: {action.key}")
        elif action.action_type == 'scroll':
            print(f"    좌표: ({action.x}, {action.y})")
            print(f"    스크롤: dx={action.scroll_dx}, dy={action.scroll_dy}")
        elif action.action_type == 'wait':
            print(f"    (자동 삽입된 대기 액션)")


def main():
    print_banner()
    print_instructions()
    
    # 테스트 시간 입력
    print("모니터링 시간을 입력하세요 (초, 기본값: 10초):")
    duration_input = input("> ").strip()
    
    try:
        duration = int(duration_input) if duration_input else 10
    except ValueError:
        duration = 10
        print(f"잘못된 입력입니다. 기본값 {duration}초를 사용합니다.")
    
    print(f"\n준비되면 Enter를 누르세요... ({duration}초 동안 모니터링)")
    input()
    
    # ConfigManager 초기화
    config = ConfigManager('config.json')
    try:
        config.load_config()
    except FileNotFoundError:
        config.create_default_config()
    
    # ActionRecorder와 InputMonitor 초기화
    recorder = ActionRecorder(config)
    monitor = InputMonitor(recorder)
    
    # 모니터링 시작
    print(f"\n{'*' * 60}")
    print(f"   모니터링 시작! {duration}초 동안 입력을 시도하세요...")
    print(f"{'*' * 60}\n")
    
    monitor.start_monitoring()
    
    # 카운트다운
    for remaining in range(duration, 0, -1):
        print(f"남은 시간: {remaining}초...", end='\r')
        time.sleep(1)
    
    # 모니터링 중지
    monitor.stop_monitoring()
    print("\n\n✓ 모니터링 중지")
    
    # 기록된 액션 분석 및 출력
    actions = recorder.get_actions()
    
    if len(actions) == 0:
        print("\n⚠ 기록된 액션이 없습니다.")
        print("   마우스나 키보드 입력이 감지되지 않았습니다.")
        return
    
    # 요약 출력
    print_action_summary(actions)
    
    # 상세 정보 출력 여부 확인
    print("상세 액션 목록을 보시겠습니까? (y/n, 기본값: y)")
    show_details = input("> ").strip().lower()
    
    if show_details != 'n':
        print_action_details(actions)
    
    print("\n" + "=" * 60)
    print("   테스트 완료!")
    print("=" * 60)
    print("\n검증 사항:")
    print("  ✓ 클릭한 위치의 좌표가 정확한가?")
    print("  ✓ 클릭한 버튼(left/right)이 올바른가?")
    print("  ✓ 입력한 키가 정확하게 기록되었는가?")
    print("  ✓ 스크롤 방향과 양이 올바른가?")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
