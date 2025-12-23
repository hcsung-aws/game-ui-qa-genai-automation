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
        'timestamp': '2025-12-24T00:33:54.016963',
        'action_type': 'click',
        'x': 988,
        'y': 278,
        'description': '클릭 (988, 278)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2025-12-24T00:33:55.278952',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '5.4초 대기',
        'wait_time': 5.4,
    },
    {
        'timestamp': '2025-12-24T00:34:00.646333',
        'action_type': 'click',
        'x': 782,
        'y': 643,
        'description': '클릭 (782, 643)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2025-12-24T00:34:01.802295',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.9초 대기',
        'wait_time': 4.9,
    },
    {
        'timestamp': '2025-12-24T00:34:06.661944',
        'action_type': 'click',
        'x': 1003,
        'y': 372,
        'description': '클릭 (1003, 372)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0002.png',
    },
    {
        'timestamp': '2025-12-24T00:34:07.771636',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '5.6초 대기',
        'wait_time': 5.6,
    },
    {
        'timestamp': '2025-12-24T00:34:13.374403',
        'action_type': 'click',
        'x': 390,
        'y': 227,
        'description': '클릭 (390, 227)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0003.png',
    },
    {
        'timestamp': '2025-12-24T00:34:14.567327',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.8초 대기',
        'wait_time': 4.8,
    },
    {
        'timestamp': '2025-12-24T00:34:19.351743',
        'action_type': 'click',
        'x': 311,
        'y': 524,
        'description': '클릭 (311, 524)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0004.png',
    },
    {
        'timestamp': '2025-12-24T00:34:20.546013',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.1초 대기',
        'wait_time': 4.1,
    },
    {
        'timestamp': '2025-12-24T00:34:24.609499',
        'action_type': 'click',
        'x': 322,
        'y': 646,
        'description': '클릭 (322, 646)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0005.png',
    },
    {
        'timestamp': '2025-12-24T00:34:25.788884',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '5.8초 대기',
        'wait_time': 5.8,
    },
    {
        'timestamp': '2025-12-24T00:34:31.636513',
        'action_type': 'click',
        'x': 147,
        'y': 220,
        'description': '클릭 (147, 220)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0006.png',
    },
    {
        'timestamp': '2025-12-24T00:34:32.781761',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.3초 대기',
        'wait_time': 1.3,
    },
    {
        'timestamp': '2025-12-24T00:34:32.781761',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.0초 대기',
        'wait_time': 2.0,
    },
    {
        'timestamp': '2025-12-24T00:34:34.074523',
        'action_type': 'click',
        'x': 780,
        'y': 952,
        'description': '클릭 (780, 952)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0007.png',
    },
    {
        'timestamp': '2025-12-24T00:34:34.799314',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: s',
        'key': 's',
        'screenshot_path': 'screenshots/action_0008.png',
    },
    {
        'timestamp': '2025-12-24T00:34:35.871441',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: o',
        'key': 'o',
        'screenshot_path': 'screenshots/action_0009.png',
    },
    {
        'timestamp': '2025-12-24T00:34:36.944900',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: Key.enter',
        'key': 'Key.enter',
        'screenshot_path': 'screenshots/action_0010.png',
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
    
    print(f"총 19개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (988, 278)'
    print(f'[1/19] ' + '클릭 (988, 278)')
    try:
        pyautogui.click(988, 278, button='left')
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

    # 액션 2: '5.4초 대기'
    print(f'[2/19] ' + '5.4초 대기')
    try:
        time.sleep(5.4)
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

    # 액션 3: '클릭 (782, 643)'
    print(f'[3/19] ' + '클릭 (782, 643)')
    try:
        pyautogui.click(782, 643, button='left')
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

    # 액션 4: '4.9초 대기'
    print(f'[4/19] ' + '4.9초 대기')
    try:
        time.sleep(4.9)
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

    # 액션 5: '클릭 (1003, 372)'
    print(f'[5/19] ' + '클릭 (1003, 372)')
    try:
        pyautogui.click(1003, 372, button='left')
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

    # 액션 6: '5.6초 대기'
    print(f'[6/19] ' + '5.6초 대기')
    try:
        time.sleep(5.6)
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

    # 액션 7: '클릭 (390, 227)'
    print(f'[7/19] ' + '클릭 (390, 227)')
    try:
        pyautogui.click(390, 227, button='left')
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

    # 액션 8: '4.8초 대기'
    print(f'[8/19] ' + '4.8초 대기')
    try:
        time.sleep(4.8)
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

    # 액션 9: '클릭 (311, 524)'
    print(f'[9/19] ' + '클릭 (311, 524)')
    try:
        pyautogui.click(311, 524, button='left')
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

    # 액션 10: '4.1초 대기'
    print(f'[10/19] ' + '4.1초 대기')
    try:
        time.sleep(4.1)
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

    # 액션 11: '클릭 (322, 646)'
    print(f'[11/19] ' + '클릭 (322, 646)')
    try:
        pyautogui.click(322, 646, button='left')
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

    # 액션 12: '5.8초 대기'
    print(f'[12/19] ' + '5.8초 대기')
    try:
        time.sleep(5.8)
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

    # 액션 13: '클릭 (147, 220)'
    print(f'[13/19] ' + '클릭 (147, 220)')
    try:
        pyautogui.click(147, 220, button='left')
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

    # 액션 14: '1.3초 대기'
    print(f'[14/19] ' + '1.3초 대기')
    try:
        time.sleep(1.3)
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

    # 액션 15: '2.0초 대기'
    print(f'[15/19] ' + '2.0초 대기')
    try:
        time.sleep(2.0)
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

    # 액션 16: '클릭 (780, 952)'
    print(f'[16/19] ' + '클릭 (780, 952)')
    try:
        pyautogui.click(780, 952, button='left')
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

    # 액션 17: '키 입력: s'
    print(f'[17/19] ' + '키 입력: s')
    try:
        pyautogui.write('s')
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

    # 액션 18: '키 입력: o'
    print(f'[18/19] ' + '키 입력: o')
    try:
        pyautogui.write('o')
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

    # 액션 19: '키 입력: Key.enter'
    print(f'[19/19] ' + '키 입력: Key.enter')
    try:
        pyautogui.press('enter')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            verifier.capture_and_verify(18, ACTIONS[18], None)
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
