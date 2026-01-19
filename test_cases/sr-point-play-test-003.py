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

# 녹화 시점의 스크린샷 캡처 대기 시간 (검증 시 동일하게 적용)
CAPTURE_DELAY = 2.0

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
        'timestamp': '2026-01-18T02:31:18.138054',
        'action_type': 'click',
        'x': 472,
        'y': 378,
        'description': '클릭 (472, 378)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0000.png',
    },
    {
        'timestamp': '2026-01-18T02:31:22.591498',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.2초 대기',
        'wait_time': 2.2,
    },
    {
        'timestamp': '2026-01-18T02:31:24.745603',
        'action_type': 'click',
        'x': 62,
        'y': 57,
        'description': '클릭 (62, 57)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0001.png',
    },
    {
        'timestamp': '2026-01-18T02:31:30.203584',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.5초 대기',
        'wait_time': 4.5,
    },
    {
        'timestamp': '2026-01-18T02:31:34.753431',
        'action_type': 'click',
        'x': 96,
        'y': 235,
        'description': '클릭 (96, 235)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0002.png',
    },
    {
        'timestamp': '2026-01-18T02:31:37.352705',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.7초 대기',
        'wait_time': 3.7,
    },
    {
        'timestamp': '2026-01-18T02:31:41.072280',
        'action_type': 'click',
        'x': 370,
        'y': 150,
        'description': '클릭 (370, 150)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0003.png',
    },
    {
        'timestamp': '2026-01-18T02:31:43.234526',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '6.7초 대기',
        'wait_time': 6.7,
    },
    {
        'timestamp': '2026-01-18T02:31:49.915485',
        'action_type': 'click',
        'x': 496,
        'y': 132,
        'description': '클릭 (496, 132)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0004.png',
    },
    {
        'timestamp': '2026-01-18T02:31:52.216169',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '6.3초 대기',
        'wait_time': 6.3,
    },
    {
        'timestamp': '2026-01-18T02:31:58.495677',
        'action_type': 'click',
        'x': 851,
        'y': 138,
        'description': '클릭 (851, 138)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0005.png',
    },
    {
        'timestamp': '2026-01-18T02:32:00.761692',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '6.2초 대기',
        'wait_time': 6.2,
    },
    {
        'timestamp': '2026-01-18T02:32:06.989368',
        'action_type': 'click',
        'x': 1129,
        'y': 150,
        'description': '클릭 (1129, 150)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0006.png',
    },
    {
        'timestamp': '2026-01-18T02:32:09.273758',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '6.4초 대기',
        'wait_time': 6.4,
    },
    {
        'timestamp': '2026-01-18T02:32:15.645874',
        'action_type': 'click',
        'x': 193,
        'y': 333,
        'description': '클릭 (193, 333)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0007.png',
    },
    {
        'timestamp': '2026-01-18T02:32:17.956933',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.2초 대기',
        'wait_time': 4.2,
    },
    {
        'timestamp': '2026-01-18T02:32:22.131559',
        'action_type': 'click',
        'x': 135,
        'y': 446,
        'description': '클릭 (135, 446)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0008.png',
    },
    {
        'timestamp': '2026-01-18T02:32:24.372530',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.6초 대기',
        'wait_time': 4.6,
    },
    {
        'timestamp': '2026-01-18T02:32:28.994514',
        'action_type': 'click',
        'x': 172,
        'y': 521,
        'description': '클릭 (172, 521)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0009.png',
    },
    {
        'timestamp': '2026-01-18T02:32:31.367604',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '5.2초 대기',
        'wait_time': 5.2,
    },
    {
        'timestamp': '2026-01-18T02:32:36.584178',
        'action_type': 'click',
        'x': 86,
        'y': 65,
        'description': '클릭 (86, 65)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0010.png',
    },
    {
        'timestamp': '2026-01-18T02:32:38.852705',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '5.4초 대기',
        'wait_time': 5.4,
    },
    {
        'timestamp': '2026-01-18T02:32:38.852705',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '5.9초 대기',
        'wait_time': 5.9,
    },
    {
        'timestamp': '2026-01-18T02:32:44.206223',
        'action_type': 'click',
        'x': 1637,
        'y': 778,
        'description': '클릭 (1637, 778)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0011.png',
    },
    {
        'timestamp': '2026-01-18T02:32:44.744248',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: s',
        'key': 's',
        'screenshot_path': 'screenshots\sr-point-play-test-003/action_0012.png',
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
    
    print(f"총 25개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (472, 378)'
    print(f'[1/25] ' + '클릭 (472, 378)')
    try:
        screen_x, screen_y = to_screen_coords(472, 378); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[1] if 1 < len(ACTIONS) else None
            verifier.capture_and_verify(0, ACTIONS[0], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 2: '2.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[2/25] ' + '2.2초 대기' + ' (건너뜀)')
    else:
        print(f'[2/25] ' + '2.2초 대기')
        try:
            time.sleep(2.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 3: '클릭 (62, 57)'
    print(f'[3/25] ' + '클릭 (62, 57)')
    try:
        screen_x, screen_y = to_screen_coords(62, 57); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[3] if 3 < len(ACTIONS) else None
            verifier.capture_and_verify(2, ACTIONS[2], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 4: '4.5초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[4/25] ' + '4.5초 대기' + ' (건너뜀)')
    else:
        print(f'[4/25] ' + '4.5초 대기')
        try:
            time.sleep(4.5)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 5: '클릭 (96, 235)'
    print(f'[5/25] ' + '클릭 (96, 235)')
    try:
        screen_x, screen_y = to_screen_coords(96, 235); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[5] if 5 < len(ACTIONS) else None
            verifier.capture_and_verify(4, ACTIONS[4], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 6: '3.7초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[6/25] ' + '3.7초 대기' + ' (건너뜀)')
    else:
        print(f'[6/25] ' + '3.7초 대기')
        try:
            time.sleep(3.7)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 7: '클릭 (370, 150)'
    print(f'[7/25] ' + '클릭 (370, 150)')
    try:
        screen_x, screen_y = to_screen_coords(370, 150); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[7] if 7 < len(ACTIONS) else None
            verifier.capture_and_verify(6, ACTIONS[6], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 8: '6.7초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[8/25] ' + '6.7초 대기' + ' (건너뜀)')
    else:
        print(f'[8/25] ' + '6.7초 대기')
        try:
            time.sleep(6.7)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 9: '클릭 (496, 132)'
    print(f'[9/25] ' + '클릭 (496, 132)')
    try:
        screen_x, screen_y = to_screen_coords(496, 132); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[9] if 9 < len(ACTIONS) else None
            verifier.capture_and_verify(8, ACTIONS[8], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 10: '6.3초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[10/25] ' + '6.3초 대기' + ' (건너뜀)')
    else:
        print(f'[10/25] ' + '6.3초 대기')
        try:
            time.sleep(6.3)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 11: '클릭 (851, 138)'
    print(f'[11/25] ' + '클릭 (851, 138)')
    try:
        screen_x, screen_y = to_screen_coords(851, 138); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[11] if 11 < len(ACTIONS) else None
            verifier.capture_and_verify(10, ACTIONS[10], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 12: '6.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[12/25] ' + '6.2초 대기' + ' (건너뜀)')
    else:
        print(f'[12/25] ' + '6.2초 대기')
        try:
            time.sleep(6.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 13: '클릭 (1129, 150)'
    print(f'[13/25] ' + '클릭 (1129, 150)')
    try:
        screen_x, screen_y = to_screen_coords(1129, 150); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[13] if 13 < len(ACTIONS) else None
            verifier.capture_and_verify(12, ACTIONS[12], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 14: '6.4초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[14/25] ' + '6.4초 대기' + ' (건너뜀)')
    else:
        print(f'[14/25] ' + '6.4초 대기')
        try:
            time.sleep(6.4)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 15: '클릭 (193, 333)'
    print(f'[15/25] ' + '클릭 (193, 333)')
    try:
        screen_x, screen_y = to_screen_coords(193, 333); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[15] if 15 < len(ACTIONS) else None
            verifier.capture_and_verify(14, ACTIONS[14], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 16: '4.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[16/25] ' + '4.2초 대기' + ' (건너뜀)')
    else:
        print(f'[16/25] ' + '4.2초 대기')
        try:
            time.sleep(4.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 17: '클릭 (135, 446)'
    print(f'[17/25] ' + '클릭 (135, 446)')
    try:
        screen_x, screen_y = to_screen_coords(135, 446); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[17] if 17 < len(ACTIONS) else None
            verifier.capture_and_verify(16, ACTIONS[16], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 18: '4.6초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[18/25] ' + '4.6초 대기' + ' (건너뜀)')
    else:
        print(f'[18/25] ' + '4.6초 대기')
        try:
            time.sleep(4.6)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 19: '클릭 (172, 521)'
    print(f'[19/25] ' + '클릭 (172, 521)')
    try:
        screen_x, screen_y = to_screen_coords(172, 521); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[19] if 19 < len(ACTIONS) else None
            verifier.capture_and_verify(18, ACTIONS[18], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 20: '5.2초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[20/25] ' + '5.2초 대기' + ' (건너뜀)')
    else:
        print(f'[20/25] ' + '5.2초 대기')
        try:
            time.sleep(5.2)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 21: '클릭 (86, 65)'
    print(f'[21/25] ' + '클릭 (86, 65)')
    try:
        screen_x, screen_y = to_screen_coords(86, 65); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[21] if 21 < len(ACTIONS) else None
            verifier.capture_and_verify(20, ACTIONS[20], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 22: '5.4초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[22/25] ' + '5.4초 대기' + ' (건너뜀)')
    else:
        print(f'[22/25] ' + '5.4초 대기')
        try:
            time.sleep(5.4)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 23: '5.9초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[23/25] ' + '5.9초 대기' + ' (건너뜀)')
    else:
        print(f'[23/25] ' + '5.9초 대기')
        try:
            time.sleep(5.9)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 24: '클릭 (1637, 778)'
    print(f'[24/25] ' + '클릭 (1637, 778)')
    try:
        screen_x, screen_y = to_screen_coords(1637, 778); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[24] if 24 < len(ACTIONS) else None
            verifier.capture_and_verify(23, ACTIONS[23], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 25: '키 입력: s'
    print(f'[25/25] ' + '키 입력: s')
    try:
        pyautogui.write('s')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            verifier.capture_and_verify(24, ACTIONS[24], None)
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
