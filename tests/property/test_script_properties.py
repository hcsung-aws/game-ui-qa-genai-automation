"""
Property-based tests for ScriptGenerator

**Feature: game-qa-automation, Property 9: 스크립트 생성 완전성**
**Feature: game-qa-automation, Property 11: UTF-8 인코딩 보장**
"""

import os
import sys
import tempfile
import ast
from datetime import datetime
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.input_monitor import Action
from src.config_manager import ConfigManager


# 유효한 액션 타입 전략
action_type_strategy = st.sampled_from(['click', 'key_press', 'scroll', 'wait'])

# 좌표 전략
coordinate_strategy = st.integers(min_value=0, max_value=3840)

# 유니코드 문자를 포함한 설명 전략 (한글, 일본어, 중국어, 이모지 등)
unicode_description_strategy = st.text(
    alphabet=st.characters(
        blacklist_categories=('Cs',),  # Surrogate 제외
        min_codepoint=0x20,  # 제어 문자 제외
        max_codepoint=0x10FFFF
    ),
    min_size=1,
    max_size=50
)


def create_action_list(count, use_unicode=False):
    """테스트용 액션 리스트 생성"""
    actions = []
    for i in range(count):
        if use_unicode:
            description = f'테스트 액션 {i} 🎮 クリック 点击'
        else:
            description = f'Test action {i}'
        
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100 * i,
            y=100 * i,
            description=description
        )
        actions.append(action)
    return actions


@settings(max_examples=100, deadline=None)
@given(
    action_count=st.integers(min_value=1, max_value=20),
    action_type=action_type_strategy,
    x=coordinate_strategy,
    y=coordinate_strategy,
    description=st.text(min_size=1, max_size=100)
)
def test_script_generation_completeness(action_count, action_type, x, y, description):
    """
    **Feature: game-qa-automation, Property 9: 스크립트 생성 완전성**
    
    For any 액션 리스트, 생성된 Replay Script는 모든 액션을 포함해야 하며,
    각 액션은 timestamp, action_type, x, y, description을 포함해야 한다.
    
    Validates: Requirements 5.1, 5.2
    """
    # ScriptGenerator를 import (아직 구현 전이므로 try-except 사용)
    try:
        from src.script_generator import ScriptGenerator
    except ImportError:
        # 구현 전이므로 테스트 스킵
        import pytest
        pytest.skip("ScriptGenerator not implemented yet")
    
    # 임시 설정 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_config_path = f.name
    
    # 임시 스크립트 파일 경로
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        temp_script_path = f.name
    
    try:
        # ConfigManager 생성
        config = ConfigManager(temp_config_path)
        config.create_default_config()
        
        # ScriptGenerator 생성
        generator = ScriptGenerator(config)
        
        # 액션 리스트 생성
        actions = []
        for i in range(action_count):
            action = Action(
                timestamp=datetime.now().isoformat(),
                action_type=action_type,
                x=x + i,
                y=y + i,
                description=f"{description}_{i}"
            )
            actions.append(action)
        
        # 스크립트 생성
        script_path = generator.generate_replay_script(actions, temp_script_path)
        
        # 스크립트 파일이 생성되었는지 확인
        assert os.path.exists(script_path), "스크립트 파일이 생성되지 않았습니다"
        
        # 스크립트 파일 읽기
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # 모든 액션이 스크립트에 포함되어 있는지 확인
        for i, action in enumerate(actions):
            # timestamp 확인
            assert action.timestamp in script_content, \
                f"액션 {i}의 timestamp가 스크립트에 없습니다"
            
            # action_type 확인
            assert action.action_type in script_content, \
                f"액션 {i}의 action_type이 스크립트에 없습니다"
            
            # 좌표 확인 (문자열로 변환하여 확인)
            assert str(action.x) in script_content, \
                f"액션 {i}의 x 좌표가 스크립트에 없습니다"
            assert str(action.y) in script_content, \
                f"액션 {i}의 y 좌표가 스크립트에 없습니다"
            
            # description 확인 (특수 문자가 이스케이프될 수 있으므로 repr 형태도 확인)
            # 원본 또는 이스케이프된 형태 중 하나가 있으면 통과
            description_in_content = (
                action.description in script_content or 
                repr(action.description) in script_content
            )
            assert description_in_content, \
                f"액션 {i}의 description이 스크립트에 없습니다"
        
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)


@settings(max_examples=50, deadline=None)
@given(
    description=unicode_description_strategy
)
def test_utf8_encoding_guarantee(description):
    """
    **Feature: game-qa-automation, Property 11: UTF-8 인코딩 보장**
    
    For any 생성된 Replay Script, 파일은 UTF-8 인코딩으로 저장되어야 하며,
    한글 등 유니코드 문자가 손실 없이 저장되어야 한다.
    
    Validates: Requirements 5.4
    """
    try:
        from src.script_generator import ScriptGenerator
    except ImportError:
        import pytest
        pytest.skip("ScriptGenerator not implemented yet")
    
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_config_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        temp_script_path = f.name
    
    try:
        # ConfigManager 생성
        config = ConfigManager(temp_config_path)
        config.create_default_config()
        
        # ScriptGenerator 생성
        generator = ScriptGenerator(config)
        
        # 유니코드 문자를 포함한 액션 생성
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100,
            y=200,
            description=description
        )
        
        # 스크립트 생성
        script_path = generator.generate_replay_script([action], temp_script_path)
        
        # UTF-8로 파일 읽기
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # 원본 description이 손실 없이 포함되어 있는지 확인
        # (특수 문자가 이스케이프될 수 있으므로 repr 형태도 확인)
        description_in_content = (
            description in script_content or 
            repr(description) in script_content
        )
        assert description_in_content, \
            f"유니코드 문자가 손실되었습니다: {description}"
        
        # 파일이 유효한 UTF-8인지 확인 (다시 읽어서 예외가 발생하지 않는지)
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                f.read()
        except UnicodeDecodeError:
            assert False, "파일이 UTF-8로 인코딩되지 않았습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)


def test_script_structure_validity():
    """
    **Feature: game-qa-automation, Property 10: 스크립트 구조 유효성**
    
    For any 생성된 Replay Script, 스크립트는 유효한 Python 문법을 따라야 하며,
    replay_actions 함수를 포함해야 한다.
    
    Validates: Requirements 5.3
    """
    try:
        from src.script_generator import ScriptGenerator
    except ImportError:
        import pytest
        pytest.skip("ScriptGenerator not implemented yet")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_config_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        temp_script_path = f.name
    
    try:
        config = ConfigManager(temp_config_path)
        config.create_default_config()
        
        generator = ScriptGenerator(config)
        
        # 테스트용 액션 생성
        actions = create_action_list(5)
        
        # 스크립트 생성
        script_path = generator.generate_replay_script(actions, temp_script_path)
        
        # 스크립트 파일 읽기
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Python 문법 검증 (AST 파싱)
        try:
            ast.parse(script_content)
        except SyntaxError as e:
            assert False, f"생성된 스크립트가 유효한 Python 문법이 아닙니다: {e}"
        
        # replay_actions 함수 존재 확인
        assert 'def replay_actions' in script_content, \
            "replay_actions 함수가 스크립트에 없습니다"
        
        # 필수 import 확인
        assert 'import pyautogui' in script_content, \
            "pyautogui import가 없습니다"
        assert 'import time' in script_content, \
            "time import가 없습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)


def test_wait_action_parsing():
    """
    **Feature: game-qa-automation, Property 12: 대기 액션 파싱 정확성**
    
    For any "N초 대기" 형식의 설명을 가진 대기 액션,
    생성된 스크립트는 time.sleep(N)을 포함해야 한다.
    
    Validates: Requirements 5.5
    """
    try:
        from src.script_generator import ScriptGenerator
    except ImportError:
        import pytest
        pytest.skip("ScriptGenerator not implemented yet")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_config_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        temp_script_path = f.name
    
    try:
        config = ConfigManager(temp_config_path)
        config.create_default_config()
        
        generator = ScriptGenerator(config)
        
        # 대기 액션 생성
        wait_action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='wait',
            x=0,
            y=0,
            description='2.5초 대기'
        )
        
        # 스크립트 생성
        script_path = generator.generate_replay_script([wait_action], temp_script_path)
        
        # 스크립트 파일 읽기
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # time.sleep(2.5) 포함 확인
        assert 'time.sleep(2.5)' in script_content, \
            "대기 시간이 올바르게 파싱되지 않았습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)


def test_action_execution_order():
    """
    액션이 스크립트에 순서대로 포함되는지 테스트
    
    Validates: Requirements 6.1
    """
    try:
        from src.script_generator import ScriptGenerator
    except ImportError:
        import pytest
        pytest.skip("ScriptGenerator not implemented yet")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_config_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        temp_script_path = f.name
    
    try:
        config = ConfigManager(temp_config_path)
        config.create_default_config()
        
        generator = ScriptGenerator(config)
        
        # 순서가 있는 액션 리스트 생성
        actions = []
        for i in range(5):
            action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=i * 100,
                y=i * 100,
                description=f'액션 순서 {i}'
            )
            actions.append(action)
        
        # 스크립트 생성
        script_path = generator.generate_replay_script(actions, temp_script_path)
        
        # 스크립트 파일 읽기
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # 각 액션의 description이 순서대로 나타나는지 확인
        last_index = -1
        for i, action in enumerate(actions):
            current_index = script_content.find(action.description)
            assert current_index > last_index, \
                f"액션 {i}의 순서가 올바르지 않습니다"
            last_index = current_index
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)


def test_script_with_korean_characters():
    """한글이 포함된 스크립트 생성 테스트"""
    try:
        from src.script_generator import ScriptGenerator
    except ImportError:
        import pytest
        pytest.skip("ScriptGenerator not implemented yet")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_config_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        temp_script_path = f.name
    
    try:
        config = ConfigManager(temp_config_path)
        config.create_default_config()
        
        generator = ScriptGenerator(config)
        
        # 한글이 포함된 액션 생성
        actions = [
            Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=640,
                y=400,
                description='게임 시작 버튼 클릭'
            ),
            Action(
                timestamp=datetime.now().isoformat(),
                action_type='key_press',
                x=0,
                y=0,
                description='플레이어 이름 입력',
                key='홍길동'
            ),
            Action(
                timestamp=datetime.now().isoformat(),
                action_type='wait',
                x=0,
                y=0,
                description='1.5초 대기'
            )
        ]
        
        # 스크립트 생성
        script_path = generator.generate_replay_script(actions, temp_script_path)
        
        # UTF-8로 파일 읽기
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # 한글이 손실 없이 포함되어 있는지 확인
        assert '게임 시작 버튼 클릭' in script_content
        assert '플레이어 이름 입력' in script_content
        assert '1.5초 대기' in script_content
        
        # Python 문법 검증
        try:
            ast.parse(script_content)
        except SyntaxError as e:
            assert False, f"한글이 포함된 스크립트가 유효하지 않습니다: {e}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
