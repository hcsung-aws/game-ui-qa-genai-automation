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
        'timestamp': '2025-12-24T00:20:20.754568',
        'action_type': 'click',
        'x': 971,
        'y': 261,
        'description': '클릭 (971, 261)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2025-12-24T00:20:21.023677',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.6초 대기',
        'wait_time': 2.6,
    },
    {
        'timestamp': '2025-12-24T00:20:23.387500',
        'action_type': 'click',
        'x': 757,
        'y': 641,
        'description': '클릭 (757, 641)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2025-12-24T00:20:23.630922',
        'action_type': 'click',
        'x': 757,
        'y': 641,
        'description': '클릭 (757, 641)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0003.png',
    },
    {
        'timestamp': '2025-12-24T00:20:23.894895',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.2초 대기',
        'wait_time': 1.2,
    },
    {
        'timestamp': '2025-12-24T00:20:24.849870',
        'action_type': 'click',
        'x': 1032,
        'y': 376,
        'description': '클릭 (1032, 376)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0004.png',
    },
    {
        'timestamp': '2025-12-24T00:20:25.073368',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.0초 대기',
        'wait_time': 2.0,
    },
    {
        'timestamp': '2025-12-24T00:20:26.883185',
        'action_type': 'click',
        'x': 407,
        'y': 220,
        'description': '클릭 (407, 220)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0006.png',
    },
    {
        'timestamp': '2025-12-24T00:20:27.102799',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.3초 대기',
        'wait_time': 1.3,
    },
    {
        'timestamp': '2025-12-24T00:20:28.187456',
        'action_type': 'click',
        'x': 325,
        'y': 488,
        'description': '클릭 (325, 488)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0008.png',
    },
    {
        'timestamp': '2025-12-24T00:20:28.387767',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.0초 대기',
        'wait_time': 1.0,
    },
    {
        'timestamp': '2025-12-24T00:20:29.215071',
        'action_type': 'click',
        'x': 310,
        'y': 633,
        'description': '클릭 (310, 633)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0010.png',
    },
    {
        'timestamp': '2025-12-24T00:20:29.375085',
        'action_type': 'click',
        'x': 310,
        'y': 633,
        'description': '클릭 (310, 633)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0012.png',
    },
    {
        'timestamp': '2025-12-24T00:20:29.579548',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.5초 대기',
        'wait_time': 1.5,
    },
    {
        'timestamp': '2025-12-24T00:20:30.932429',
        'action_type': 'click',
        'x': 289,
        'y': 219,
        'description': '클릭 (289, 219)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0013.png',
    },
    {
        'timestamp': '2025-12-24T00:20:31.122818',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.6초 대기',
        'wait_time': 1.6,
    },
    {
        'timestamp': '2025-12-24T00:20:32.537912',
        'action_type': 'click',
        'x': 183,
        'y': 218,
        'description': '클릭 (183, 218)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0015.png',
    },
    {
        'timestamp': '2025-12-24T00:20:32.704176',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.3초 대기',
        'wait_time': 1.3,
    },
    {
        'timestamp': '2025-12-24T00:20:33.752944',
        'action_type': 'click',
        'x': 833,
        'y': 959,
        'description': '클릭 (833, 959)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0017.png',
    },
    {
        'timestamp': '2025-12-24T00:20:34.226122',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: s',
        'key': 's',
        'screenshot_path': 'screenshots/action_0019.png',
    },
    {
        'timestamp': '2025-12-24T00:20:34.697983',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: o',
        'key': 'o',
        'screenshot_path': 'screenshots/action_0020.png',
    },
    {
        'timestamp': '2025-12-24T00:20:35.074079',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: Key.backspace',
        'key': 'Key.backspace',
        'screenshot_path': 'screenshots/action_0021.png',
    },
    {
        'timestamp': '2025-12-24T00:20:35.418455',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: t',
        'key': 't',
        'screenshot_path': 'screenshots/action_0022.png',
    },
    {
        'timestamp': '2025-12-24T00:20:35.552374',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: o',
        'key': 'o',
        'screenshot_path': 'screenshots/action_0023.png',
    },
    {
        'timestamp': '2025-12-24T00:20:35.701543',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: p',
        'key': 'p',
        'screenshot_path': 'screenshots/action_0024.png',
    },
    {
        'timestamp': '2025-12-24T00:20:35.885328',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: Key.enter',
        'key': 'Key.enter',
        'screenshot_path': 'screenshots/action_0025.png',
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
    
    print(f"총 26개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (971, 261)'
    print(f'[1/26] ' + '클릭 (971, 261)')
    try:
        pyautogui.click(971, 261, button='left')
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

    # 액션 2: '2.6초 대기'
    print(f'[2/26] ' + '2.6초 대기')
    try:
        time.sleep(2.6)
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

    # 액션 3: '클릭 (757, 641)'
    print(f'[3/26] ' + '클릭 (757, 641)')
    try:
        pyautogui.click(757, 641, button='left')
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

    # 액션 4: '클릭 (757, 641)'
    print(f'[4/26] ' + '클릭 (757, 641)')
    try:
        pyautogui.click(757, 641, button='left')
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

    # 액션 5: '1.2초 대기'
    print(f'[5/26] ' + '1.2초 대기')
    try:
        time.sleep(1.2)
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

    # 액션 6: '클릭 (1032, 376)'
    print(f'[6/26] ' + '클릭 (1032, 376)')
    try:
        pyautogui.click(1032, 376, button='left')
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

    # 액션 7: '2.0초 대기'
    print(f'[7/26] ' + '2.0초 대기')
    try:
        time.sleep(2.0)
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

    # 액션 8: '클릭 (407, 220)'
    print(f'[8/26] ' + '클릭 (407, 220)')
    try:
        pyautogui.click(407, 220, button='left')
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

    # 액션 9: '1.3초 대기'
    print(f'[9/26] ' + '1.3초 대기')
    try:
        time.sleep(1.3)
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

    # 액션 10: '클릭 (325, 488)'
    print(f'[10/26] ' + '클릭 (325, 488)')
    try:
        pyautogui.click(325, 488, button='left')
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

    # 액션 11: '1.0초 대기'
    print(f'[11/26] ' + '1.0초 대기')
    try:
        time.sleep(1.0)
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

    # 액션 12: '클릭 (310, 633)'
    print(f'[12/26] ' + '클릭 (310, 633)')
    try:
        pyautogui.click(310, 633, button='left')
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

    # 액션 13: '클릭 (310, 633)'
    print(f'[13/26] ' + '클릭 (310, 633)')
    try:
        pyautogui.click(310, 633, button='left')
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

    # 액션 14: '1.5초 대기'
    print(f'[14/26] ' + '1.5초 대기')
    try:
        time.sleep(1.5)
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

    # 액션 15: '클릭 (289, 219)'
    print(f'[15/26] ' + '클릭 (289, 219)')
    try:
        pyautogui.click(289, 219, button='left')
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

    # 액션 16: '1.6초 대기'
    print(f'[16/26] ' + '1.6초 대기')
    try:
        time.sleep(1.6)
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

    # 액션 17: '클릭 (183, 218)'
    print(f'[17/26] ' + '클릭 (183, 218)')
    try:
        pyautogui.click(183, 218, button='left')
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

    # 액션 18: '1.3초 대기'
    print(f'[18/26] ' + '1.3초 대기')
    try:
        time.sleep(1.3)
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

    # 액션 19: '클릭 (833, 959)'
    print(f'[19/26] ' + '클릭 (833, 959)')
    try:
        pyautogui.click(833, 959, button='left')
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

    # 액션 20: '키 입력: s'
    print(f'[20/26] ' + '키 입력: s')
    try:
        pyautogui.write('s')
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
    print(f'[21/26] ' + '키 입력: o')
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

    # 액션 22: '키 입력: Key.backspace'
    print(f'[22/26] ' + '키 입력: Key.backspace')
    try:
        pyautogui.press('backspace')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[22] if 22 < len(ACTIONS) else None
            verifier.capture_and_verify(21, ACTIONS[21], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 23: '키 입력: t'
    print(f'[23/26] ' + '키 입력: t')
    try:
        pyautogui.write('t')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[23] if 23 < len(ACTIONS) else None
            verifier.capture_and_verify(22, ACTIONS[22], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 24: '키 입력: o'
    print(f'[24/26] ' + '키 입력: o')
    try:
        pyautogui.write('o')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[24] if 24 < len(ACTIONS) else None
            verifier.capture_and_verify(23, ACTIONS[23], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 25: '키 입력: p'
    print(f'[25/26] ' + '키 입력: p')
    try:
        pyautogui.write('p')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            next_action = ACTIONS[25] if 25 < len(ACTIONS) else None
            verifier.capture_and_verify(24, ACTIONS[24], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 26: '키 입력: Key.enter'
    print(f'[26/26] ' + '키 입력: Key.enter')
    try:
        pyautogui.press('enter')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            verifier.capture_and_verify(25, ACTIONS[25], None)
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
