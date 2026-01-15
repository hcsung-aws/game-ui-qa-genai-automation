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
        'timestamp': '2026-01-06T12:58:29.797800',
        'action_type': 'click',
        'x': 476,
        'y': 362,
        'description': '클릭 (476, 362)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2026-01-06T12:58:32.305807',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.5초 대기',
        'wait_time': 1.5,
    },
    {
        'timestamp': '2026-01-06T12:58:33.762998',
        'action_type': 'click',
        'x': 67,
        'y': 63,
        'description': '클릭 (67, 63)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2026-01-06T12:58:36.401921',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.6초 대기',
        'wait_time': 1.6,
    },
    {
        'timestamp': '2026-01-06T12:58:38.046218',
        'action_type': 'click',
        'x': 94,
        'y': 228,
        'description': '클릭 (94, 228)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0002.png',
    },
    {
        'timestamp': '2026-01-06T12:58:40.671580',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.7초 대기',
        'wait_time': 1.7,
    },
    {
        'timestamp': '2026-01-06T12:58:42.399477',
        'action_type': 'click',
        'x': 378,
        'y': 139,
        'description': '클릭 (378, 139)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0003.png',
    },
    {
        'timestamp': '2026-01-06T12:58:44.843799',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.9초 대기',
        'wait_time': 2.9,
    },
    {
        'timestamp': '2026-01-06T12:58:47.759423',
        'action_type': 'click',
        'x': 629,
        'y': 145,
        'description': '클릭 (629, 145)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0004.png',
    },
    {
        'timestamp': '2026-01-06T12:58:50.318280',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.7초 대기',
        'wait_time': 3.7,
    },
    {
        'timestamp': '2026-01-06T12:58:53.978369',
        'action_type': 'click',
        'x': 848,
        'y': 146,
        'description': '클릭 (848, 146)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0005.png',
    },
    {
        'timestamp': '2026-01-06T12:58:56.454851',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.2초 대기',
        'wait_time': 3.2,
    },
    {
        'timestamp': '2026-01-06T12:58:59.645879',
        'action_type': 'click',
        'x': 1000,
        'y': 149,
        'description': '클릭 (1000, 149)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0006.png',
    },
    {
        'timestamp': '2026-01-06T12:59:02.215302',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.3초 대기',
        'wait_time': 3.3,
    },
    {
        'timestamp': '2026-01-06T12:59:05.497698',
        'action_type': 'click',
        'x': 53,
        'y': 351,
        'description': '클릭 (53, 351)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0007.png',
    },
    {
        'timestamp': '2026-01-06T12:59:08.206858',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.0초 대기',
        'wait_time': 3.0,
    },
    {
        'timestamp': '2026-01-06T12:59:11.212685',
        'action_type': 'click',
        'x': 192,
        'y': 447,
        'description': '클릭 (192, 447)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0008.png',
    },
    {
        'timestamp': '2026-01-06T12:59:14.149503',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.9초 대기',
        'wait_time': 1.9,
    },
    {
        'timestamp': '2026-01-06T12:59:16.036048',
        'action_type': 'click',
        'x': 67,
        'y': 64,
        'description': '클릭 (67, 64)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0009.png',
    },
    {
        'timestamp': '2026-01-06T12:59:19.021136',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.2초 대기',
        'wait_time': 1.2,
    },
    {
        'timestamp': '2026-01-06T12:59:19.021136',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.2초 대기',
        'wait_time': 1.2,
    },
    {
        'timestamp': '2026-01-06T12:59:20.252559',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: s',
        'key': 's',
        'screenshot_path': 'screenshots/action_0010.png',
    },
    {
        'timestamp': '2026-01-06T12:59:20.196504',
        'action_type': 'click',
        'x': 2135,
        'y': 1062,
        'description': '클릭 (2135, 1062)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0010.png',
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
    
    print(f"총 23개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (476, 362)'
    print(f'[1/23] ' + '클릭 (476, 362)')
    try:
        pyautogui.click(476, 362, button='left')
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

    # 액션 2: '1.5초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[2/23] ' + '1.5초 대기' + ' (건너뜀)')
    else:
        print(f'[2/23] ' + '1.5초 대기')
        try:
            time.sleep(1.5)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 3: '클릭 (67, 63)'
    print(f'[3/23] ' + '클릭 (67, 63)')
    try:
        pyautogui.click(67, 63, button='left')
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

    # 액션 4: '1.6초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[4/23] ' + '1.6초 대기' + ' (건너뜀)')
    else:
        print(f'[4/23] ' + '1.6초 대기')
        try:
            time.sleep(1.6)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 5: '클릭 (94, 228)'
    print(f'[5/23] ' + '클릭 (94, 228)')
    try:
        pyautogui.click(94, 228, button='left')
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

    # 액션 6: '1.7초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[6/23] ' + '1.7초 대기' + ' (건너뜀)')
    else:
        print(f'[6/23] ' + '1.7초 대기')
        try:
            time.sleep(1.7)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 7: '클릭 (378, 139)'
    print(f'[7/23] ' + '클릭 (378, 139)')
    try:
        pyautogui.click(378, 139, button='left')
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
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[8/23] ' + '2.9초 대기' + ' (건너뜀)')
    else:
        print(f'[8/23] ' + '2.9초 대기')
        try:
            time.sleep(2.9)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 9: '클릭 (629, 145)'
    print(f'[9/23] ' + '클릭 (629, 145)')
    try:
        pyautogui.click(629, 145, button='left')
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

    # 액션 10: '3.7초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[10/23] ' + '3.7초 대기' + ' (건너뜀)')
    else:
        print(f'[10/23] ' + '3.7초 대기')
        try:
            time.sleep(3.7)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 11: '클릭 (848, 146)'
    print(f'[11/23] ' + '클릭 (848, 146)')
    try:
        pyautogui.click(848, 146, button='left')
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

    # 액션 12: '3.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[12/23] ' + '3.2초 대기' + ' (건너뜀)')
    else:
        print(f'[12/23] ' + '3.2초 대기')
        try:
            time.sleep(3.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 13: '클릭 (1000, 149)'
    print(f'[13/23] ' + '클릭 (1000, 149)')
    try:
        pyautogui.click(1000, 149, button='left')
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

    # 액션 14: '3.3초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[14/23] ' + '3.3초 대기' + ' (건너뜀)')
    else:
        print(f'[14/23] ' + '3.3초 대기')
        try:
            time.sleep(3.3)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 15: '클릭 (53, 351)'
    print(f'[15/23] ' + '클릭 (53, 351)')
    try:
        pyautogui.click(53, 351, button='left')
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

    # 액션 16: '3.0초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[16/23] ' + '3.0초 대기' + ' (건너뜀)')
    else:
        print(f'[16/23] ' + '3.0초 대기')
        try:
            time.sleep(3.0)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 17: '클릭 (192, 447)'
    print(f'[17/23] ' + '클릭 (192, 447)')
    try:
        pyautogui.click(192, 447, button='left')
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

    # 액션 18: '1.9초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[18/23] ' + '1.9초 대기' + ' (건너뜀)')
    else:
        print(f'[18/23] ' + '1.9초 대기')
        try:
            time.sleep(1.9)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 19: '클릭 (67, 64)'
    print(f'[19/23] ' + '클릭 (67, 64)')
    try:
        pyautogui.click(67, 64, button='left')
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

    # 액션 20: '1.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[20/23] ' + '1.2초 대기' + ' (건너뜀)')
    else:
        print(f'[20/23] ' + '1.2초 대기')
        try:
            time.sleep(1.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 21: '1.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[21/23] ' + '1.2초 대기' + ' (건너뜀)')
    else:
        print(f'[21/23] ' + '1.2초 대기')
        try:
            time.sleep(1.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 22: '키 입력: s'
    print(f'[22/23] ' + '키 입력: s')
    try:
        pyautogui.write('s')
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

    # 액션 23: '클릭 (2135, 1062)'
    print(f'[23/23] ' + '클릭 (2135, 1062)')
    try:
        pyautogui.click(2135, 1062, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: 스크린샷 검증
        if verifier:
            verifier.capture_and_verify(22, ACTIONS[22], None)
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
