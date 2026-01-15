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
        'timestamp': '2026-01-15T00:11:04.060843',
        'action_type': 'click',
        'x': 480,
        'y': 373,
        'description': '클릭 (480, 373)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2026-01-15T00:11:06.373636',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.5초 대기',
        'wait_time': 1.5,
    },
    {
        'timestamp': '2026-01-15T00:11:07.831326',
        'action_type': 'click',
        'x': 65,
        'y': 62,
        'description': '클릭 (65, 62)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2026-01-15T00:11:10.215801',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.7초 대기',
        'wait_time': 1.7,
    },
    {
        'timestamp': '2026-01-15T00:11:11.899758',
        'action_type': 'click',
        'x': 93,
        'y': 214,
        'description': '클릭 (93, 214)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0002.png',
    },
    {
        'timestamp': '2026-01-15T00:11:14.189788',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.6초 대기',
        'wait_time': 1.6,
    },
    {
        'timestamp': '2026-01-15T00:11:15.763825',
        'action_type': 'click',
        'x': 417,
        'y': 135,
        'description': '클릭 (417, 135)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0003.png',
    },
    {
        'timestamp': '2026-01-15T00:11:18.054214',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.5초 대기',
        'wait_time': 1.5,
    },
    {
        'timestamp': '2026-01-15T00:11:19.521551',
        'action_type': 'click',
        'x': 646,
        'y': 142,
        'description': '클릭 (646, 142)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0004.png',
    },
    {
        'timestamp': '2026-01-15T00:11:21.869637',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.1초 대기',
        'wait_time': 1.1,
    },
    {
        'timestamp': '2026-01-15T00:11:22.962552',
        'action_type': 'click',
        'x': 841,
        'y': 142,
        'description': '클릭 (841, 142)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0005.png',
    },
    {
        'timestamp': '2026-01-15T00:11:25.382052',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.0초 대기',
        'wait_time': 1.0,
    },
    {
        'timestamp': '2026-01-15T00:11:26.343673',
        'action_type': 'click',
        'x': 1103,
        'y': 136,
        'description': '클릭 (1103, 136)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0006.png',
    },
    {
        'timestamp': '2026-01-15T00:11:28.698362',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.1초 대기',
        'wait_time': 1.1,
    },
    {
        'timestamp': '2026-01-15T00:11:29.775707',
        'action_type': 'click',
        'x': 138,
        'y': 294,
        'description': '클릭 (138, 294)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0007.png',
    },
    {
        'timestamp': '2026-01-15T00:11:32.241954',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '0.7초 대기',
        'wait_time': 0.7,
    },
    {
        'timestamp': '2026-01-15T00:11:32.956994',
        'action_type': 'click',
        'x': 142,
        'y': 422,
        'description': '클릭 (142, 422)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0008.png',
    },
    {
        'timestamp': '2026-01-15T00:11:35.316385',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.1초 대기',
        'wait_time': 1.1,
    },
    {
        'timestamp': '2026-01-15T00:11:36.397515',
        'action_type': 'click',
        'x': 138,
        'y': 501,
        'description': '클릭 (138, 501)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0009.png',
    },
    {
        'timestamp': '2026-01-15T00:11:38.652291',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.5초 대기',
        'wait_time': 1.5,
    },
    {
        'timestamp': '2026-01-15T00:11:40.181355',
        'action_type': 'click',
        'x': 75,
        'y': 76,
        'description': '클릭 (75, 76)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0010.png',
    },
    {
        'timestamp': '2026-01-15T00:11:42.598536',
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
    
    print(f"총 22개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (480, 373)'
    print(f'[1/22] ' + '클릭 (480, 373)')
    try:
        screen_x, screen_y = to_screen_coords(480, 373)
                pyautogui.click(screen_x, screen_y, button='left')
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
        print(f'[2/22] ' + '1.5초 대기' + ' (건너뜀)')
    else:
        print(f'[2/22] ' + '1.5초 대기')
        try:
            time.sleep(1.5)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 3: '클릭 (65, 62)'
    print(f'[3/22] ' + '클릭 (65, 62)')
    try:
        screen_x, screen_y = to_screen_coords(65, 62)
                pyautogui.click(screen_x, screen_y, button='left')
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
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[4/22] ' + '1.7초 대기' + ' (건너뜀)')
    else:
        print(f'[4/22] ' + '1.7초 대기')
        try:
            time.sleep(1.7)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 5: '클릭 (93, 214)'
    print(f'[5/22] ' + '클릭 (93, 214)')
    try:
        screen_x, screen_y = to_screen_coords(93, 214)
                pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 6: '1.6초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[6/22] ' + '1.6초 대기' + ' (건너뜀)')
    else:
        print(f'[6/22] ' + '1.6초 대기')
        try:
            time.sleep(1.6)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 7: '클릭 (417, 135)'
    print(f'[7/22] ' + '클릭 (417, 135)')
    try:
        screen_x, screen_y = to_screen_coords(417, 135)
                pyautogui.click(screen_x, screen_y, button='left')
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
        print(f'[8/22] ' + '1.5초 대기' + ' (건너뜀)')
    else:
        print(f'[8/22] ' + '1.5초 대기')
        try:
            time.sleep(1.5)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 9: '클릭 (646, 142)'
    print(f'[9/22] ' + '클릭 (646, 142)')
    try:
        screen_x, screen_y = to_screen_coords(646, 142)
                pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 10: '1.1초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[10/22] ' + '1.1초 대기' + ' (건너뜀)')
    else:
        print(f'[10/22] ' + '1.1초 대기')
        try:
            time.sleep(1.1)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 11: '클릭 (841, 142)'
    print(f'[11/22] ' + '클릭 (841, 142)')
    try:
        screen_x, screen_y = to_screen_coords(841, 142)
                pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 12: '1.0초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[12/22] ' + '1.0초 대기' + ' (건너뜀)')
    else:
        print(f'[12/22] ' + '1.0초 대기')
        try:
            time.sleep(1.0)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 13: '클릭 (1103, 136)'
    print(f'[13/22] ' + '클릭 (1103, 136)')
    try:
        screen_x, screen_y = to_screen_coords(1103, 136)
                pyautogui.click(screen_x, screen_y, button='left')
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
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[14/22] ' + '1.1초 대기' + ' (건너뜀)')
    else:
        print(f'[14/22] ' + '1.1초 대기')
        try:
            time.sleep(1.1)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 15: '클릭 (138, 294)'
    print(f'[15/22] ' + '클릭 (138, 294)')
    try:
        screen_x, screen_y = to_screen_coords(138, 294)
                pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 16: '0.7초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[16/22] ' + '0.7초 대기' + ' (건너뜀)')
    else:
        print(f'[16/22] ' + '0.7초 대기')
        try:
            time.sleep(0.7)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 17: '클릭 (142, 422)'
    print(f'[17/22] ' + '클릭 (142, 422)')
    try:
        screen_x, screen_y = to_screen_coords(142, 422)
                pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 18: '1.1초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[18/22] ' + '1.1초 대기' + ' (건너뜀)')
    else:
        print(f'[18/22] ' + '1.1초 대기')
        try:
            time.sleep(1.1)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 19: '클릭 (138, 501)'
    print(f'[19/22] ' + '클릭 (138, 501)')
    try:
        screen_x, screen_y = to_screen_coords(138, 501)
                pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 20: '1.5초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[20/22] ' + '1.5초 대기' + ' (건너뜀)')
    else:
        print(f'[20/22] ' + '1.5초 대기')
        try:
            time.sleep(1.5)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 21: '클릭 (75, 76)'
    print(f'[21/22] ' + '클릭 (75, 76)')
    try:
        screen_x, screen_y = to_screen_coords(75, 76)
                pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 22: '0.9초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[22/22] ' + '0.9초 대기' + ' (건너뜀)')
    else:
        print(f'[22/22] ' + '0.9초 대기')
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
