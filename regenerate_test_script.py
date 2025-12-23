#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
기존 테스트 케이스의 스크립트를 검증 모드 지원으로 재생성
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_manager import ConfigManager
from src.script_generator import ScriptGenerator
from src.input_monitor import Action


def regenerate_script(test_case_name: str):
    """테스트 케이스 스크립트 재생성
    
    Args:
        test_case_name: 테스트 케이스 이름
    """
    json_path = f"test_cases/{test_case_name}.json"
    script_path = f"test_cases/{test_case_name}.py"
    
    if not os.path.exists(json_path):
        print(f"❌ 테스트 케이스를 찾을 수 없습니다: {json_path}")
        return
    
    # JSON 로드
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Action 객체로 변환
    actions = []
    for action_data in data.get('actions', []):
        action = Action(
            timestamp=action_data.get('timestamp', ''),
            action_type=action_data.get('action_type', ''),
            x=action_data.get('x', 0),
            y=action_data.get('y', 0),
            description=action_data.get('description', ''),
            screenshot_path=action_data.get('screenshot_path'),
            button=action_data.get('button'),
            key=action_data.get('key'),
            scroll_dx=action_data.get('scroll_dx'),
            scroll_dy=action_data.get('scroll_dy')
        )
        actions.append(action)
    
    # 스크립트 재생성
    config = ConfigManager()
    config.load_config()
    generator = ScriptGenerator(config)
    
    generator.generate_replay_script(actions, script_path, verify_mode=True)
    print(f"✓ 스크립트 재생성 완료: {script_path}")
    print(f"  검증 모드 실행: python {script_path} --verify")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_case_name = sys.argv[1]
    else:
        test_case_name = "limbus_test_02"
    
    regenerate_script(test_case_name)
