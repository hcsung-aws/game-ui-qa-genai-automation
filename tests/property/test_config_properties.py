"""
Property-based tests for ConfigManager

**Feature: game-qa-automation, Property 1: 설정 파일 round trip**
"""

import os
import tempfile
from hypothesis import given, settings, strategies as st
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.config_manager import ConfigManager


# 유효한 JSON 값을 생성하는 전략 (단순화)
json_value_strategy = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1000, max_value=1000),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1000.0, max_value=1000.0),
    st.text(min_size=0, max_size=50)
)


@settings(max_examples=100, deadline=None)
@given(config=st.dictionaries(
    keys=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    values=json_value_strategy,
    min_size=1,
    max_size=5
))
def test_config_round_trip(config):
    """
    **Feature: game-qa-automation, Property 1: 설정 파일 round trip**
    
    For any 유효한 설정 딕셔너리, 설정을 JSON 파일로 저장한 후 다시 로드하면 
    원래 설정과 동일한 값을 가져야 한다.
    
    Validates: Requirements 1.5
    """
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        # ConfigManager 생성
        manager = ConfigManager(temp_path)
        
        # 설정 저장
        manager.save_config(config)
        
        # 설정 로드
        loaded_config = manager.load_config()
        
        # 원본과 동일한지 확인
        assert loaded_config == config, f"Expected {config}, but got {loaded_config}"
        
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_config_get_nested_keys():
    """중첩된 키 경로 접근 테스트"""
    config = {
        "aws": {
            "region": "ap-northeast-2",
            "model_id": "test-model"
        },
        "game": {
            "exe_path": "C:/test.exe"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    try:
        manager = ConfigManager(temp_path)
        manager.save_config(config)
        manager.load_config()
        
        # 중첩된 키 접근
        assert manager.get('aws.region') == 'ap-northeast-2'
        assert manager.get('aws.model_id') == 'test-model'
        assert manager.get('game.exe_path') == 'C:/test.exe'
        
        # 존재하지 않는 키
        assert manager.get('nonexistent.key', 'default') == 'default'
        assert manager.get('aws.nonexistent', None) is None
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_config_create_default():
    """기본 설정 생성 테스트"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_path = f.name
    
    # 파일 삭제 (존재하지 않는 상태로 만들기)
    os.remove(temp_path)
    
    try:
        manager = ConfigManager(temp_path)
        
        # 기본 설정 생성
        default_config = manager.create_default_config()
        
        # 필수 키 확인
        assert 'aws' in default_config
        assert 'game' in default_config
        assert 'automation' in default_config
        assert 'test_cases' in default_config
        
        # 파일이 생성되었는지 확인
        assert os.path.exists(temp_path)
        
        # 파일에서 로드하여 동일한지 확인
        loaded_config = manager.load_config()
        assert loaded_config == default_config
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
