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
        'timestamp': '2025-12-23T23:44:31.265083',
        'action_type': 'click',
        'x': 982,
        'y': 265,
        'description': '클릭 (982, 265)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2025-12-23T23:44:31.478463',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '5.5초 대기',
        'wait_time': 5.5,
    },
    {
        'timestamp': '2025-12-23T23:44:36.717116',
        'action_type': 'click',
        'x': 756,
        'y': 637,
        'description': '클릭 (756, 637)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2025-12-23T23:44:36.956233',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.3초 대기',
        'wait_time': 3.3,
    },
    {
        'timestamp': '2025-12-23T23:44:40.069395',
        'action_type': 'click',
        'x': 1023,
        'y': 367,
        'description': '클릭 (1023, 367)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0003.png',
    },
    {
        'timestamp': '2025-12-23T23:44:40.267862',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '7.4초 대기',
        'wait_time': 7.4,
    },
    {
        'timestamp': '2025-12-23T23:44:47.457070',
        'action_type': 'click',
        'x': 384,
        'y': 229,
        'description': '클릭 (384, 229)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0005.png',
    },
    {
        'timestamp': '2025-12-23T23:44:47.716343',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.0초 대기',
        'wait_time': 2.0,
    },
    {
        'timestamp': '2025-12-23T23:44:49.556856',
        'action_type': 'click',
        'x': 301,
        'y': 229,
        'description': '클릭 (301, 229)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0007.png',
    },
    {
        'timestamp': '2025-12-23T23:44:49.702454',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.3초 대기',
        'wait_time': 1.3,
    },
    {
        'timestamp': '2025-12-23T23:44:50.779249',
        'action_type': 'click',
        'x': 155,
        'y': 224,
        'description': '클릭 (155, 224)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0009.png',
    },
    {
        'timestamp': '2025-12-23T23:44:50.993491',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.1초 대기',
        'wait_time': 2.1,
    },
    {
        'timestamp': '2025-12-23T23:44:52.924372',
        'action_type': 'click',
        'x': 596,
        'y': 976,
        'description': '클릭 (596, 976)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0011.png',
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
    
    print(f"총 13개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (982, 265)'
    print(f'[1/13] ' + '클릭 (982, 265)')
    try:
        pyautogui.click(982, 265, button='left')
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

    # 액션 2: '5.5초 대기'
    print(f'[2/13] ' + '5.5초 대기')
    try:
        time.sleep(5.5)
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

    # 액션 3: '클릭 (756, 637)'
    print(f'[3/13] ' + '클릭 (756, 637)')
    try:
        pyautogui.click(756, 637, button='left')
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

    # 액션 4: '3.3초 대기'
    print(f'[4/13] ' + '3.3초 대기')
    try:
        time.sleep(3.3)
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

    # 액션 5: '클릭 (1023, 367)'
    print(f'[5/13] ' + '클릭 (1023, 367)')
    try:
        pyautogui.click(1023, 367, button='left')
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

    # 액션 6: '7.4초 대기'
    print(f'[6/13] ' + '7.4초 대기')
    try:
        time.sleep(7.4)
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

    # 액션 7: '클릭 (384, 229)'
    print(f'[7/13] ' + '클릭 (384, 229)')
    try:
        pyautogui.click(384, 229, button='left')
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

    # 액션 8: '2.0초 대기'
    print(f'[8/13] ' + '2.0초 대기')
    try:
        time.sleep(2.0)
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

    # 액션 9: '클릭 (301, 229)'
    print(f'[9/13] ' + '클릭 (301, 229)')
    try:
        pyautogui.click(301, 229, button='left')
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

    # 액션 10: '1.3초 대기'
    print(f'[10/13] ' + '1.3초 대기')
    try:
        time.sleep(1.3)
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

    # 액션 11: '클릭 (155, 224)'
    print(f'[11/13] ' + '클릭 (155, 224)')
    try:
        pyautogui.click(155, 224, button='left')
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

    # 액션 12: '2.1초 대기'
    print(f'[12/13] ' + '2.1초 대기')
    try:
        time.sleep(2.1)
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

    # 액션 13: '클릭 (596, 976)'
    print(f'[13/13] ' + '클릭 (596, 976)')
    try:
        pyautogui.click(596, 976, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            verifier.capture_and_verify(12, ACTIONS[12], None)
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
