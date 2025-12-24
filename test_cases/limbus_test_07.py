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
        'timestamp': '2025-12-24T00:47:23.064596',
        'action_type': 'click',
        'x': 966,
        'y': 279,
        'description': '클릭 (966, 279)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2025-12-24T00:47:25.937615',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '5.3초 대기',
        'wait_time': 5.3,
    },
    {
        'timestamp': '2025-12-24T00:47:31.210158',
        'action_type': 'click',
        'x': 784,
        'y': 643,
        'description': '클릭 (784, 643)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2025-12-24T00:47:33.581110',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '7.0초 대기',
        'wait_time': 7.0,
    },
    {
        'timestamp': '2025-12-24T00:47:40.547597',
        'action_type': 'click',
        'x': 1015,
        'y': 369,
        'description': '클릭 (1015, 369)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0002.png',
    },
    {
        'timestamp': '2025-12-24T00:47:42.887362',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '5.8초 대기',
        'wait_time': 5.8,
    },
    {
        'timestamp': '2025-12-24T00:47:48.662321',
        'action_type': 'click',
        'x': 405,
        'y': 216,
        'description': '클릭 (405, 216)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0003.png',
    },
    {
        'timestamp': '2025-12-24T00:47:50.983773',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.8초 대기',
        'wait_time': 3.8,
    },
    {
        'timestamp': '2025-12-24T00:47:54.827477',
        'action_type': 'click',
        'x': 311,
        'y': 523,
        'description': '클릭 (311, 523)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0004.png',
    },
    {
        'timestamp': '2025-12-24T00:47:57.130368',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.4초 대기',
        'wait_time': 4.4,
    },
    {
        'timestamp': '2025-12-24T00:48:01.510144',
        'action_type': 'click',
        'x': 320,
        'y': 645,
        'description': '클릭 (320, 645)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0005.png',
    },
    {
        'timestamp': '2025-12-24T00:48:03.735688',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.1초 대기',
        'wait_time': 4.1,
    },
    {
        'timestamp': '2025-12-24T00:48:07.849786',
        'action_type': 'click',
        'x': 153,
        'y': 238,
        'description': '클릭 (153, 238)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0006.png',
    },
    {
        'timestamp': '2025-12-24T00:48:10.195613',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '0.9초 대기',
        'wait_time': 0.9,
    },
]

def replay_actions(action_delay=0.5, verify=False, test_case_name="unknown", skip_wait=True):
    """액션을 순서대로 재실행
    
    Args:
        action_delay: 액션 간 지연 시간 (초)
        verify: 검증 모드 활성화 여부
        test_case_name: 테스트 케이스 이름 (검증 모드용)
        skip_wait: 검증 모드에서 대기 액션 건너뛰기 (기본: True)
    """
    verifier = None
    
    # 검증 모드 초기화
    if verify and VERIFY_AVAILABLE:
        config = ConfigManager()
        config.load_config()
        verifier = ReplayVerifier(config)
        verifier.start_verification_session(test_case_name)
        print("✓ 검증 모드 활성화")
        if skip_wait:
            print("✓ 빠른 검증 모드: 대기 시간 건너뛰기")
        else:
            print("✓ 전체 재현 모드: 대기 시간 포함")
    elif verify and not VERIFY_AVAILABLE:
        print("⚠ 검증 모듈을 로드할 수 없습니다. 검증 없이 진행합니다.")
    
    print(f"총 14개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (966, 279)'
    print(f'[1/14] ' + '클릭 (966, 279)')
    try:
        pyautogui.click(966, 279, button='left')
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

    # 액션 2: '5.3초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[2/14] ' + '5.3초 대기 (건너뜀)')
    else:
        print(f'[2/14] ' + '5.3초 대기')
        try:
            time.sleep(5.3)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 3: '클릭 (784, 643)'
    print(f'[3/14] ' + '클릭 (784, 643)')
    try:
        pyautogui.click(784, 643, button='left')
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

    # 액션 4: '7.0초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[4/14] ' + '7.0초 대기 (건너뜀)')
    else:
        print(f'[4/14] ' + '7.0초 대기')
        try:
            time.sleep(7.0)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 5: '클릭 (1015, 369)'
    print(f'[5/14] ' + '클릭 (1015, 369)')
    try:
        pyautogui.click(1015, 369, button='left')
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

    # 액션 6: '5.8초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[6/14] ' + '5.8초 대기 (건너뜀)')
    else:
        print(f'[6/14] ' + '5.8초 대기')
        try:
            time.sleep(5.8)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 7: '클릭 (405, 216)'
    print(f'[7/14] ' + '클릭 (405, 216)')
    try:
        pyautogui.click(405, 216, button='left')
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

    # 액션 8: '3.8초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[8/14] ' + '3.8초 대기 (건너뜀)')
    else:
        print(f'[8/14] ' + '3.8초 대기')
        try:
            time.sleep(3.8)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 9: '클릭 (311, 523)'
    print(f'[9/14] ' + '클릭 (311, 523)')
    try:
        pyautogui.click(311, 523, button='left')
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

    # 액션 10: '4.4초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[10/14] ' + '4.4초 대기 (건너뜀)')
    else:
        print(f'[10/14] ' + '4.4초 대기')
        try:
            time.sleep(4.4)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 11: '클릭 (320, 645)'
    print(f'[11/14] ' + '클릭 (320, 645)')
    try:
        pyautogui.click(320, 645, button='left')
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

    # 액션 12: '4.1초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[12/14] ' + '4.1초 대기 (건너뜀)')
    else:
        print(f'[12/14] ' + '4.1초 대기')
        try:
            time.sleep(4.1)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 13: '클릭 (153, 238)'
    print(f'[13/14] ' + '클릭 (153, 238)')
    try:
        pyautogui.click(153, 238, button='left')
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
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[14/14] ' + '0.9초 대기 (건너뜀)')
    else:
        print(f'[14/14] ' + '0.9초 대기')
        try:
            time.sleep(0.9)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
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
    parser.add_argument('--full-replay', action='store_true', help='전체 재현 모드 (대기 시간 포함)')
    parser.add_argument('--name', type=str, default='unknown', help='테스트 케이스 이름')
    
    args = parser.parse_args()
    
    # 테스트 케이스 이름 자동 추출 (파일명에서)
    if args.name == 'unknown':
        import os
        args.name = os.path.splitext(os.path.basename(__file__))[0]
    
    # skip_wait: 검증 모드에서 기본 True, --full-replay 옵션 시 False
    skip_wait = not args.full_replay
    
    # 액션 재실행
    replay_actions(action_delay=args.delay, verify=args.verify, test_case_name=args.name, skip_wait=skip_wait)
