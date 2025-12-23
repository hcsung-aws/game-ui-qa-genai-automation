"""
Property-based tests for ActionRecorder

**Feature: game-qa-automation, Property 5: 액션 기록 완전성**
"""

import os
import sys
import tempfile
from datetime import datetime
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.input_monitor import Action, ActionRecorder
from src.config_manager import ConfigManager


# 유효한 액션 타입 전략
action_type_strategy = st.sampled_from(['click', 'key_press', 'scroll', 'wait'])

# 좌표 전략 (화면 해상도 범위 내)
coordinate_strategy = st.integers(min_value=0, max_value=3840)

# 설명 전략
description_strategy = st.text(min_size=1, max_size=100)


@settings(max_examples=100, deadline=None)
@given(
    action_type=action_type_strategy,
    x=coordinate_strategy,
    y=coordinate_strategy,
    description=description_strategy
)
def test_action_completeness(action_type, x, y, description):
    """
    **Feature: game-qa-automation, Property 5: 액션 기록 완전성**
    
    For any 실행된 액션, 기록된 액션은 timestamp, action_type, x, y, description 
    필드를 모두 포함해야 한다.
    
    Validates: Requirements 3.5
    """
    # 임시 설정 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_config_path = f.name
    
    try:
        # ConfigManager 생성 및 기본 설정 생성
        config = ConfigManager(temp_config_path)
        config.create_default_config()
        
        # screenshot_on_action을 False로 설정 (테스트 속도 향상)
        config.config['automation']['screenshot_on_action'] = False
        
        # ActionRecorder 생성
        recorder = ActionRecorder(config)
        
        # 액션 생성
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type=action_type,
            x=x,
            y=y,
            description=description
        )
        
        # 액션 기록
        recorder.record_action(action)
        
        # 기록된 액션 가져오기
        recorded_actions = recorder.get_actions()
        
        # 최소 1개 이상의 액션이 기록되어야 함
        assert len(recorded_actions) >= 1, "액션이 기록되지 않았습니다"
        
        # 마지막 기록된 액션 확인 (wait 액션이 추가될 수 있으므로)
        recorded_action = recorded_actions[-1]
        
        # 필수 필드 존재 확인
        assert hasattr(recorded_action, 'timestamp'), "timestamp 필드가 없습니다"
        assert hasattr(recorded_action, 'action_type'), "action_type 필드가 없습니다"
        assert hasattr(recorded_action, 'x'), "x 필드가 없습니다"
        assert hasattr(recorded_action, 'y'), "y 필드가 없습니다"
        assert hasattr(recorded_action, 'description'), "description 필드가 없습니다"
        
        # 필수 필드 값 확인 (None이 아니어야 함)
        assert recorded_action.timestamp is not None, "timestamp가 None입니다"
        assert recorded_action.action_type is not None, "action_type이 None입니다"
        assert recorded_action.x is not None, "x가 None입니다"
        assert recorded_action.y is not None, "y가 None입니다"
        assert recorded_action.description is not None, "description이 None입니다"
        
        # 값이 원본과 일치하는지 확인
        assert recorded_action.action_type == action_type, \
            f"action_type이 일치하지 않습니다: {recorded_action.action_type} != {action_type}"
        assert recorded_action.x == x, \
            f"x 좌표가 일치하지 않습니다: {recorded_action.x} != {x}"
        assert recorded_action.y == y, \
            f"y 좌표가 일치하지 않습니다: {recorded_action.y} != {y}"
        assert recorded_action.description == description, \
            f"description이 일치하지 않습니다: {recorded_action.description} != {description}"
        
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


def test_action_wait_insertion():
    """액션 간 시간 간격이 0.5초를 초과하면 wait 액션이 자동 삽입되는지 테스트
    
    Validates: Requirements 3.6
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_config_path = f.name
    
    try:
        # ConfigManager 생성
        config = ConfigManager(temp_config_path)
        config.create_default_config()
        config.config['automation']['screenshot_on_action'] = False
        
        # ActionRecorder 생성
        recorder = ActionRecorder(config)
        
        # 첫 번째 액션 기록
        action1 = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100,
            y=100,
            description='첫 번째 클릭'
        )
        recorder.record_action(action1)
        
        # 0.6초 대기 (0.5초 초과)
        import time
        time.sleep(0.6)
        
        # 두 번째 액션 기록
        action2 = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=200,
            y=200,
            description='두 번째 클릭'
        )
        recorder.record_action(action2)
        
        # 기록된 액션 확인
        recorded_actions = recorder.get_actions()
        
        # 3개의 액션이 있어야 함 (action1, wait, action2)
        assert len(recorded_actions) == 3, \
            f"wait 액션이 삽입되지 않았습니다. 액션 수: {len(recorded_actions)}"
        
        # 두 번째 액션이 wait 타입인지 확인
        wait_action = recorded_actions[1]
        assert wait_action.action_type == 'wait', \
            f"두 번째 액션이 wait가 아닙니다: {wait_action.action_type}"
        
        # wait 액션의 description에 시간 정보가 포함되어 있는지 확인
        assert '대기' in wait_action.description, \
            f"wait 액션의 description이 올바르지 않습니다: {wait_action.description}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


def test_action_clear():
    """액션 초기화 기능 테스트"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_config_path = f.name
    
    try:
        config = ConfigManager(temp_config_path)
        config.create_default_config()
        config.config['automation']['screenshot_on_action'] = False
        
        recorder = ActionRecorder(config)
        
        # 여러 액션 기록
        for i in range(5):
            action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=i * 100,
                y=i * 100,
                description=f'클릭 {i}'
            )
            recorder.record_action(action)
        
        # 액션이 기록되었는지 확인
        assert len(recorder.get_actions()) >= 5
        
        # 액션 초기화
        recorder.clear_actions()
        
        # 액션이 비어있는지 확인
        assert len(recorder.get_actions()) == 0, "액션이 초기화되지 않았습니다"
        assert recorder.last_action_time is None, "last_action_time이 초기화되지 않았습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


def test_action_optional_fields():
    """선택적 필드가 올바르게 저장되는지 테스트"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_config_path = f.name
    
    try:
        config = ConfigManager(temp_config_path)
        config.create_default_config()
        config.config['automation']['screenshot_on_action'] = False
        
        recorder = ActionRecorder(config)
        
        # 클릭 액션 (button 필드 포함)
        click_action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100,
            y=100,
            description='클릭',
            button='left'
        )
        recorder.record_action(click_action)
        
        # 키 입력 액션 (key 필드 포함)
        key_action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='key_press',
            x=0,
            y=0,
            description='키 입력',
            key='a'
        )
        recorder.record_action(key_action)
        
        # 스크롤 액션 (scroll_dx, scroll_dy 필드 포함)
        scroll_action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='scroll',
            x=500,
            y=500,
            description='스크롤',
            scroll_dx=0,
            scroll_dy=-3
        )
        recorder.record_action(scroll_action)
        
        # 기록된 액션 확인
        recorded_actions = recorder.get_actions()
        
        # 클릭 액션 확인
        click = recorded_actions[0]
        assert click.button == 'left', "button 필드가 올바르지 않습니다"
        
        # 키 입력 액션 확인 (wait 액션이 있을 수 있으므로 타입으로 찾기)
        key = next(a for a in recorded_actions if a.action_type == 'key_press')
        assert key.key == 'a', "key 필드가 올바르지 않습니다"
        
        # 스크롤 액션 확인
        scroll = next(a for a in recorded_actions if a.action_type == 'scroll')
        assert scroll.scroll_dx == 0, "scroll_dx 필드가 올바르지 않습니다"
        assert scroll.scroll_dy == -3, "scroll_dy 필드가 올바르지 않습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
