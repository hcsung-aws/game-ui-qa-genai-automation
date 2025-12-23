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
        'timestamp': '2025-12-14T18:49:25.729539',
        'action_type': 'click',
        'x': 640,
        'y': 400,
        'description': '게임 시작 버튼 클릭',
        'button': 'left',
    },
    {
        'timestamp': '2025-12-14T18:49:25.729570',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '2.0초 대기',
        'wait_time': 2.0,
    },
    {
        'timestamp': '2025-12-14T18:49:25.729579',
        'action_type': 'key_press',
        'x': 0,
        'y': 0,
        'description': '플레이어 이름 입력',
        'key': 'TestPlayer',
    },
    {
        'timestamp': '2025-12-14T18:49:25.729585',
        'action_type': 'wait',
        'x': 0,
        'y': 0,
        'description': '1.5초 대기',
        'wait_time': 1.5,
    },
    {
        'timestamp': '2025-12-14T18:49:25.729590',
        'action_type': 'click',
        'x': 800,
        'y': 500,
        'description': '확인 버튼 클릭',
        'button': 'left',
    },
]

def replay_actions(action_delay=0.5):
    """액션을 순서대로 재실행
    
    Args:
        action_delay: 액션 간 지연 시간 (초)
    """
    print(f"총 5개의 액션을 재실행합니다...")
    print()
    
    # 액션 1: 게임 시작 버튼 클릭
    print(f'[1/5] 게임 시작 버튼 클릭')
    try:
        pyautogui.click(640, 400, button='left')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 2: 2.0초 대기
    print(f'[2/5] 2.0초 대기')
    try:
        time.sleep(2.0)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 3: 플레이어 이름 입력
    print(f'[3/5] 플레이어 이름 입력')
    try:
        pyautogui.write('TestPlayer')
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 4: 1.5초 대기
    print(f'[4/5] 1.5초 대기')
    try:
        time.sleep(1.5)
        # 액션 간 지연 시간
        if action_delay > 0:
            time.sleep(action_delay)
    except Exception as e:
        print(f'  ❌ 액션 실행 실패: {e}')
        # 오류가 발생해도 계속 진행 (Requirements 9.5)
        pass

    # 액션 5: 확인 버튼 클릭
    print(f'[5/5] 확인 버튼 클릭')
    try:
        pyautogui.click(800, 500, button='left')
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
