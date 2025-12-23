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
        'timestamp': '2025-12-24T00:27:33.621929',
        'action_type': 'click',
        'x': 973,
        'y': 256,
        'description': '클릭 (973, 256)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2025-12-24T00:27:34.416588',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.9초 대기',
        'wait_time': 1.9,
    },
    {
        'timestamp': '2025-12-24T00:27:36.284528',
        'action_type': 'click',
        'x': 762,
        'y': 630,
        'description': '클릭 (762, 630)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2025-12-24T00:27:36.973728',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.7초 대기',
        'wait_time': 1.7,
    },
    {
        'timestamp': '2025-12-24T00:27:38.647312',
        'action_type': 'click',
        'x': 969,
        'y': 330,
        'description': '클릭 (969, 330)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0002.png',
    },
    {
        'timestamp': '2025-12-24T00:27:39.365367',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.1초 대기',
        'wait_time': 2.1,
    },
    {
        'timestamp': '2025-12-24T00:27:41.421969',
        'action_type': 'click',
        'x': 389,
        'y': 215,
        'description': '클릭 (389, 215)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0003.png',
    },
    {
        'timestamp': '2025-12-24T00:27:42.063195',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.2초 대기',
        'wait_time': 1.2,
    },
    {
        'timestamp': '2025-12-24T00:27:43.221750',
        'action_type': 'click',
        'x': 308,
        'y': 499,
        'description': '클릭 (308, 499)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0004.png',
    },
    {
        'timestamp': '2025-12-24T00:27:43.895823',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '0.5초 대기',
        'wait_time': 0.5,
    },
    {
        'timestamp': '2025-12-24T00:27:44.414356',
        'action_type': 'click',
        'x': 319,
        'y': 639,
        'description': '클릭 (319, 639)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0005.png',
    },
    {
        'timestamp': '2025-12-24T00:27:45.066432',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '0.9초 대기',
        'wait_time': 0.9,
    },
    {
        'timestamp': '2025-12-24T00:27:45.921968',
        'action_type': 'click',
        'x': 266,
        'y': 222,
        'description': '클릭 (266, 222)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0006.png',
    },
    {
        'timestamp': '2025-12-24T00:27:46.602855',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '0.9초 대기',
        'wait_time': 0.9,
    },
    {
        'timestamp': '2025-12-24T00:27:47.526875',
        'action_type': 'click',
        'x': 179,
        'y': 222,
        'description': '클릭 (179, 222)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0007.png',
    },
    {
        'timestamp': '2025-12-24T00:27:48.152770',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '0.9초 대기',
        'wait_time': 0.9,
    },
    {
        'timestamp': '2025-12-24T00:27:49.026983',
        'action_type': 'click',
        'x': 569,
        'y': 968,
        'description': '클릭 (569, 968)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0008.png',
    },
    {
        'timestamp': '2025-12-24T00:27:49.703601',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: s',
        'key': 's',
        'screenshot_path': 'screenshots/action_0009.png',
    },
    {
        'timestamp': '2025-12-24T00:27:50.335638',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '0.8초 대기',
        'wait_time': 0.8,
    },
    {
        'timestamp': '2025-12-24T00:27:51.103596',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: t',
        'key': 't',
        'screenshot_path': 'screenshots/action_0010.png',
    },
    {
        'timestamp': '2025-12-24T00:27:51.689472',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: o',
        'key': 'o',
        'screenshot_path': 'screenshots/action_0011.png',
    },
    {
        'timestamp': '2025-12-24T00:27:52.335403',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: Key.enter',
        'key': 'Key.enter',
        'screenshot_path': 'screenshots/action_0012.png',
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
    
    print(f"총 22개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (973, 256)'
    print(f'[1/22] ' + '클릭 (973, 256)')
    try:
        pyautogui.click(973, 256, button='left')
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

    # 액션 2: '1.9초 대기'
    print(f'[2/22] ' + '1.9초 대기')
    try:
        time.sleep(1.9)
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

    # 액션 3: '클릭 (762, 630)'
    print(f'[3/22] ' + '클릭 (762, 630)')
    try:
        pyautogui.click(762, 630, button='left')
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

    # 액션 4: '1.7초 대기'
    print(f'[4/22] ' + '1.7초 대기')
    try:
        time.sleep(1.7)
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

    # 액션 5: '클릭 (969, 330)'
    print(f'[5/22] ' + '클릭 (969, 330)')
    try:
        pyautogui.click(969, 330, button='left')
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

    # 액션 6: '2.1초 대기'
    print(f'[6/22] ' + '2.1초 대기')
    try:
        time.sleep(2.1)
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

    # 액션 7: '클릭 (389, 215)'
    print(f'[7/22] ' + '클릭 (389, 215)')
    try:
        pyautogui.click(389, 215, button='left')
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

    # 액션 8: '1.2초 대기'
    print(f'[8/22] ' + '1.2초 대기')
    try:
        time.sleep(1.2)
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

    # 액션 9: '클릭 (308, 499)'
    print(f'[9/22] ' + '클릭 (308, 499)')
    try:
        pyautogui.click(308, 499, button='left')
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

    # 액션 10: '0.5초 대기'
    print(f'[10/22] ' + '0.5초 대기')
    try:
        time.sleep(0.5)
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

    # 액션 11: '클릭 (319, 639)'
    print(f'[11/22] ' + '클릭 (319, 639)')
    try:
        pyautogui.click(319, 639, button='left')
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

    # 액션 12: '0.9초 대기'
    print(f'[12/22] ' + '0.9초 대기')
    try:
        time.sleep(0.9)
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

    # 액션 13: '클릭 (266, 222)'
    print(f'[13/22] ' + '클릭 (266, 222)')
    try:
        pyautogui.click(266, 222, button='left')
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

    # 액션 14: '0.9초 대기'
    print(f'[14/22] ' + '0.9초 대기')
    try:
        time.sleep(0.9)
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

    # 액션 15: '클릭 (179, 222)'
    print(f'[15/22] ' + '클릭 (179, 222)')
    try:
        pyautogui.click(179, 222, button='left')
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

    # 액션 16: '0.9초 대기'
    print(f'[16/22] ' + '0.9초 대기')
    try:
        time.sleep(0.9)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[16] if 16 < len(ACTIONS) else None
            verifier.capture_and_verify(15, ACTIONS[15], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 17: '클릭 (569, 968)'
    print(f'[17/22] ' + '클릭 (569, 968)')
    try:
        pyautogui.click(569, 968, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[17] if 17 < len(ACTIONS) else None
            verifier.capture_and_verify(16, ACTIONS[16], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 18: '키 입력: s'
    print(f'[18/22] ' + '키 입력: s')
    try:
        pyautogui.write('s')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[18] if 18 < len(ACTIONS) else None
            verifier.capture_and_verify(17, ACTIONS[17], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 19: '0.8초 대기'
    print(f'[19/22] ' + '0.8초 대기')
    try:
        time.sleep(0.8)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[19] if 19 < len(ACTIONS) else None
            verifier.capture_and_verify(18, ACTIONS[18], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 20: '키 입력: t'
    print(f'[20/22] ' + '키 입력: t')
    try:
        pyautogui.write('t')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[20] if 20 < len(ACTIONS) else None
            verifier.capture_and_verify(19, ACTIONS[19], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 21: '키 입력: o'
    print(f'[21/22] ' + '키 입력: o')
    try:
        pyautogui.write('o')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[21] if 21 < len(ACTIONS) else None
            verifier.capture_and_verify(20, ACTIONS[20], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 22: '키 입력: Key.enter'
    print(f'[22/22] ' + '키 입력: Key.enter')
    try:
        pyautogui.press('enter')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            verifier.capture_and_verify(21, ACTIONS[21], None)
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
