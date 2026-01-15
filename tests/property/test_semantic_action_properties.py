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

# bounding_box 전략 (표준화된 구조)
bounding_box_strategy = st.fixed_dictionaries({
    "x": st.integers(min_value=0, max_value=3840),
    "y": st.integers(min_value=0, max_value=2160),
    "width": st.integers(min_value=0, max_value=500),
    "height": st.integers(min_value=0, max_value=500)
})

# 신뢰도 전략
confidence_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# 표준화된 target_element 전략 (Requirements: 1.3, 1.4, 2.3)
standardized_target_element_strategy = st.fixed_dictionaries({
    "type": st.sampled_from(['button', 'icon', 'text_field', 'unknown']),
    "text": st.text(min_size=0, max_size=50),
    "description": st.text(min_size=0, max_size=100),
    "bounding_box": bounding_box_strategy,
    "confidence": confidence_strategy
})

# 의미론적 정보 전략 (표준화된 구조 포함)
semantic_info_strategy = st.fixed_dictionaries({
    "intent": st.sampled_from(['click_button', 'text_input', 'scroll_content', 'unknown_action']),
    "target_element": standardized_target_element_strategy,
    "context": st.fixed_dictionaries({
        "screen_state": st.sampled_from(['lobby', 'game', 'menu', 'unknown']),
        "expected_result": st.sampled_from(['navigation', 'dialog', 'none', 'unknown'])
    })
})

# 레거시 의미론적 정보 전략 (visual_features 포함, 이전 버전 호환)
legacy_semantic_info_strategy = st.fixed_dictionaries({
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
        "text_fields": [],
        "source": "vision_llm"
    }
    return mock_analyzer


def create_mock_ui_analyzer_with_find_element():
    """find_element_at_position을 지원하는 Mock UIAnalyzer 생성"""
    mock_analyzer = Mock()
    mock_analyzer.analyze_with_retry.return_value = {
        "buttons": [
            {
                "text": "테스트 버튼", 
                "x": 100, 
                "y": 100, 
                "width": 80, 
                "height": 30, 
                "bounding_box": {"x": 60, "y": 85, "width": 80, "height": 30},
                "confidence": 0.95,
                "description": "테스트 버튼"
            }
        ],
        "icons": [],
        "text_fields": [],
        "source": "vision_llm"
    }
    
    def find_element_side_effect(ui_data, x, y, tolerance=50):
        """좌표에 따라 적절한 요소 반환"""
        for button in ui_data.get("buttons", []):
            bx, by = button.get("x", 0), button.get("y", 0)
            distance = ((bx - x) ** 2 + (by - y) ** 2) ** 0.5
            if distance <= tolerance:
                result = button.copy()
                result["element_type"] = "button"
                return result
        return None
    
    mock_analyzer.find_element_at_position.side_effect = find_element_side_effect
    return mock_analyzer


# ============================================================================
# Property 1: 클릭 액션의 의미론적 정보 완전성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    x=st.integers(min_value=50, max_value=150),  # 버튼 근처 좌표
    y=st.integers(min_value=50, max_value=150),
    button=st.sampled_from(['left', 'right', 'middle'])
)
def test_click_action_semantic_info_completeness(x, y, button):
    """
    **Feature: semantic-test-replay, Property 1: 클릭 액션의 의미론적 정보 완전성**
    
    *For any* 클릭 액션에 대해, 기록이 완료되면 해당 액션은 반드시 
    물리적 좌표(x, y)와 semantic_info(target_element 포함)를 모두 포함해야 한다.
    
    **Validates: Requirements 1.3, 1.4**
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        # Mock UIAnalyzer 생성 (find_element_at_position 지원)
        mock_analyzer = create_mock_ui_analyzer_with_find_element()
        
        # SemanticActionRecorder 생성
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        # pyautogui.screenshot과 pyautogui.click을 Mock으로 대체
        with patch('src.semantic_action_recorder.pyautogui') as mock_pyautogui:
            # Mock 이미지 생성
            from PIL import Image
            mock_image = Image.new('RGB', (200, 200), color='blue')
            mock_pyautogui.screenshot.return_value = mock_image
            
            # record_click_with_semantic_analysis 호출
            semantic_action = recorder.record_click_with_semantic_analysis(
                x=x,
                y=y,
                button=button,
                perform_click=False,  # 실제 클릭은 수행하지 않음
                click_delay=0.0  # 테스트에서는 지연 없음
            )
        
        # ========================================
        # 물리적 좌표 검증 (Requirements: 1.4)
        # ========================================
        assert semantic_action.x is not None, "x 좌표가 None입니다"
        assert semantic_action.y is not None, "y 좌표가 None입니다"
        assert semantic_action.x == x, f"x 좌표 불일치: {semantic_action.x} != {x}"
        assert semantic_action.y == y, f"y 좌표 불일치: {semantic_action.y} != {y}"
        assert semantic_action.action_type == 'click', f"action_type이 'click'이 아닙니다: {semantic_action.action_type}"
        
        # ========================================
        # semantic_info 존재 검증 (Requirements: 1.3, 1.4)
        # ========================================
        assert semantic_action.semantic_info is not None, "semantic_info가 None입니다"
        assert isinstance(semantic_action.semantic_info, dict), "semantic_info가 딕셔너리가 아닙니다"
        assert len(semantic_action.semantic_info) > 0, "semantic_info가 비어있습니다"
        
        # ========================================
        # target_element 존재 및 구조 검증 (Requirements: 1.3)
        # ========================================
        assert 'target_element' in semantic_action.semantic_info, "target_element가 없습니다"
        target_element = semantic_action.semantic_info['target_element']
        assert isinstance(target_element, dict), "target_element가 딕셔너리가 아닙니다"
        
        # target_element 필수 필드 검증
        assert 'type' in target_element, "target_element에 type이 없습니다"
        assert 'text' in target_element, "target_element에 text가 없습니다"
        assert 'description' in target_element, "target_element에 description이 없습니다"
        assert 'bounding_box' in target_element, "target_element에 bounding_box가 없습니다"
        assert 'confidence' in target_element, "target_element에 confidence가 없습니다"
        
        # bounding_box 구조 검증
        bbox = target_element['bounding_box']
        assert isinstance(bbox, dict), "bounding_box가 딕셔너리가 아닙니다"
        assert 'x' in bbox, "bounding_box에 x가 없습니다"
        assert 'y' in bbox, "bounding_box에 y가 없습니다"
        assert 'width' in bbox, "bounding_box에 width가 없습니다"
        assert 'height' in bbox, "bounding_box에 height가 없습니다"
        
        # confidence 범위 검증
        confidence = target_element['confidence']
        assert isinstance(confidence, (int, float)), "confidence가 숫자가 아닙니다"
        assert 0.0 <= confidence <= 1.0, f"confidence가 0.0~1.0 범위를 벗어났습니다: {confidence}"
        
        # ========================================
        # intent 존재 검증
        # ========================================
        assert 'intent' in semantic_action.semantic_info, "intent가 없습니다"
        
        # ========================================
        # context 존재 검증
        # ========================================
        assert 'context' in semantic_action.semantic_info, "context가 없습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


@settings(max_examples=50, deadline=None)
@given(
    x=st.integers(min_value=500, max_value=1000),  # 버튼에서 먼 좌표
    y=st.integers(min_value=500, max_value=1000),
    button=st.sampled_from(['left', 'right', 'middle'])
)
def test_click_action_semantic_info_completeness_no_element(x, y, button):
    """
    **Feature: semantic-test-replay, Property 1 확장: 요소가 없는 경우에도 완전성 유지**
    
    *For any* 클릭 액션에 대해, UI 요소가 발견되지 않더라도 
    semantic_info와 target_element 구조는 완전해야 한다.
    
    **Validates: Requirements 1.3, 1.4**
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        # Mock UIAnalyzer 생성 (요소를 찾지 못하는 경우)
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [],
            "icons": [],
            "text_fields": [],
            "source": "vision_llm"
        }
        mock_analyzer.find_element_at_position.return_value = None
        
        recorder = SemanticActionRecorder(config, ui_analyzer=mock_analyzer)
        
        with patch('src.semantic_action_recorder.pyautogui') as mock_pyautogui:
            from PIL import Image
            mock_image = Image.new('RGB', (200, 200), color='blue')
            mock_pyautogui.screenshot.return_value = mock_image
            
            semantic_action = recorder.record_click_with_semantic_analysis(
                x=x,
                y=y,
                button=button,
                perform_click=False,
                click_delay=0.0
            )
        
        # 물리적 좌표 검증
        assert semantic_action.x == x
        assert semantic_action.y == y
        
        # semantic_info 완전성 검증
        assert semantic_action.semantic_info is not None
        assert 'target_element' in semantic_action.semantic_info
        
        target_element = semantic_action.semantic_info['target_element']
        
        # 요소가 없어도 기본 구조는 유지되어야 함
        assert 'type' in target_element
        assert 'text' in target_element
        assert 'description' in target_element
        assert 'bounding_box' in target_element
        assert 'confidence' in target_element
        
        # 요소가 없으면 type은 'unknown'이어야 함
        assert target_element['type'] == 'unknown', \
            f"요소가 없을 때 type이 'unknown'이 아닙니다: {target_element['type']}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


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
# Property 2: 직렬화 왕복 동등성 (Round-trip Equivalence)
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
def test_semantic_action_serialization_round_trip(action_type, x, y, description,
                                                   semantic_info, screen_transition):
    """
    **Feature: semantic-test-replay, Property 2: 직렬화 왕복 동등성**
    
    *For any* 의미론적 액션, to_dict()로 직렬화 후 from_dict()로 역직렬화하면
    원래 객체와 동등해야 한다.
    
    **Validates: Requirements 2.4, 2.5, 6.1, 6.2, 6.3, 6.4**
    """
    timestamp = datetime.now().isoformat()
    
    # SemanticAction 생성
    original = SemanticAction(
        timestamp=timestamp,
        action_type=action_type,
        x=x,
        y=y,
        description=description,
        semantic_info=semantic_info,
        screen_transition=screen_transition,
        screenshot_before_path="test/before.png",
        screenshot_after_path="test/after.png",
        ui_state_hash_before="abc123",
        ui_state_hash_after="def456"
    )
    
    # 직렬화
    serialized = original.to_dict()
    
    # 역직렬화
    restored = SemanticAction.from_dict(serialized)
    
    # ========================================
    # 물리적 정보 동등성 검증
    # ========================================
    assert restored.timestamp == original.timestamp, \
        f"timestamp 불일치: {restored.timestamp} != {original.timestamp}"
    assert restored.action_type == original.action_type, \
        f"action_type 불일치: {restored.action_type} != {original.action_type}"
    assert restored.x == original.x, \
        f"x 불일치: {restored.x} != {original.x}"
    assert restored.y == original.y, \
        f"y 불일치: {restored.y} != {original.y}"
    assert restored.description == original.description, \
        f"description 불일치: {restored.description} != {original.description}"
    
    # ========================================
    # 스크린샷 경로 동등성 검증
    # ========================================
    assert restored.screenshot_before_path == original.screenshot_before_path, \
        f"screenshot_before_path 불일치"
    assert restored.screenshot_after_path == original.screenshot_after_path, \
        f"screenshot_after_path 불일치"
    
    # ========================================
    # UI 상태 해시 동등성 검증
    # ========================================
    assert restored.ui_state_hash_before == original.ui_state_hash_before, \
        f"ui_state_hash_before 불일치"
    assert restored.ui_state_hash_after == original.ui_state_hash_after, \
        f"ui_state_hash_after 불일치"
    
    # ========================================
    # 의미론적 정보 동등성 검증 (중첩 구조)
    # ========================================
    assert restored.semantic_info.get("intent") == original.semantic_info.get("intent"), \
        f"intent 불일치"
    
    # target_element 검증
    orig_target = original.semantic_info.get("target_element", {})
    rest_target = restored.semantic_info.get("target_element", {})
    
    assert rest_target.get("type") == orig_target.get("type"), \
        f"target_element.type 불일치"
    assert rest_target.get("text") == orig_target.get("text"), \
        f"target_element.text 불일치"
    assert rest_target.get("description") == orig_target.get("description"), \
        f"target_element.description 불일치"
    
    # bounding_box 검증 (표준화된 구조)
    orig_bbox = orig_target.get("bounding_box", {})
    rest_bbox = rest_target.get("bounding_box", {})
    assert rest_bbox.get("x") == orig_bbox.get("x"), "bounding_box.x 불일치"
    assert rest_bbox.get("y") == orig_bbox.get("y"), "bounding_box.y 불일치"
    assert rest_bbox.get("width") == orig_bbox.get("width"), "bounding_box.width 불일치"
    assert rest_bbox.get("height") == orig_bbox.get("height"), "bounding_box.height 불일치"
    
    # confidence 검증
    # float 비교는 근사값으로 (부동소수점 오차 허용)
    orig_conf = orig_target.get("confidence", 0.0)
    rest_conf = rest_target.get("confidence", 0.0)
    assert abs(rest_conf - orig_conf) < 1e-6, \
        f"confidence 불일치: {rest_conf} != {orig_conf}"
    
    # context 검증
    orig_ctx = original.semantic_info.get("context", {})
    rest_ctx = restored.semantic_info.get("context", {})
    assert rest_ctx.get("screen_state") == orig_ctx.get("screen_state"), \
        f"context.screen_state 불일치"
    assert rest_ctx.get("expected_result") == orig_ctx.get("expected_result"), \
        f"context.expected_result 불일치"
    
    # ========================================
    # 화면 전환 정보 동등성 검증
    # ========================================
    orig_trans = original.screen_transition
    rest_trans = restored.screen_transition
    
    assert rest_trans.get("before_state") == orig_trans.get("before_state"), \
        f"screen_transition.before_state 불일치"
    assert rest_trans.get("after_state") == orig_trans.get("after_state"), \
        f"screen_transition.after_state 불일치"
    assert rest_trans.get("transition_type") == orig_trans.get("transition_type"), \
        f"screen_transition.transition_type 불일치"
    assert rest_trans.get("hash_difference") == orig_trans.get("hash_difference"), \
        f"screen_transition.hash_difference 불일치"


@settings(max_examples=100, deadline=None)
@given(
    action_type=action_type_strategy,
    x=coordinate_strategy,
    y=coordinate_strategy,
    description=description_strategy,
    semantic_info=semantic_info_strategy,
    screen_transition=screen_transition_strategy
)
def test_double_round_trip_idempotence(action_type, x, y, description,
                                        semantic_info, screen_transition):
    """
    **Feature: semantic-test-replay, Property 2 확장: 이중 왕복 멱등성**
    
    *For any* 의미론적 액션, 두 번 연속 직렬화/역직렬화해도 결과가 동일해야 한다.
    
    **Validates: Requirements 6.1, 6.2, 6.3**
    """
    timestamp = datetime.now().isoformat()
    
    original = SemanticAction(
        timestamp=timestamp,
        action_type=action_type,
        x=x,
        y=y,
        description=description,
        semantic_info=semantic_info,
        screen_transition=screen_transition
    )
    
    # 첫 번째 왕복
    serialized1 = original.to_dict()
    restored1 = SemanticAction.from_dict(serialized1)
    
    # 두 번째 왕복
    serialized2 = restored1.to_dict()
    restored2 = SemanticAction.from_dict(serialized2)
    
    # 두 번째 직렬화 결과가 첫 번째와 동일해야 함
    # (JSON 직렬화 가능한 형태로 비교)
    import json
    json1 = json.dumps(serialized1, sort_keys=True, default=str)
    json2 = json.dumps(serialized2, sort_keys=True, default=str)
    
    assert json1 == json2, "이중 왕복 후 직렬화 결과가 다릅니다"


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


# ============================================================================
# Property 8: None 필드 직렬화 일관성
# ============================================================================

# None 가능 필드 전략
optional_string_strategy = st.one_of(st.none(), st.text(min_size=1, max_size=50))
optional_int_strategy = st.one_of(st.none(), st.integers(min_value=-100, max_value=100))


@settings(max_examples=100, deadline=None)
@given(
    action_type=action_type_strategy,
    x=coordinate_strategy,
    y=coordinate_strategy,
    screenshot_path=optional_string_strategy,
    button=button_strategy,
    key=key_strategy,
    scroll_dx=optional_int_strategy,
    scroll_dy=optional_int_strategy,
    screenshot_before_path=optional_string_strategy,
    screenshot_after_path=optional_string_strategy,
    ui_state_hash_before=optional_string_strategy,
    ui_state_hash_after=optional_string_strategy
)
def test_none_field_serialization_consistency(action_type, x, y, screenshot_path,
                                               button, key, scroll_dx, scroll_dy,
                                               screenshot_before_path, screenshot_after_path,
                                               ui_state_hash_before, ui_state_hash_after):
    """
    **Feature: semantic-test-replay, Property 8: None 필드 직렬화 일관성**
    
    *For any* SemanticAction with None 필드, 직렬화 후 역직렬화하면
    None 필드가 일관되게 None으로 유지되어야 한다.
    
    **Validates: Requirements 6.5**
    """
    timestamp = datetime.now().isoformat()
    
    # None 필드를 포함한 SemanticAction 생성
    original = SemanticAction(
        timestamp=timestamp,
        action_type=action_type,
        x=x,
        y=y,
        description="테스트 액션",
        screenshot_path=screenshot_path,
        button=button,
        key=key,
        scroll_dx=scroll_dx,
        scroll_dy=scroll_dy,
        screenshot_before_path=screenshot_before_path,
        screenshot_after_path=screenshot_after_path,
        ui_state_hash_before=ui_state_hash_before,
        ui_state_hash_after=ui_state_hash_after,
        semantic_info={},
        screen_transition={}
    )
    
    # 직렬화
    serialized = original.to_dict()
    
    # 역직렬화
    restored = SemanticAction.from_dict(serialized)
    
    # ========================================
    # None 필드 일관성 검증
    # ========================================
    
    # screenshot_path
    assert restored.screenshot_path == original.screenshot_path, \
        f"screenshot_path 불일치: {restored.screenshot_path} != {original.screenshot_path}"
    
    # button
    assert restored.button == original.button, \
        f"button 불일치: {restored.button} != {original.button}"
    
    # key
    assert restored.key == original.key, \
        f"key 불일치: {restored.key} != {original.key}"
    
    # scroll_dx
    assert restored.scroll_dx == original.scroll_dx, \
        f"scroll_dx 불일치: {restored.scroll_dx} != {original.scroll_dx}"
    
    # scroll_dy
    assert restored.scroll_dy == original.scroll_dy, \
        f"scroll_dy 불일치: {restored.scroll_dy} != {original.scroll_dy}"
    
    # screenshot_before_path
    assert restored.screenshot_before_path == original.screenshot_before_path, \
        f"screenshot_before_path 불일치: {restored.screenshot_before_path} != {original.screenshot_before_path}"
    
    # screenshot_after_path
    assert restored.screenshot_after_path == original.screenshot_after_path, \
        f"screenshot_after_path 불일치: {restored.screenshot_after_path} != {original.screenshot_after_path}"
    
    # ui_state_hash_before
    assert restored.ui_state_hash_before == original.ui_state_hash_before, \
        f"ui_state_hash_before 불일치: {restored.ui_state_hash_before} != {original.ui_state_hash_before}"
    
    # ui_state_hash_after
    assert restored.ui_state_hash_after == original.ui_state_hash_after, \
        f"ui_state_hash_after 불일치: {restored.ui_state_hash_after} != {original.ui_state_hash_after}"


@settings(max_examples=50, deadline=None)
@given(
    action_type=action_type_strategy,
    x=coordinate_strategy,
    y=coordinate_strategy
)
def test_empty_semantic_info_serialization(action_type, x, y):
    """
    빈 semantic_info 직렬화 테스트
    
    *For any* SemanticAction with 빈 semantic_info, 직렬화 후 역직렬화하면
    빈 딕셔너리가 유지되어야 한다.
    
    **Validates: Requirements 6.5**
    """
    timestamp = datetime.now().isoformat()
    
    # 빈 semantic_info로 생성
    original = SemanticAction(
        timestamp=timestamp,
        action_type=action_type,
        x=x,
        y=y,
        description="테스트",
        semantic_info={},
        screen_transition={}
    )
    
    # 직렬화
    serialized = original.to_dict()
    
    # 역직렬화
    restored = SemanticAction.from_dict(serialized)
    
    # 빈 딕셔너리 유지 확인
    assert restored.semantic_info == {}, \
        f"빈 semantic_info가 유지되지 않음: {restored.semantic_info}"
    assert restored.screen_transition == {}, \
        f"빈 screen_transition이 유지되지 않음: {restored.screen_transition}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
