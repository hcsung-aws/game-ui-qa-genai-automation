#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
자동 생성된 Replay Script

이 스크립트는 기록된 액션을 재실행합니다.
--verify 옵션으로 검증 모드를 활성화할 수 있습니다.
"""

import pyautogui
import time
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# 검증 모드용 임포트
try:
    from src.config_manager import ConfigManager
    from src.replay_verifier import ReplayVerifier
    VERIFY_AVAILABLE = True
except ImportError:
    VERIFY_AVAILABLE = False

# 기록된 액션 데이터
ACTIONS = [
    {
        'timestamp': '2025-12-24T00:40:54.620002',
        'action_type': 'click',
        'x': 996,
        'y': 284,
        'description': '클릭 (996, 284)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2025-12-24T00:40:56.939397',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.9초 대기',
        'wait_time': 3.9,
    },
    {
        'timestamp': '2025-12-24T00:41:00.814565',
        'action_type': 'click',
        'x': 759,
        'y': 625,
        'description': '클릭 (759, 625)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2025-12-24T00:41:03.031083',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.5초 대기',
        'wait_time': 3.5,
    },
    {
        'timestamp': '2025-12-24T00:41:06.484826',
        'action_type': 'click',
        'x': 1016,
        'y': 375,
        'description': '클릭 (1016, 375)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0002.png',
    },
    {
        'timestamp': '2025-12-24T00:41:08.648226',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.5초 대기',
        'wait_time': 3.5,
    },
    {
        'timestamp': '2025-12-24T00:41:12.109925',
        'action_type': 'click',
        'x': 416,
        'y': 219,
        'description': '클릭 (416, 219)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0003.png',
    },
    {
        'timestamp': '2025-12-24T00:41:14.242201',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.9초 대기',
        'wait_time': 2.9,
    },
    {
        'timestamp': '2025-12-24T00:41:17.157168',
        'action_type': 'click',
        'x': 315,
        'y': 521,
        'description': '클릭 (315, 521)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0004.png',
    },
    {
        'timestamp': '2025-12-24T00:41:19.382484',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.8초 대기',
        'wait_time': 2.8,
    },
    {
        'timestamp': '2025-12-24T00:41:22.227561',
        'action_type': 'click',
        'x': 312,
        'y': 631,
        'description': '클릭 (312, 631)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0005.png',
    },
    {
        'timestamp': '2025-12-24T00:41:24.404398',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.6초 대기',
        'wait_time': 3.6,
    },
    {
        'timestamp': '2025-12-24T00:41:27.979888',
        'action_type': 'click',
        'x': 174,
        'y': 213,
        'description': '클릭 (174, 213)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0006.png',
    },
    {
        'timestamp': '2025-12-24T00:41:30.155767',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.1초 대기',
        'wait_time': 1.1,
    },
    {
        'timestamp': '2025-12-24T00:41:31.261157',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: Key.alt_l',
        'key': 'Key.alt_l',
        'screenshot_path': 'screenshots/action_0007.png',
    },
    {
        'timestamp': '2025-12-24T00:41:33.386067',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: o',
        'key': 'o',
        'screenshot_path': 'screenshots/action_0008.png',
    },
]

def replay_actions(action_delay=0.5, verify=False, test_case_name="unknown"):
    """액션을 순서대로 재실행
    
    Args:
        action_delay: 액션 간 지연 시간 (초)
        verify: 검증 모드 활성화 여부
        test_case_name: 테스트 케이스 이름 (검증 모드용)
    """
    verifier = None
    
    # 검증 모드 초기화
    if verify and VERIFY_AVAILABLE:
        config = ConfigManager()
        config.load_config()
        verifier = ReplayVerifier(config)
        verifier.start_verification_session(test_case_name)
        print("✓ 검증 모드 활성화")
    elif verify and not VERIFY_AVAILABLE:
        print("⚠ 검증 모듈을 로드할 수 없습니다. 검증 없이 진행합니다.")
    
    print(f"총 16개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (996, 284)'
    print(f'[1/16] ' + '클릭 (996, 284)')
    try:
        pyautogui.click(996, 284, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[1] if 1 < len(ACTIONS) else None
            verifier.capture_and_verify(0, ACTIONS[0], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 2: '3.9초 대기'
    print(f'[2/16] ' + '3.9초 대기')
    try:
        time.sleep(3.9)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[2] if 2 < len(ACTIONS) else None
            verifier.capture_and_verify(1, ACTIONS[1], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 3: '클릭 (759, 625)'
    print(f'[3/16] ' + '클릭 (759, 625)')
    try:
        pyautogui.click(759, 625, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[3] if 3 < len(ACTIONS) else None
            verifier.capture_and_verify(2, ACTIONS[2], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 4: '3.5초 대기'
    print(f'[4/16] ' + '3.5초 대기')
    try:
        time.sleep(3.5)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[4] if 4 < len(ACTIONS) else None
            verifier.capture_and_verify(3, ACTIONS[3], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 5: '클릭 (1016, 375)'
    print(f'[5/16] ' + '클릭 (1016, 375)')
    try:
        pyautogui.click(1016, 375, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[5] if 5 < len(ACTIONS) else None
            verifier.capture_and_verify(4, ACTIONS[4], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 6: '3.5초 대기'
    print(f'[6/16] ' + '3.5초 대기')
    try:
        time.sleep(3.5)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[6] if 6 < len(ACTIONS) else None
            verifier.capture_and_verify(5, ACTIONS[5], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 7: '클릭 (416, 219)'
    print(f'[7/16] ' + '클릭 (416, 219)')
    try:
        pyautogui.click(416, 219, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[7] if 7 < len(ACTIONS) else None
            verifier.capture_and_verify(6, ACTIONS[6], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 8: '2.9초 대기'
    print(f'[8/16] ' + '2.9초 대기')
    try:
        time.sleep(2.9)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[8] if 8 < len(ACTIONS) else None
            verifier.capture_and_verify(7, ACTIONS[7], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 9: '클릭 (315, 521)'
    print(f'[9/16] ' + '클릭 (315, 521)')
    try:
        pyautogui.click(315, 521, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[9] if 9 < len(ACTIONS) else None
            verifier.capture_and_verify(8, ACTIONS[8], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 10: '2.8초 대기'
    print(f'[10/16] ' + '2.8초 대기')
    try:
        time.sleep(2.8)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[10] if 10 < len(ACTIONS) else None
            verifier.capture_and_verify(9, ACTIONS[9], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 11: '클릭 (312, 631)'
    print(f'[11/16] ' + '클릭 (312, 631)')
    try:
        pyautogui.click(312, 631, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[11] if 11 < len(ACTIONS) else None
            verifier.capture_and_verify(10, ACTIONS[10], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 12: '3.6초 대기'
    print(f'[12/16] ' + '3.6초 대기')
    try:
        time.sleep(3.6)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[12] if 12 < len(ACTIONS) else None
            verifier.capture_and_verify(11, ACTIONS[11], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 13: '클릭 (174, 213)'
    print(f'[13/16] ' + '클릭 (174, 213)')
    try:
        pyautogui.click(174, 213, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[13] if 13 < len(ACTIONS) else None
            verifier.capture_and_verify(12, ACTIONS[12], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 14: '1.1초 대기'
    print(f'[14/16] ' + '1.1초 대기')
    try:
        time.sleep(1.1)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[14] if 14 < len(ACTIONS) else None
            verifier.capture_and_verify(13, ACTIONS[13], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 15: '키 입력: Key.alt_l'
    print(f'[15/16] ' + '키 입력: Key.alt_l')
    try:
        pyautogui.press('alt_l')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[15] if 15 < len(ACTIONS) else None
            verifier.capture_and_verify(14, ACTIONS[14], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 16: '키 입력: o'
    print(f'[16/16] ' + '키 입력: o')
    try:
        pyautogui.write('o')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            verifier.capture_and_verify(15, ACTIONS[15], None)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    print()
    print('✓ 재실행 완료')

    # 검증 보고서 생성
    if verifier:
        report = verifier.generate_report()
        verifier.print_report(report)
        verifier.save_report(report)
        return report
    return None


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Replay Script')
    parser.add_argument('--delay', type=float, default=0.5, help='액션 간 지연 시간 (초)')
    parser.add_argument('--verify', action='store_true', help='검증 모드 활성화')
    parser.add_argument('--name', type=str, default='unknown', help='테스트 케이스 이름')
    
    args = parser.parse_args()
    
    # 테스트 케이스 이름 자동 추출 (파일명에서)
    if args.name == 'unknown':
        import os
        args.name = os.path.splitext(os.path.basename(__file__))[0]
    
    # 액션 재실행
    replay_actions(action_delay=args.delay, verify=args.verify, test_case_name=args.name)
