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
        'timestamp': '2026-01-14T23:53:00.735308',
        'action_type': 'click',
        'x': 469,
        'y': 377,
        'description': '클릭 (469, 377)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2026-01-14T23:53:03.037591',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.2초 대기',
        'wait_time': 1.2,
    },
    {
        'timestamp': '2026-01-14T23:53:04.278600',
        'action_type': 'click',
        'x': 76,
        'y': 61,
        'description': '클릭 (76, 61)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2026-01-14T23:53:06.901886',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.8초 대기',
        'wait_time': 1.8,
    },
    {
        'timestamp': '2026-01-14T23:53:08.731409',
        'action_type': 'click',
        'x': 83,
        'y': 214,
        'description': '클릭 (83, 214)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0002.png',
    },
    {
        'timestamp': '2026-01-14T23:53:11.023720',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.7초 대기',
        'wait_time': 2.7,
    },
    {
        'timestamp': '2026-01-14T23:53:13.703149',
        'action_type': 'click',
        'x': 424,
        'y': 153,
        'description': '클릭 (424, 153)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0003.png',
    },
    {
        'timestamp': '2026-01-14T23:53:15.996638',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.5초 대기',
        'wait_time': 1.5,
    },
    {
        'timestamp': '2026-01-14T23:53:17.478189',
        'action_type': 'click',
        'x': 643,
        'y': 143,
        'description': '클릭 (643, 143)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0004.png',
    },
    {
        'timestamp': '2026-01-14T23:53:19.950455',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.3초 대기',
        'wait_time': 1.3,
    },
    {
        'timestamp': '2026-01-14T23:53:21.282726',
        'action_type': 'click',
        'x': 873,
        'y': 150,
        'description': '클릭 (873, 150)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0005.png',
    },
    {
        'timestamp': '2026-01-14T23:53:23.790482',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '0.8초 대기',
        'wait_time': 0.8,
    },
    {
        'timestamp': '2026-01-14T23:53:24.601741',
        'action_type': 'click',
        'x': 977,
        'y': 151,
        'description': '클릭 (977, 151)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0006.png',
    },
    {
        'timestamp': '2026-01-14T23:53:26.988518',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.3초 대기',
        'wait_time': 1.3,
    },
    {
        'timestamp': '2026-01-14T23:53:28.251353',
        'action_type': 'click',
        'x': 181,
        'y': 355,
        'description': '클릭 (181, 355)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0007.png',
    },
    {
        'timestamp': '2026-01-14T23:53:31.105887',
        'action_type': 'click',
        'x': 164,
        'y': 426,
        'description': '클릭 (164, 426)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0008.png',
    },
    {
        'timestamp': '2026-01-14T23:53:33.506904',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.2초 대기',
        'wait_time': 1.2,
    },
    {
        'timestamp': '2026-01-14T23:53:34.686314',
        'action_type': 'click',
        'x': 146,
        'y': 500,
        'description': '클릭 (146, 500)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0009.png',
    },
    {
        'timestamp': '2026-01-14T23:53:36.995743',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.2초 대기',
        'wait_time': 1.2,
    },
    {
        'timestamp': '2026-01-14T23:53:38.165943',
        'action_type': 'click',
        'x': 69,
        'y': 54,
        'description': '클릭 (69, 54)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0010.png',
    },
    {
        'timestamp': '2026-01-14T23:53:40.604265',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.0초 대기',
        'wait_time': 1.0,
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
    
    print(f"총 21개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (469, 377)'
    print(f'[1/21] ' + '클릭 (469, 377)')
    try:
        pyautogui.click(469, 377, button='left')
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

    # 액션 2: '1.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[2/21] ' + '1.2초 대기' + ' (건너뜀)')
    else:
        print(f'[2/21] ' + '1.2초 대기')
        try:
            time.sleep(1.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 3: '클릭 (76, 61)'
    print(f'[3/21] ' + '클릭 (76, 61)')
    try:
        pyautogui.click(76, 61, button='left')
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

    # 액션 4: '1.8초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[4/21] ' + '1.8초 대기' + ' (건너뜀)')
    else:
        print(f'[4/21] ' + '1.8초 대기')
        try:
            time.sleep(1.8)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 5: '클릭 (83, 214)'
    print(f'[5/21] ' + '클릭 (83, 214)')
    try:
        pyautogui.click(83, 214, button='left')
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

    # 액션 6: '2.7초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[6/21] ' + '2.7초 대기' + ' (건너뜀)')
    else:
        print(f'[6/21] ' + '2.7초 대기')
        try:
            time.sleep(2.7)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 7: '클릭 (424, 153)'
    print(f'[7/21] ' + '클릭 (424, 153)')
    try:
        pyautogui.click(424, 153, button='left')
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

    # 액션 8: '1.5초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[8/21] ' + '1.5초 대기' + ' (건너뜀)')
    else:
        print(f'[8/21] ' + '1.5초 대기')
        try:
            time.sleep(1.5)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 9: '클릭 (643, 143)'
    print(f'[9/21] ' + '클릭 (643, 143)')
    try:
        pyautogui.click(643, 143, button='left')
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
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[10/21] ' + '1.3초 대기' + ' (건너뜀)')
    else:
        print(f'[10/21] ' + '1.3초 대기')
        try:
            time.sleep(1.3)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 11: '클릭 (873, 150)'
    print(f'[11/21] ' + '클릭 (873, 150)')
    try:
        pyautogui.click(873, 150, button='left')
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

    # 액션 12: '0.8초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[12/21] ' + '0.8초 대기' + ' (건너뜀)')
    else:
        print(f'[12/21] ' + '0.8초 대기')
        try:
            time.sleep(0.8)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 13: '클릭 (977, 151)'
    print(f'[13/21] ' + '클릭 (977, 151)')
    try:
        pyautogui.click(977, 151, button='left')
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
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[14/21] ' + '1.3초 대기' + ' (건너뜀)')
    else:
        print(f'[14/21] ' + '1.3초 대기')
        try:
            time.sleep(1.3)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 15: '클릭 (181, 355)'
    print(f'[15/21] ' + '클릭 (181, 355)')
    try:
        pyautogui.click(181, 355, button='left')
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

    # 액션 16: '클릭 (164, 426)'
    print(f'[16/21] ' + '클릭 (164, 426)')
    try:
        pyautogui.click(164, 426, button='left')
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

    # 액션 17: '1.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[17/21] ' + '1.2초 대기' + ' (건너뜀)')
    else:
        print(f'[17/21] ' + '1.2초 대기')
        try:
            time.sleep(1.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 18: '클릭 (146, 500)'
    print(f'[18/21] ' + '클릭 (146, 500)')
    try:
        pyautogui.click(146, 500, button='left')
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

    # 액션 19: '1.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[19/21] ' + '1.2초 대기' + ' (건너뜀)')
    else:
        print(f'[19/21] ' + '1.2초 대기')
        try:
            time.sleep(1.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 20: '클릭 (69, 54)'
    print(f'[20/21] ' + '클릭 (69, 54)')
    try:
        pyautogui.click(69, 54, button='left')
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

    # 액션 21: '1.0초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[21/21] ' + '1.0초 대기' + ' (건너뜀)')
    else:
        print(f'[21/21] ' + '1.0초 대기')
        try:
            time.sleep(1.0)
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
