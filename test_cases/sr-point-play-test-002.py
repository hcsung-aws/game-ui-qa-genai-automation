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
        'timestamp': '2026-01-18T02:26:19.434642',
        'action_type': 'click',
        'x': 447,
        'y': 375,
        'description': '클릭 (447, 375)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0000.png',
    },
    {
        'timestamp': '2026-01-18T02:26:23.534053',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '7.9초 대기',
        'wait_time': 7.9,
    },
    {
        'timestamp': '2026-01-18T02:26:31.482375',
        'action_type': 'click',
        'x': 88,
        'y': 220,
        'description': '클릭 (88, 220)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0001.png',
    },
    {
        'timestamp': '2026-01-18T02:26:35.031110',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.8초 대기',
        'wait_time': 3.8,
    },
    {
        'timestamp': '2026-01-18T02:26:38.811411',
        'action_type': 'click',
        'x': 403,
        'y': 143,
        'description': '클릭 (403, 143)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0002.png',
    },
    {
        'timestamp': '2026-01-18T02:26:42.324275',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.4초 대기',
        'wait_time': 4.4,
    },
    {
        'timestamp': '2026-01-18T02:26:46.763792',
        'action_type': 'click',
        'x': 623,
        'y': 148,
        'description': '클릭 (623, 148)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0003.png',
    },
    {
        'timestamp': '2026-01-18T02:26:49.727409',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.8초 대기',
        'wait_time': 3.8,
    },
    {
        'timestamp': '2026-01-18T02:26:53.563141',
        'action_type': 'click',
        'x': 870,
        'y': 149,
        'description': '클릭 (870, 149)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0004.png',
    },
    {
        'timestamp': '2026-01-18T02:26:55.925148',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.4초 대기',
        'wait_time': 4.4,
    },
    {
        'timestamp': '2026-01-18T02:27:00.333791',
        'action_type': 'click',
        'x': 1120,
        'y': 143,
        'description': '클릭 (1120, 143)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0005.png',
    },
    {
        'timestamp': '2026-01-18T02:27:02.568532',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.9초 대기',
        'wait_time': 4.9,
    },
    {
        'timestamp': '2026-01-18T02:27:07.464105',
        'action_type': 'click',
        'x': 87,
        'y': 353,
        'description': '클릭 (87, 353)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0006.png',
    },
    {
        'timestamp': '2026-01-18T02:27:09.656504',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.0초 대기',
        'wait_time': 4.0,
    },
    {
        'timestamp': '2026-01-18T02:27:13.627456',
        'action_type': 'click',
        'x': 87,
        'y': 390,
        'description': '클릭 (87, 390)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0007.png',
    },
    {
        'timestamp': '2026-01-18T02:27:15.889240',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.7초 대기',
        'wait_time': 4.7,
    },
    {
        'timestamp': '2026-01-18T02:27:20.638230',
        'action_type': 'click',
        'x': 214,
        'y': 530,
        'description': '클릭 (214, 530)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0008.png',
    },
    {
        'timestamp': '2026-01-18T02:27:22.785572',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '4.7초 대기',
        'wait_time': 4.7,
    },
    {
        'timestamp': '2026-01-18T02:27:27.439871',
        'action_type': 'click',
        'x': 80,
        'y': 51,
        'description': '클릭 (80, 51)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0009.png',
    },
    {
        'timestamp': '2026-01-18T02:27:29.670113',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.0초 대기',
        'wait_time': 3.0,
    },
    {
        'timestamp': '2026-01-18T02:27:29.670113',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.8초 대기',
        'wait_time': 3.8,
    },
    {
        'timestamp': '2026-01-18T02:27:32.622111',
        'action_type': 'click',
        'x': 1512,
        'y': 842,
        'description': '클릭 (1512, 842)',
        'button': 'left',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0010.png',
    },
    {
        'timestamp': '2026-01-18T02:27:33.489968',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: s',
        'key': 's',
        'screenshot_path': 'screenshots\sr-point-play-test-002/action_0011.png',
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
    
    print(f"총 23개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '클릭 (447, 375)'
    print(f'[1/23] ' + '클릭 (447, 375)')
    try:
        screen_x, screen_y = to_screen_coords(447, 375); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 2: '7.9초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[2/23] ' + '7.9초 대기' + ' (건너뜀)')
    else:
        print(f'[2/23] ' + '7.9초 대기')
        try:
            time.sleep(7.9)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 3: '클릭 (88, 220)'
    print(f'[3/23] ' + '클릭 (88, 220)')
    try:
        screen_x, screen_y = to_screen_coords(88, 220); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 4: '3.8초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[4/23] ' + '3.8초 대기' + ' (건너뜀)')
    else:
        print(f'[4/23] ' + '3.8초 대기')
        try:
            time.sleep(3.8)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 5: '클릭 (403, 143)'
    print(f'[5/23] ' + '클릭 (403, 143)')
    try:
        screen_x, screen_y = to_screen_coords(403, 143); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 6: '4.4초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[6/23] ' + '4.4초 대기' + ' (건너뜀)')
    else:
        print(f'[6/23] ' + '4.4초 대기')
        try:
            time.sleep(4.4)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 7: '클릭 (623, 148)'
    print(f'[7/23] ' + '클릭 (623, 148)')
    try:
        screen_x, screen_y = to_screen_coords(623, 148); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 8: '3.8초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[8/23] ' + '3.8초 대기' + ' (건너뜀)')
    else:
        print(f'[8/23] ' + '3.8초 대기')
        try:
            time.sleep(3.8)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 9: '클릭 (870, 149)'
    print(f'[9/23] ' + '클릭 (870, 149)')
    try:
        screen_x, screen_y = to_screen_coords(870, 149); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 10: '4.4초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[10/23] ' + '4.4초 대기' + ' (건너뜀)')
    else:
        print(f'[10/23] ' + '4.4초 대기')
        try:
            time.sleep(4.4)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 11: '클릭 (1120, 143)'
    print(f'[11/23] ' + '클릭 (1120, 143)')
    try:
        screen_x, screen_y = to_screen_coords(1120, 143); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 12: '4.9초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[12/23] ' + '4.9초 대기' + ' (건너뜀)')
    else:
        print(f'[12/23] ' + '4.9초 대기')
        try:
            time.sleep(4.9)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 13: '클릭 (87, 353)'
    print(f'[13/23] ' + '클릭 (87, 353)')
    try:
        screen_x, screen_y = to_screen_coords(87, 353); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 14: '4.0초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[14/23] ' + '4.0초 대기' + ' (건너뜀)')
    else:
        print(f'[14/23] ' + '4.0초 대기')
        try:
            time.sleep(4.0)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 15: '클릭 (87, 390)'
    print(f'[15/23] ' + '클릭 (87, 390)')
    try:
        screen_x, screen_y = to_screen_coords(87, 390); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 16: '4.7초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[16/23] ' + '4.7초 대기' + ' (건너뜀)')
    else:
        print(f'[16/23] ' + '4.7초 대기')
        try:
            time.sleep(4.7)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 17: '클릭 (214, 530)'
    print(f'[17/23] ' + '클릭 (214, 530)')
    try:
        screen_x, screen_y = to_screen_coords(214, 530); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 18: '4.7초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[18/23] ' + '4.7초 대기' + ' (건너뜀)')
    else:
        print(f'[18/23] ' + '4.7초 대기')
        try:
            time.sleep(4.7)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 19: '클릭 (80, 51)'
    print(f'[19/23] ' + '클릭 (80, 51)')
    try:
        screen_x, screen_y = to_screen_coords(80, 51); pyautogui.click(screen_x, screen_y, button='left')
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

    # 액션 20: '3.0초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[20/23] ' + '3.0초 대기' + ' (건너뜀)')
    else:
        print(f'[20/23] ' + '3.0초 대기')
        try:
            time.sleep(3.0)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 21: '3.8초 대기'
    # 검증 모드 + skip_wait일 때 대기 건너뛰기
    if verify and skip_wait:
        print(f'[21/23] ' + '3.8초 대기' + ' (건너뜀)')
    else:
        print(f'[21/23] ' + '3.8초 대기')
        try:
            time.sleep(3.8)
            # 액션 간 지연 시간
            if action_delay > 0:
                time.sleep(action_delay)
        except Exception as e:
            print(f'  ❌ 액션 실행 실패: {e}')
            pass

    # 액션 22: '클릭 (1512, 842)'
    print(f'[22/23] ' + '클릭 (1512, 842)')
    try:
        screen_x, screen_y = to_screen_coords(1512, 842); pyautogui.click(screen_x, screen_y, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
            next_action = ACTIONS[22] if 22 < len(ACTIONS) else None
            verifier.capture_and_verify(21, ACTIONS[21], next_action)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 23: '키 입력: s'
    print(f'[23/23] ' + '키 입력: s')
    try:
        pyautogui.write('s')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
        # 검증 모드: CAPTURE_DELAY 대기 후 스크린샷 검증 (녹화 시점과 동일한 타이밍)
        if verifier:
            time.sleep(CAPTURE_DELAY)  # 화면 전환 완료 대기
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
