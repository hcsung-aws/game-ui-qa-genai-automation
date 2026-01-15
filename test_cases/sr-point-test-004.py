#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
자동 생성된 Replay Script

이 스크립트는 기록된 액션을 재실행합니다.
--verify 옵션으로 검증 모드를 활성화할 수 있습니다.

좌표는 게임 윈도우 기준 상대 좌표로 저장되어 있으며,
재현 시 윈도우 위치를 감지하여 스크린 절대 좌표로 변환합니다.
"""

import pyautogui
import time
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 윈도우 좌표 변환용 임포트
try:
    from src.window_capture import WindowCapture
    WINDOW_CAPTURE_AVAILABLE = True
except ImportError:
    WINDOW_CAPTURE_AVAILABLE = False

# 게임 윈도우 타이틀
GAME_WINDOW_TITLE = 'Seven Knights : Rebirth'

# 윈도우 오프셋 캐시
_window_offset = None

def get_window_offset():
    """게임 윈도우의 스크린 오프셋 가져오기
    
    Returns:
        (offset_x, offset_y) 튜플
    """
    global _window_offset
    
    if _window_offset is not None:
        return _window_offset
    
    if WINDOW_CAPTURE_AVAILABLE and GAME_WINDOW_TITLE:
        try:
            wc = WindowCapture(GAME_WINDOW_TITLE)
            if wc.find_window():
                rect = wc.get_window_rect()
                if rect:
                    _window_offset = (rect[0], rect[1])
                    return _window_offset
        except Exception as e:
            print(f"⚠ 윈도우 오프셋 가져오기 실패: {e}")
    
    _window_offset = (0, 0)
    return _window_offset

def to_screen_coords(window_x, window_y):
    """윈도우 상대 좌표를 스크린 절대 좌표로 변환
    
    Args:
        window_x: 윈도우 기준 X 좌표
        window_y: 윈도우 기준 Y 좌표
        
    Returns:
        (screen_x, screen_y) 스크린 절대 좌표
    """
    offset_x, offset_y = get_window_offset()
    return (window_x + offset_x, window_y + offset_y)


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
        'timestamp': '2026-01-15T00:17:13.101799',
        'action_type': 'click',
        'x': 487,
        'y': 371,
        'description': '클릭 (487, 371)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2026-01-15T00:17:15.411112',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.3초 대기',
        'wait_time': 1.3,
    },
    {
        'timestamp': '2026-01-15T00:17:16.704340',
        'action_type': 'click',
        'x': 74,
        'y': 66,
        'description': '클릭 (74, 66)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2026-01-15T00:17:19.142552',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.1초 대기',
        'wait_time': 1.1,
    },
    {
        'timestamp': '2026-01-15T00:17:20.288622',
        'action_type': 'click',
        'x': 83,
        'y': 203,
        'description': '클릭 (83, 203)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0002.png',
    },
    {
        'timestamp': '2026-01-15T00:17:22.584714',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.1초 대기',
        'wait_time': 1.1,
    },
    {
        'timestamp': '2026-01-15T00:17:23.690086',
        'action_type': 'click',
        'x': 409,
        'y': 134,
        'description': '클릭 (409, 134)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0003.png',
    },
    {
        'timestamp': '2026-01-15T00:17:26.263348',
        'action_type': 'click',
        'x': 716,
        'y': 131,
        'description': '클릭 (716, 131)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0004.png',
    },
    {
        'timestamp': '2026-01-15T00:17:28.541024',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.4초 대기',
        'wait_time': 1.4,
    },
    {
        'timestamp': '2026-01-15T00:17:29.903817',
        'action_type': 'click',
        'x': 669,
        'y': 137,
        'description': '클릭 (669, 137)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0005.png',
    },
    {
        'timestamp': '2026-01-15T00:17:32.252385',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.0초 대기',
        'wait_time': 1.0,
    },
    {
        'timestamp': '2026-01-15T00:17:33.244832',
        'action_type': 'click',
        'x': 1011,
        'y': 138,
        'description': '클릭 (1011, 138)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0006.png',
    },
    {
        'timestamp': '2026-01-15T00:17:35.648567',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.2초 대기',
        'wait_time': 1.2,
    },
    {
        'timestamp': '2026-01-15T00:17:36.882082',
        'action_type': 'click',
        'x': 173,
        'y': 321,
        'description': '클릭 (173, 321)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0007.png',
    },
    {
        'timestamp': '2026-01-15T00:17:39.206246',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '0.8초 대기',
        'wait_time': 0.8,
    },
    {
        'timestamp': '2026-01-15T00:17:39.977238',
        'action_type': 'click',
        'x': 149,
        'y': 451,
        'description': '클릭 (149, 451)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0008.png',
    },
    {
        'timestamp': '2026-01-15T00:17:42.355987',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.1초 대기',
        'wait_time': 1.1,
    },
    {
        'timestamp': '2026-01-15T00:17:43.447108',
        'action_type': 'click',
        'x': 158,
        'y': 495,
        'description': '클릭 (158, 495)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0009.png',
    },
    {
        'timestamp': '2026-01-15T00:17:45.743243',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.3초 대기',
        'wait_time': 1.3,
    },
    {
        'timestamp': '2026-01-15T00:17:47.046433',
        'action_type': 'click',
        'x': 69,
        'y': 61,
        'description': '클릭 (69, 61)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0010.png',
    },
    {
        'timestamp': '2026-01-15T00:17:49.458882',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '0.8초 대기',
        'wait_time': 0.8,
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
    
    # 윈도우 오프셋 미리 가져오기
    offset_x, offset_y = get_window_offset()
    if offset_x != 0 or offset_y != 0:
        print(f"✓ 게임 윈도우 감지: 오프셋 ({offset_x}, {offset_y})")
    else:
        print("⚠ 게임 윈도우를 찾지 못했습니다. 좌표가 정확하지 않을 수 있습니다.")
    
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
    
    # 액션 1: '클릭 (487, 371)'
    print(f'[1/21] ' + '클릭 (487, 371)')
    try:
        screen_x, screen_y = to_screen_coords(487, 371); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 2: '1.3초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[2/21] ' + '1.3초 대기' + ' (건너뜀)')
    else:
        print(f'[2/21] ' + '1.3초 대기')
        try:
            time.sleep(1.3)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 3: '클릭 (74, 66)'
    print(f'[3/21] ' + '클릭 (74, 66)')
    try:
        screen_x, screen_y = to_screen_coords(74, 66); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 4: '1.1초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[4/21] ' + '1.1초 대기' + ' (건너뜀)')
    else:
        print(f'[4/21] ' + '1.1초 대기')
        try:
            time.sleep(1.1)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 5: '클릭 (83, 203)'
    print(f'[5/21] ' + '클릭 (83, 203)')
    try:
        screen_x, screen_y = to_screen_coords(83, 203); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 6: '1.1초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[6/21] ' + '1.1초 대기' + ' (건너뜀)')
    else:
        print(f'[6/21] ' + '1.1초 대기')
        try:
            time.sleep(1.1)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 7: '클릭 (409, 134)'
    print(f'[7/21] ' + '클릭 (409, 134)')
    try:
        screen_x, screen_y = to_screen_coords(409, 134); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 8: '클릭 (716, 131)'
    print(f'[8/21] ' + '클릭 (716, 131)')
    try:
        screen_x, screen_y = to_screen_coords(716, 131); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 9: '1.4초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[9/21] ' + '1.4초 대기' + ' (건너뜀)')
    else:
        print(f'[9/21] ' + '1.4초 대기')
        try:
            time.sleep(1.4)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 10: '클릭 (669, 137)'
    print(f'[10/21] ' + '클릭 (669, 137)')
    try:
        screen_x, screen_y = to_screen_coords(669, 137); pyautogui.click(screen_x, screen_y, button='left')
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
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[11/21] ' + '1.0초 대기' + ' (건너뜀)')
    else:
        print(f'[11/21] ' + '1.0초 대기')
        try:
            time.sleep(1.0)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 12: '클릭 (1011, 138)'
    print(f'[12/21] ' + '클릭 (1011, 138)')
    try:
        screen_x, screen_y = to_screen_coords(1011, 138); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 13: '1.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[13/21] ' + '1.2초 대기' + ' (건너뜀)')
    else:
        print(f'[13/21] ' + '1.2초 대기')
        try:
            time.sleep(1.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 14: '클릭 (173, 321)'
    print(f'[14/21] ' + '클릭 (173, 321)')
    try:
        screen_x, screen_y = to_screen_coords(173, 321); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 15: '0.8초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[15/21] ' + '0.8초 대기' + ' (건너뜀)')
    else:
        print(f'[15/21] ' + '0.8초 대기')
        try:
            time.sleep(0.8)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 16: '클릭 (149, 451)'
    print(f'[16/21] ' + '클릭 (149, 451)')
    try:
        screen_x, screen_y = to_screen_coords(149, 451); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 17: '1.1초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[17/21] ' + '1.1초 대기' + ' (건너뜀)')
    else:
        print(f'[17/21] ' + '1.1초 대기')
        try:
            time.sleep(1.1)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 18: '클릭 (158, 495)'
    print(f'[18/21] ' + '클릭 (158, 495)')
    try:
        screen_x, screen_y = to_screen_coords(158, 495); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 19: '1.3초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[19/21] ' + '1.3초 대기' + ' (건너뜀)')
    else:
        print(f'[19/21] ' + '1.3초 대기')
        try:
            time.sleep(1.3)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 20: '클릭 (69, 61)'
    print(f'[20/21] ' + '클릭 (69, 61)')
    try:
        screen_x, screen_y = to_screen_coords(69, 61); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 21: '0.8초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[21/21] ' + '0.8초 대기' + ' (건너뜀)')
    else:
        print(f'[21/21] ' + '0.8초 대기')
        try:
            time.sleep(0.8)
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
