#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
자동 생성된 Replay Script

이 스크립트는 기록된 액션을 재실행합니다.
"""

import pyautogui
import time
import sys


# 기록된 액션 데이터
ACTIONS = [
    {
        'timestamp': '2025-12-23T23:18:26.531139',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: Key.alt_l',
        'key': 'Key.alt_l',
        'screenshot_path': 'screenshots/action_0000.png',
    },
    {
        'timestamp': '2025-12-23T23:18:26.784152',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: Key.tab',
        'key': 'Key.tab',
        'screenshot_path': 'screenshots/action_0001.png',
    },
    {
        'timestamp': '2025-12-23T23:18:27.032937',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.4초 대기',
        'wait_time': 2.4,
    },
    {
        'timestamp': '2025-12-23T23:18:29.104442',
        'action_type': 'click',
        'x': 613,
        'y': 635,
        'description': '클릭 (613, 635)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0002.png',
    },
    {
        'timestamp': '2025-12-23T23:18:29.420229',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.8초 대기',
        'wait_time': 3.8,
    },
    {
        'timestamp': '2025-12-23T23:18:32.936673',
        'action_type': 'click',
        'x': 714,
        'y': 547,
        'description': '클릭 (714, 547)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0004.png',
    },
    {
        'timestamp': '2025-12-23T23:18:33.170333',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '7.0초 대기',
        'wait_time': 7.0,
    },
    {
        'timestamp': '2025-12-23T23:18:39.837138',
        'action_type': 'click',
        'x': 1143,
        'y': 455,
        'description': '클릭 (1143, 455)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0006.png',
    },
    {
        'timestamp': '2025-12-23T23:18:40.173778',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.4초 대기',
        'wait_time': 2.4,
    },
    {
        'timestamp': '2025-12-23T23:18:42.274999',
        'action_type': 'click',
        'x': 1148,
        'y': 458,
        'description': '클릭 (1148, 458)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0008.png',
    },
    {
        'timestamp': '2025-12-23T23:18:42.593007',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.9초 대기',
        'wait_time': 2.9,
    },
    {
        'timestamp': '2025-12-23T23:18:45.081721',
        'action_type': 'click',
        'x': 1148,
        'y': 458,
        'description': '클릭 (1148, 458)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0010.png',
    },
    {
        'timestamp': '2025-12-23T23:18:45.447007',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.0초 대기',
        'wait_time': 3.0,
    },
    {
        'timestamp': '2025-12-23T23:18:48.142473',
        'action_type': 'click',
        'x': 1148,
        'y': 458,
        'description': '클릭 (1148, 458)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0012.png',
    },
    {
        'timestamp': '2025-12-23T23:18:48.467034',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.9초 대기',
        'wait_time': 2.9,
    },
    {
        'timestamp': '2025-12-23T23:18:51.045134',
        'action_type': 'click',
        'x': 1148,
        'y': 458,
        'description': '클릭 (1148, 458)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0014.png',
    },
    {
        'timestamp': '2025-12-23T23:18:51.367542',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '3.0초 대기',
        'wait_time': 3.0,
    },
    {
        'timestamp': '2025-12-23T23:18:54.067042',
        'action_type': 'click',
        'x': 1148,
        'y': 458,
        'description': '클릭 (1148, 458)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0016.png',
    },
    {
        'timestamp': '2025-12-23T23:18:54.384013',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '6.2초 대기',
        'wait_time': 6.2,
    },
    {
        'timestamp': '2025-12-23T23:19:00.322542',
        'action_type': 'click',
        'x': 949,
        'y': 931,
        'description': '클릭 (949, 931)',
        'button': 'left',
        'screenshot_path': 'screenshots/action_0018.png',
    },
    {
        'timestamp': '2025-12-23T23:19:00.684175',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: s',
        'key': 's',
        'screenshot_path': 'screenshots/action_0020.png',
    },
    {
        'timestamp': '2025-12-23T23:19:01.124070',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: t',
        'key': 't',
        'screenshot_path': 'screenshots/action_0021.png',
    },
    {
        'timestamp': '2025-12-23T23:19:01.348006',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: o',
        'key': 'o',
        'screenshot_path': 'screenshots/action_0022.png',
    },
    {
        'timestamp': '2025-12-23T23:19:01.564049',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: p',
        'key': 'p',
        'screenshot_path': 'screenshots/action_0023.png',
    },
    {
        'timestamp': '2025-12-23T23:19:02.027558',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '키 입력: Key.enter',
        'key': 'Key.enter',
        'screenshot_path': 'screenshots/action_0024.png',
    },
]

def replay_actions(action_delay=0.5):
    """액션을 순서대로 재실행
    
    Args:
        action_delay: 액션 간 지연 시간 (초)
    """
    print(f"총 25개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: '키 입력: Key.alt_l'
    print(f'[1/25] ' + '키 입력: Key.alt_l')
    try:
        pyautogui.press('alt_l')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 2: '키 입력: Key.tab'
    print(f'[2/25] ' + '키 입력: Key.tab')
    try:
        pyautogui.press('tab')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 3: '2.4초 대기'
    print(f'[3/25] ' + '2.4초 대기')
    try:
        time.sleep(2.4)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 4: '클릭 (613, 635)'
    print(f'[4/25] ' + '클릭 (613, 635)')
    try:
        pyautogui.click(613, 635, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 5: '3.8초 대기'
    print(f'[5/25] ' + '3.8초 대기')
    try:
        time.sleep(3.8)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 6: '클릭 (714, 547)'
    print(f'[6/25] ' + '클릭 (714, 547)')
    try:
        pyautogui.click(714, 547, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 7: '7.0초 대기'
    print(f'[7/25] ' + '7.0초 대기')
    try:
        time.sleep(7.0)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 8: '클릭 (1143, 455)'
    print(f'[8/25] ' + '클릭 (1143, 455)')
    try:
        pyautogui.click(1143, 455, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 9: '2.4초 대기'
    print(f'[9/25] ' + '2.4초 대기')
    try:
        time.sleep(2.4)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 10: '클릭 (1148, 458)'
    print(f'[10/25] ' + '클릭 (1148, 458)')
    try:
        pyautogui.click(1148, 458, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 11: '2.9초 대기'
    print(f'[11/25] ' + '2.9초 대기')
    try:
        time.sleep(2.9)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 12: '클릭 (1148, 458)'
    print(f'[12/25] ' + '클릭 (1148, 458)')
    try:
        pyautogui.click(1148, 458, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 13: '3.0초 대기'
    print(f'[13/25] ' + '3.0초 대기')
    try:
        time.sleep(3.0)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 14: '클릭 (1148, 458)'
    print(f'[14/25] ' + '클릭 (1148, 458)')
    try:
        pyautogui.click(1148, 458, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 15: '2.9초 대기'
    print(f'[15/25] ' + '2.9초 대기')
    try:
        time.sleep(2.9)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 16: '클릭 (1148, 458)'
    print(f'[16/25] ' + '클릭 (1148, 458)')
    try:
        pyautogui.click(1148, 458, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 17: '3.0초 대기'
    print(f'[17/25] ' + '3.0초 대기')
    try:
        time.sleep(3.0)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 18: '클릭 (1148, 458)'
    print(f'[18/25] ' + '클릭 (1148, 458)')
    try:
        pyautogui.click(1148, 458, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 19: '6.2초 대기'
    print(f'[19/25] ' + '6.2초 대기')
    try:
        time.sleep(6.2)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 20: '클릭 (949, 931)'
    print(f'[20/25] ' + '클릭 (949, 931)')
    try:
        pyautogui.click(949, 931, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 21: '키 입력: s'
    print(f'[21/25] ' + '키 입력: s')
    try:
        pyautogui.write('s')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 22: '키 입력: t'
    print(f'[22/25] ' + '키 입력: t')
    try:
        pyautogui.write('t')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 23: '키 입력: o'
    print(f'[23/25] ' + '키 입력: o')
    try:
        pyautogui.write('o')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 24: '키 입력: p'
    print(f'[24/25] ' + '키 입력: p')
    try:
        pyautogui.write('p')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 25: '키 입력: Key.enter'
    print(f'[25/25] ' + '키 입력: Key.enter')
    try:
        pyautogui.press('enter')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    print()
    print('✓ 재실행 완료')


if __name__ == '__main__':
    # 명령줄 인자로 action_delay 설정 가능
    action_delay = 0.5
    if len(sys.argv) > 1:
        try:
            action_delay = float(sys.argv[1])
        except ValueError:
            print("경고: 유효하지 않은 action_delay 값입니다. 기본값 0.5초를 사용합니다.")
    
    # 액션 재실행
    replay_actions(action_delay)
