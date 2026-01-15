#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
InputMonitor 디버그 스크립트
pynput 이벤트가 제대로 캡처되는지 확인
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_manager import ConfigManager
from src.input_monitor import InputMonitor, ActionRecorder

def main():
    print("=" * 50)
    print("  InputMonitor 디버그 테스트")
    print("=" * 50)
    print()
    
    # 설정 로드
    config = ConfigManager('config.json')
    config.load_config()
    
    # screenshot_on_action을 False로 설정하여 스크린샷 캡처 비활성화
    # 이렇게 하면 순수하게 pynput 이벤트만 테스트할 수 있음
    config.config['automation']['screenshot_on_action'] = False
    
    print(f"screenshot_on_action: {config.get('automation.screenshot_on_action')}")
    print()
    
    # ActionRecorder 및 InputMonitor 생성
    action_recorder = ActionRecorder(config)
    input_monitor = InputMonitor(action_recorder)
    
    print("5초 후 모니터링을 시작합니다...")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    
    print()
    print("🔴 모니터링 시작! 아무 곳이나 클릭하세요.")
    print("   10초 후 자동 종료됩니다.")
    print()
    
    input_monitor.start_monitoring()
    
    try:
        for i in range(20):
            time.sleep(0.5)
            actions = action_recorder.get_actions()
            print(f"\r  경과: {(i+1)*0.5:.1f}초 | 기록된 액션: {len(actions)}개", end="", flush=True)
    except KeyboardInterrupt:
        print("\n중단됨")
    finally:
        input_monitor.stop_monitoring()
    
    print()
    print()
    
    actions = action_recorder.get_actions()
    print(f"✓ 총 {len(actions)}개의 액션이 기록되었습니다.")
    
    if actions:
        print("\n기록된 액션:")
        for i, action in enumerate(actions):
            print(f"  {i+1}. {action.action_type} at ({action.x}, {action.y})")
    else:
        print("\n❌ 액션이 기록되지 않았습니다.")
        print("   - 관리자 권한으로 실행해 보세요")
        print("   - 또는 다른 터미널에서 실행해 보세요")

if __name__ == '__main__':
    main()
