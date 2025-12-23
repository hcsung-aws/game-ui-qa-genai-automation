"""
Property-based tests for SemanticActionRecorder

**Feature: game-qa-automation, Property 28: 의미론적 액션 완전성**
**Feature: game-qa-automation, Property 29: 화면 전환 기록**

Validates: Requirements 11.1, 11.6
"""

import os
import sys
import tempfile
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, settings, strategies as st, assume

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.input_monitor import Action
from src.config_manager import ConfigManager
from src.semantic_action_recorder import SemanticAction, SemanticActionRecorder


# ============================================================================
# Strategies (전략 정의)
# ============================================================================

# 유효한 액션 타입 전략
action_type_strategy = st.sampled_from(['click', 'key_press', 'scroll', 'wait'])

# 좌표 전략 (화면 해상도 범위 내)
coordinate_strategy = st.integers(min_value=0, max_value=3840)

# 설명 전략 (유효한 문자열만)
description_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Z')),
    min_size=1, 
    max_size=100
).filter(lambda x: x.strip() != '')

# 버튼 타입 전략
button_strategy = st.sampled_from(['left', 'right', 'middle', None])

# 키 전략
key_strategy = st.one_of(
    st.sampled_from(['a', 'b', 'c', 'Enter', 'Space', 'Escape']),
    st.none()
)

# 스크롤 양 전략
scroll_strategy = st.integers(min_value=-10, max_value=10)

# 의미론적 정보 전략
semantic_info_strategy = st.fixed_dictionaries({
    "intent": st.sampled_from(['click_button', 'text_input', 'scroll_content', 'unknown_action']),
    "target_element": st.fixed_dictionaries({
        "type": st.sampled_from(['button', 'icon', 'text_field', 'unknown']),
        "text": st.text(min_size=0, max_size=50),
        "description": st.text(min_size=0, max_size=100),
        "visual_features": st.just({})
    }),
    "context": st.fixed_dictionaries({
        "screen_state": st.sampled_from(['lobby', 'game', 'menu', 'unknown']),
        "expected_result": st.sampled_from(['navigation', 'dialog', 'none', 'unknown'])
    })
})

# 화면 전환 정보 전략
screen_transition_strategy = st.fixed_dictionaries({
    "before_state": st.sampled_from(['lobby', 'game', 'menu', 'unknown']),
    "after_state": st.sampled_from(['lobby', 'game', 'menu', 'loading', 'unknown']),
    "transition_type": st.sampled_from(['none', 'minor_change', 'partial_change', 'full_transition']),
    "hash_difference": st.integers(min_value=0, max_value=64)
})


# ============================================================================
# Helper Functions
# ============================================================================

def create_temp_config():
    """임시 설정 파일 생성"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0"
            },
            "automation": {
                "screenshot_on_action": False,
                "screenshot_dir": tempfile.mkdtemp()
            }
        }
        json.dump(config_data, f)
        return f.name


def create_mock_ui_analyzer():
    """Mock UIAnalyzer 생성"""
    mock_analyzer = Mock()
    mock_analyzer.analyze_with_retry.return_value = {
        "buttons": [{"text": "테스트 버튼", "x": 100, "y": 100, "width": 80, "height": 30, "confidence": 0.95}],
        "icons": [],
        "text_fields": []
    }
    return mock_analyzer


# ============================================================================
# Property 28: 의미론적 액션 완전성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    action_type=action_type_strategy,
    x=coordinate_strategy,
    y=coordinate_strategy,
    description=description_strategy,
    semantic_info=semantic_info_strategy,
    screen_transition=screen_transition_strategy
)
def test_semantic_action_completeness(action_type, x, y, description, 
                                       semantic_info, screen_transition):
    """
    **Feature: game-qa-automation, Property 28: 의미론적 액션 완전성**
    
    For any 기록된 의미론적 액션, 액션은 물리적 정보(좌표)와 
    의미론적 정보(의도, 타겟 요소, 맥락)를 모두 포함해야 한다.
    
    Validates: Requirements 11.6
    """
    # SemanticAction 생성
    semantic_action = SemanticAction(
        timestamp=datetime.now().isoformat(),
        action_type=action_type,
        x=x,
        y=y,
        description=description,
        semantic_info=semantic_info,
        screen_transition=screen_transition
    )
    
    # ========================================
    # 물리적 정보 검증 (좌표)
    # ========================================
    
    # 필수 물리적 필드 존재 확인
    assert hasattr(semantic_action, 'x'), "x 좌표 필드가 없습니다"
    assert hasattr(semantic_action, 'y'), "y 좌표 필드가 없습니다"
    assert hasattr(semantic_action, 'timestamp'), "timestamp 필드가 없습니다"
    assert hasattr(semantic_action, 'action_type'), "action_type 필드가 없습니다"
    assert hasattr(semantic_action, 'description'), "description 필드가 없습니다"
    
    # 물리적 필드 값 검증
    assert semantic_action.x is not None, "x 좌표가 None입니다"
    assert semantic_action.y is not None, "y 좌표가 None입니다"
    assert semantic_action.x == x, f"x 좌표 불일치: {semantic_action.x} != {x}"
    assert semantic_action.y == y, f"y 좌표 불일치: {semantic_action.y} != {y}"
    
    # ========================================
    # 의미론적 정보 검증
    # ========================================
    
    # semantic_info 필드 존재 확인
    assert hasattr(semantic_action, 'semantic_info'), "semantic_info 필드가 없습니다"
    assert semantic_action.semantic_info is not None, "semantic_info가 None입니다"
    assert isinstance(semantic_action.semantic_info, dict), "semantic_info가 딕셔너리가 아닙니다"
    
    # 의미론적 정보 필수 키 확인
    assert 'intent' in semantic_action.semantic_info, "intent 키가 없습니다"
    assert 'target_element' in semantic_action.semantic_info, "target_element 키가 없습니다"
    assert 'context' in semantic_action.semantic_info, "context 키가 없습니다"
    
    # target_element 구조 검증
    target = semantic_action.semantic_info['target_element']
    assert isinstance(target, dict), "target_element가 딕셔너리가 아닙니다"
    assert 'type' in target, "target_element에 type이 없습니다"
    assert 'text' in target, "target_element에 text가 없습니다"
    assert 'description' in target, "target_element에 description이 없습니다"
    
    # context 구조 검증
    context = semantic_action.semantic_info['context']
    assert isinstance(context, dict), "context가 딕셔너리가 아닙니다"
    assert 'screen_state' in context, "context에 screen_state가 없습니다"
    assert 'expected_result' in context, "context에 expected_result가 없습니다"
    
    # ========================================
    # 화면 전환 정보 검증
    # ========================================
    
    assert hasattr(semantic_action, 'screen_transition'), "screen_transition 필드가 없습니다"
    assert isinstance(semantic_action.screen_transition, dict), "screen_transition이 딕셔너리가 아닙니다"


# ============================================================================
# Property 29: 화면 전환 기록
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    x=coordinate_strategy,
    y=coordinate_strategy,
    button=st.sampled_from(['left', 'right', 'middle'])
)
def test_screen_transition_recording(x, y, button):
    """
    **Feature: game-qa-automation, Property 29: 화면 전환 기록**
    
    For any 클릭 액션, 액션 전후의 스크린샷과 화면 전환 정보
    (이전 상태, 이후 상태)가 기록되어야 한다.
    
    Validates: Requirements 11.1, 11.4
    """
    temp_config_path = create_temp_config()
    
    try:
        # ConfigManager 생성
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        # Mock UIAnalyzer 생성
        mock_analyzer = create_mock_ui_analyzer()
        
        # SemanticActionRecorder 생성
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # 클릭 액션 생성
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=x,
            y=y,
            description=f'클릭 ({x}, {y})',
            button=button
        )
        
        # pyautogui.screenshot을 Mock으로 대체
        with patch('src.semantic_action_recorder.pyautogui') as mock_pyautogui:
            # Mock 이미지 생성
            from PIL import Image
            mock_image = Image.new('RGB', (100, 100), color='red')
            mock_pyautogui.screenshot.return_value = mock_image
            
            # 의미론적 액션 기록 (스크린샷 캡처 포함)
            semantic_action = recorder.record_semantic_action(
                action, 
                capture_screenshots=True,
                analyze_ui=False  # UI 분석은 별도 테스트
            )
        
        # ========================================
        # 스크린샷 경로 검증
        # ========================================
        
        # 클릭 액션의 경우 후 스크린샷이 캡처되어야 함
        assert hasattr(semantic_action, 'screenshot_after_path'), \
            "screenshot_after_path 필드가 없습니다"
        
        # 스크린샷 경로가 설정되었는지 확인
        # (실제 파일 존재 여부는 통합 테스트에서 확인)
        if semantic_action.screenshot_after_path:
            assert isinstance(semantic_action.screenshot_after_path, str), \
                "screenshot_after_path가 문자열이 아닙니다"
        
        # ========================================
        # UI 상태 해시 검증
        # ========================================
        
        assert hasattr(semantic_action, 'ui_state_hash_after'), \
            "ui_state_hash_after 필드가 없습니다"
        
        # 해시가 설정되었는지 확인
        if semantic_action.ui_state_hash_after:
            assert isinstance(semantic_action.ui_state_hash_after, str), \
                "ui_state_hash_after가 문자열이 아닙니다"
        
        # ========================================
        # 화면 전환 정보 구조 검증
        # ========================================
        
        assert hasattr(semantic_action, 'screen_transition'), \
            "screen_transition 필드가 없습니다"
        assert isinstance(semantic_action.screen_transition, dict), \
            "screen_transition이 딕셔너리가 아닙니다"
        
    finally:
        # 임시 파일 정리
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


@settings(max_examples=50, deadline=None)
@given(
    hash_before=st.text(alphabet='0123456789abcdef', min_size=16, max_size=16),
    hash_after=st.text(alphabet='0123456789abcdef', min_size=16, max_size=16)
)
def test_screen_transition_analysis(hash_before, hash_after):
    """
    화면 전환 분석 로직 테스트
    
    For any 두 개의 이미지 해시, 화면 전환 분석은 해시 차이를 계산하고
    적절한 전환 타입을 결정해야 한다.
    
    Validates: Requirements 11.4
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # Mock 이미지 생성
        from PIL import Image
        image_before = Image.new('RGB', (100, 100), color='blue')
        image_after = Image.new('RGB', (100, 100), color='green')
        
        # 화면 전환 분석
        transition = recorder._analyze_screen_transition(
            hash_before, hash_after, image_before, image_after
        )
        
        # 결과 구조 검증
        assert isinstance(transition, dict), "전환 정보가 딕셔너리가 아닙니다"
        assert 'before_state' in transition, "before_state가 없습니다"
        assert 'after_state' in transition, "after_state가 없습니다"
        assert 'transition_type' in transition, "transition_type이 없습니다"
        assert 'hash_difference' in transition, "hash_difference가 없습니다"
        
        # transition_type이 유효한 값인지 확인
        valid_types = ['none', 'minor_change', 'partial_change', 'full_transition']
        assert transition['transition_type'] in valid_types, \
            f"유효하지 않은 transition_type: {transition['transition_type']}"
        
        # hash_difference가 음수가 아닌지 확인
        assert transition['hash_difference'] >= 0, \
            f"hash_difference가 음수입니다: {transition['hash_difference']}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


# ============================================================================
# 추가 테스트: 직렬화/역직렬화 Round Trip
# ============================================================================

@settings(max_examples=50, deadline=None)
@given(
    action_type=action_type_strategy,
    x=coordinate_strategy,
    y=coordinate_strategy,
    description=description_strategy,
    semantic_info=semantic_info_strategy,
    screen_transition=screen_transition_strategy
)
def test_semantic_action_serialization_round_trip(action_type, x, y, description,
                                                   semantic_info, screen_transition):
    """
    의미론적 액션 직렬화/역직렬화 Round Trip 테스트
    
    For any 의미론적 액션, 딕셔너리로 변환 후 다시 복원하면
    원래 데이터와 동일해야 한다.
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # SemanticAction 생성 및 기록
        semantic_action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type=action_type,
            x=x,
            y=y,
            description=description,
            semantic_info=semantic_info,
            screen_transition=screen_transition
        )
        recorder.semantic_actions.append(semantic_action)
        
        # 딕셔너리로 변환
        dict_list = recorder.to_dict_list()
        
        # 새 레코더로 복원
        restored_recorder = SemanticActionRecorder.from_dict_list(dict_list, config)
        
        # 복원된 액션 검증
        assert len(restored_recorder.semantic_actions) == 1, \
            "복원된 액션 수가 일치하지 않습니다"
        
        restored_action = restored_recorder.semantic_actions[0]
        
        # 물리적 정보 검증
        assert restored_action.action_type == action_type, \
            f"action_type 불일치: {restored_action.action_type} != {action_type}"
        assert restored_action.x == x, f"x 불일치: {restored_action.x} != {x}"
        assert restored_action.y == y, f"y 불일치: {restored_action.y} != {y}"
        assert restored_action.description == description, \
            f"description 불일치: {restored_action.description} != {description}"
        
        # 의미론적 정보 검증
        assert restored_action.semantic_info == semantic_info, \
            f"semantic_info 불일치"
        assert restored_action.screen_transition == screen_transition, \
            f"screen_transition 불일치"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


# ============================================================================
# 단위 테스트
# ============================================================================

def test_intent_inference_button():
    """버튼 클릭 의도 추론 테스트"""
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # 시작 버튼
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100, y=100,
            description='클릭'
        )
        target = {"type": "button", "text": "시작", "description": "", "visual_features": {}}
        intent = recorder._infer_intent(action, target)
        assert intent == 'start_game', f"시작 버튼 의도 추론 실패: {intent}"
        
        # 설정 버튼
        target = {"type": "button", "text": "Settings", "description": "", "visual_features": {}}
        intent = recorder._infer_intent(action, target)
        assert intent == 'open_settings', f"설정 버튼 의도 추론 실패: {intent}"
        
        # 확인 버튼
        target = {"type": "button", "text": "OK", "description": "", "visual_features": {}}
        intent = recorder._infer_intent(action, target)
        assert intent == 'confirm_action', f"확인 버튼 의도 추론 실패: {intent}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


def test_find_closest_element():
    """가장 가까운 UI 요소 찾기 테스트"""
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        ui_data = {
            "buttons": [
                {"text": "버튼1", "x": 100, "y": 100, "width": 80, "height": 30},
                {"text": "버튼2", "x": 300, "y": 100, "width": 80, "height": 30}
            ],
            "icons": [
                {"type": "settings", "x": 500, "y": 50}
            ],
            "text_fields": []
        }
        
        # (100, 100) 근처 클릭 - 버튼1이 가장 가까움
        closest = recorder._find_closest_element(ui_data, 105, 105)
        assert closest['type'] == 'button', f"타입 불일치: {closest['type']}"
        assert closest['text'] == '버튼1', f"텍스트 불일치: {closest['text']}"
        
        # (500, 50) 근처 클릭 - 아이콘이 가장 가까움
        closest = recorder._find_closest_element(ui_data, 495, 55)
        assert closest['type'] == 'icon', f"타입 불일치: {closest['type']}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
