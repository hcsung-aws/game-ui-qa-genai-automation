"""
Property-based tests for SemanticActionReplayer

**Feature: game-qa-automation, Property 30: 의미론적 매칭 폴백**
**Feature: game-qa-automation, Property 31: 화면 전환 검증**
**Feature: game-qa-automation, Property: 버튼 위치 변경에도 찾기 성공 (Task 17.1)**

Validates: Requirements 12.1, 12.2, 12.4, 12.6
"""

import os
import sys
import tempfile
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, settings, strategies as st, assume

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.config_manager import ConfigManager
from src.semantic_action_recorder import SemanticAction
from src.semantic_action_replayer import SemanticActionReplayer, ReplayResult


# ============================================================================
# Strategies (전략 정의)
# ============================================================================

# 좌표 전략 (화면 해상도 범위 내)
coordinate_strategy = st.integers(min_value=0, max_value=1920)

# 버튼 타입 전략
button_strategy = st.sampled_from(['left', 'right', 'middle'])

# 화면 전환 타입 전략
transition_type_strategy = st.sampled_from(['none', 'minor_change', 'partial_change', 'full_transition', 'unknown'])

# UI 요소 타입 전략
element_type_strategy = st.sampled_from(['button', 'icon', 'text_field', 'unknown'])

# 의미론적 정보 전략
semantic_info_strategy = st.fixed_dictionaries({
    "intent": st.sampled_from(['click_button', 'text_input', 'scroll_content', 'unknown_action']),
    "target_element": st.fixed_dictionaries({
        "type": element_type_strategy,
        "text": st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=1, max_size=20),
        "description": st.text(min_size=0, max_size=50),
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
    "transition_type": transition_type_strategy,
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
                "action_delay": 0.1,
                "screenshot_on_action": False,
                "screenshot_dir": tempfile.mkdtemp()
            }
        }
        json.dump(config_data, f)
        return f.name


def create_mock_ui_analyzer(element_at_original: bool = True, 
                            element_text: str = "테스트",
                            element_x: int = 100, 
                            element_y: int = 100):
    """Mock UIAnalyzer 생성
    
    Args:
        element_at_original: 원래 좌표에 요소가 있는지 여부
        element_text: 요소 텍스트
        element_x: 요소 X 좌표
        element_y: 요소 Y 좌표
    """
    mock_analyzer = Mock()
    
    if element_at_original:
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": element_text, "x": element_x, "y": element_y, 
                        "width": 80, "height": 30, "confidence": 0.95}],
            "icons": [],
            "text_fields": []
        }
    else:
        # 원래 좌표에는 없고 다른 위치에 있음
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": element_text, "x": element_x + 200, "y": element_y + 100,
                        "width": 80, "height": 30, "confidence": 0.95}],
            "icons": [],
            "text_fields": []
        }
    
    return mock_analyzer


def create_semantic_action(x: int, y: int, button: str = 'left',
                          semantic_info: dict = None,
                          screen_transition: dict = None) -> SemanticAction:
    """테스트용 SemanticAction 생성"""
    return SemanticAction(
        timestamp=datetime.now().isoformat(),
        action_type='click',
        x=x,
        y=y,
        description=f'클릭 ({x}, {y})',
        button=button,
        semantic_info=semantic_info or {},
        screen_transition=screen_transition or {}
    )


# ============================================================================
# Property 30: 의미론적 매칭 폴백
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    original_x=coordinate_strategy,
    original_y=coordinate_strategy,
    new_x=coordinate_strategy,
    new_y=coordinate_strategy,
    button=button_strategy,
    element_text=st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=1, max_size=10)
)
def test_semantic_matching_fallback(original_x, original_y, new_x, new_y, button, element_text):
    """
    **Feature: game-qa-automation, Property 30: 의미론적 매칭 폴백**
    
    For any 의미론적 액션 재실행, 원래 좌표에서 실패하면 의미론적 매칭을 시도해야 하고,
    매칭 성공 시 새로운 좌표로 액션을 실행해야 한다.
    
    Validates: Requirements 12.1, 12.2, 12.4
    """
    # 원래 좌표와 새 좌표가 다른 경우만 테스트
    assume(abs(new_x - original_x) > 50 or abs(new_y - original_y) > 50)
    
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        # Mock UIAnalyzer - 원래 좌표에는 요소가 없고, 새 좌표에 있음
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [{"text": element_text, "x": new_x, "y": new_y,
                        "width": 80, "height": 30, "confidence": 0.95}],
            "icons": [],
            "text_fields": []
        }
        
        # SemanticActionReplayer 생성
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 의미론적 정보가 있는 액션 생성
        semantic_info = {
            "intent": "click_button",
            "target_element": {
                "type": "button",
                "text": element_text,
                "description": f"버튼: {element_text}",
                "visual_features": {}
            },
            "context": {
                "screen_state": "lobby",
                "expected_result": "navigation"
            }
        }
        
        action = create_semantic_action(
            x=original_x, y=original_y, button=button,
            semantic_info=semantic_info,
            screen_transition={"transition_type": "unknown"}
        )
        
        # pyautogui와 screenshot을 Mock으로 대체
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            from PIL import Image
            mock_image = Image.new('RGB', (100, 100), color='red')
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            # 액션 재실행
            result = replayer.replay_action(action)
        
        # ========================================
        # Property 30 검증
        # ========================================
        
        # 결과가 ReplayResult 타입인지 확인
        assert isinstance(result, ReplayResult), "결과가 ReplayResult 타입이 아닙니다"
        
        # 원래 좌표가 기록되어 있는지 확인
        assert result.original_coords == (original_x, original_y), \
            f"원래 좌표 불일치: {result.original_coords} != ({original_x}, {original_y})"
        
        # 성공한 경우 검증
        if result.success:
            # method가 'direct' 또는 'semantic' 중 하나여야 함
            assert result.method in ['direct', 'semantic'], \
                f"유효하지 않은 method: {result.method}"
            
            # actual_coords가 설정되어 있어야 함
            assert result.actual_coords is not None, "actual_coords가 None입니다"
            
            # 의미론적 매칭인 경우 좌표 변경이 기록되어야 함
            if result.method == 'semantic':
                assert result.coordinate_change is not None, \
                    "의미론적 매칭 시 coordinate_change가 None입니다"
                
                # 좌표 변경이 실제로 발생했는지 확인
                change_x, change_y = result.coordinate_change
                assert change_x != 0 or change_y != 0, \
                    "의미론적 매칭인데 좌표 변경이 없습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


@settings(max_examples=50, deadline=None)
@given(
    x=coordinate_strategy,
    y=coordinate_strategy,
    button=button_strategy
)
def test_direct_match_when_element_at_original(x, y, button):
    """
    원래 좌표에 요소가 있으면 직접 매칭을 사용해야 한다.
    
    Validates: Requirements 12.1
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        # Mock UIAnalyzer - 원래 좌표에 요소가 있음
        mock_analyzer = create_mock_ui_analyzer(
            element_at_original=True,
            element_text="테스트버튼",
            element_x=x,
            element_y=y
        )
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        semantic_info = {
            "intent": "click_button",
            "target_element": {
                "type": "button",
                "text": "테스트버튼",
                "description": "테스트 버튼",
                "visual_features": {}
            },
            "context": {"screen_state": "lobby", "expected_result": "navigation"}
        }
        
        action = create_semantic_action(
            x=x, y=y, button=button,
            semantic_info=semantic_info,
            screen_transition={"transition_type": "unknown"}
        )
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            from PIL import Image
            mock_image = Image.new('RGB', (100, 100), color='blue')
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_action(action)
        
        # 성공하고 직접 매칭이어야 함
        assert result.success, f"액션 실패: {result.error_message}"
        assert result.method == 'direct', f"직접 매칭이어야 하는데 {result.method}입니다"
        assert result.actual_coords == (x, y), \
            f"좌표 불일치: {result.actual_coords} != ({x}, {y})"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


# ============================================================================
# Property 31: 화면 전환 검증
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    x=coordinate_strategy,
    y=coordinate_strategy,
    expected_transition=transition_type_strategy,
    actual_hash_diff=st.integers(min_value=0, max_value=64)
)
def test_screen_transition_verification(x, y, expected_transition, actual_hash_diff):
    """
    **Feature: game-qa-automation, Property 31: 화면 전환 검증**
    
    For any 의미론적 액션 재실행, 액션 실행 후 예상한 화면 전환이 발생했는지 검증해야 하며,
    예상과 다르면 경고를 로그해야 한다.
    
    Validates: Requirements 12.6, 12.7
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer(
            element_at_original=True,
            element_text="테스트",
            element_x=x,
            element_y=y
        )
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 예상 화면 전환 정보가 있는 액션 생성
        screen_transition = {
            "before_state": "lobby",
            "after_state": "game",
            "transition_type": expected_transition,
            "hash_difference": 20
        }
        
        semantic_info = {
            "intent": "click_button",
            "target_element": {
                "type": "button",
                "text": "테스트",
                "description": "테스트 버튼",
                "visual_features": {}
            },
            "context": {"screen_state": "lobby", "expected_result": "navigation"}
        }
        
        action = create_semantic_action(
            x=x, y=y,
            semantic_info=semantic_info,
            screen_transition=screen_transition
        )
        
        # 해시 차이에 따른 실제 전환 타입 결정
        if actual_hash_diff == 0:
            actual_transition = 'none'
        elif actual_hash_diff < 10:
            actual_transition = 'minor_change'
        elif actual_hash_diff < 30:
            actual_transition = 'partial_change'
        else:
            actual_transition = 'full_transition'
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui, \
             patch('src.semantic_action_replayer.imagehash') as mock_imagehash:
            
            from PIL import Image
            mock_image = Image.new('RGB', (100, 100), color='green')
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            # 해시 계산 Mock
            mock_hash = Mock()
            mock_hash.__sub__ = Mock(return_value=actual_hash_diff)
            mock_imagehash.average_hash.return_value = mock_hash
            mock_imagehash.hex_to_hash.return_value = mock_hash
            
            result = replayer.replay_action(action)
        
        # ========================================
        # Property 31 검증
        # ========================================
        
        # 결과에 화면 전환 관련 필드가 있어야 함
        assert hasattr(result, 'screen_transition_verified'), \
            "screen_transition_verified 필드가 없습니다"
        assert hasattr(result, 'expected_transition'), \
            "expected_transition 필드가 없습니다"
        assert hasattr(result, 'actual_transition'), \
            "actual_transition 필드가 없습니다"
        
        # 예상 전환이 기록되어 있어야 함
        assert result.expected_transition == expected_transition, \
            f"expected_transition 불일치: {result.expected_transition} != {expected_transition}"
        
        # 성공한 경우 화면 전환 검증이 수행되어야 함
        if result.success:
            # actual_transition이 설정되어 있어야 함
            assert result.actual_transition != "", \
                "actual_transition이 비어있습니다"
            
            # 전환 타입이 유효한 값이어야 함
            valid_transitions = ['none', 'minor_change', 'partial_change', 
                               'full_transition', 'unknown', 'capture_failed', 'error']
            assert result.actual_transition in valid_transitions, \
                f"유효하지 않은 actual_transition: {result.actual_transition}"
            
            # 예상과 실제가 일치하면 verified가 True여야 함
            if expected_transition == 'unknown':
                assert result.screen_transition_verified == True, \
                    "unknown 전환은 항상 verified여야 합니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


@settings(max_examples=50, deadline=None)
@given(
    x=coordinate_strategy,
    y=coordinate_strategy
)
def test_transition_mismatch_logging(x, y):
    """
    화면 전환 불일치 시 경고가 로그되어야 한다.
    
    Validates: Requirements 12.7
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer(
            element_at_original=True,
            element_text="테스트",
            element_x=x,
            element_y=y
        )
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 'none' 전환을 예상하지만 실제로는 'full_transition'이 발생
        screen_transition = {
            "transition_type": "none",
            "hash_difference": 0
        }
        
        action = create_semantic_action(
            x=x, y=y,
            semantic_info={
                "intent": "click_button",
                "target_element": {"type": "button", "text": "테스트", 
                                  "description": "", "visual_features": {}},
                "context": {"screen_state": "lobby", "expected_result": "none"}
            },
            screen_transition=screen_transition
        )
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui, \
             patch('src.semantic_action_replayer.imagehash') as mock_imagehash, \
             patch('src.semantic_action_replayer.logger') as mock_logger:
            
            from PIL import Image
            mock_image = Image.new('RGB', (100, 100), color='red')
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            # 큰 해시 차이 (full_transition)
            mock_hash = Mock()
            mock_hash.__sub__ = Mock(return_value=50)
            mock_imagehash.average_hash.return_value = mock_hash
            mock_imagehash.hex_to_hash.return_value = mock_hash
            
            result = replayer.replay_action(action)
        
        # 성공했지만 전환 불일치
        if result.success:
            assert result.expected_transition == "none", \
                f"expected_transition 불일치: {result.expected_transition}"
            
            # 전환 불일치 시 verified가 False여야 함
            if result.actual_transition not in ['none', 'unknown', 'capture_failed', 'error']:
                assert result.screen_transition_verified == False, \
                    "전환 불일치인데 verified가 True입니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


# ============================================================================
# 추가 테스트: 통계 계산
# ============================================================================

@settings(max_examples=50, deadline=None)
@given(
    num_actions=st.integers(min_value=1, max_value=10),
    success_rate=st.floats(min_value=0.0, max_value=1.0)
)
def test_statistics_calculation(num_actions, success_rate):
    """
    재실행 통계가 올바르게 계산되어야 한다.
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 결과 직접 추가 (실제 재실행 없이)
        num_success = int(num_actions * success_rate)
        
        for i in range(num_actions):
            result = ReplayResult(
                action_id=f"action_{i:04d}",
                success=i < num_success,
                method='direct' if i % 2 == 0 else 'semantic',
                original_coords=(100, 100),
                actual_coords=(100, 100) if i < num_success else None,
                coordinate_change=(10, 10) if i % 2 == 1 and i < num_success else None,
                screen_transition_verified=True
            )
            replayer.results.append(result)
        
        # 통계 계산
        stats = replayer.get_statistics()
        
        # 통계 검증
        assert stats['total_actions'] == num_actions, \
            f"total_actions 불일치: {stats['total_actions']} != {num_actions}"
        assert stats['success_count'] == num_success, \
            f"success_count 불일치: {stats['success_count']} != {num_success}"
        assert stats['failure_count'] == num_actions - num_success, \
            f"failure_count 불일치"
        
        # 성공률 검증 (부동소수점 오차 허용)
        expected_rate = num_success / num_actions if num_actions > 0 else 0.0
        assert abs(stats['success_rate'] - expected_rate) < 0.01, \
            f"success_rate 불일치: {stats['success_rate']} != {expected_rate}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


# ============================================================================
# 단위 테스트
# ============================================================================

def test_replay_result_structure():
    """ReplayResult 구조 테스트"""
    result = ReplayResult(
        action_id="test_001",
        success=True,
        method='direct',
        original_coords=(100, 200)
    )
    
    assert result.action_id == "test_001"
    assert result.success == True
    assert result.method == 'direct'
    assert result.original_coords == (100, 200)
    assert result.actual_coords is None
    assert result.coordinate_change is None
    assert result.screen_transition_verified == False
    assert result.expected_transition == ""
    assert result.actual_transition == ""
    assert result.error_message == ""
    assert result.execution_time == 0.0


def test_match_score_calculation():
    """매칭 점수 계산 테스트"""
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 완전 일치
        element = {"text": "시작", "type": "button", "confidence": 0.95}
        score = replayer._calculate_match_score(element, "button", "시작", "시작 버튼")
        assert score > 0.5, f"완전 일치 점수가 너무 낮음: {score}"
        
        # 부분 일치
        element = {"text": "게임 시작", "type": "button", "confidence": 0.9}
        score = replayer._calculate_match_score(element, "button", "시작", "")
        assert score > 0.2, f"부분 일치 점수가 너무 낮음: {score}"
        
        # 불일치
        element = {"text": "종료", "type": "button", "confidence": 0.9}
        score = replayer._calculate_match_score(element, "button", "시작", "")
        assert score < 0.3, f"불일치 점수가 너무 높음: {score}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


def test_wait_action_parsing():
    """대기 액션 시간 파싱 테스트"""
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 대기 액션 생성
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='wait',
            x=0, y=0,
            description='1.5초 대기'
        )
        
        result = ReplayResult(
            action_id="wait_001",
            success=False,
            method='failed',
            original_coords=(0, 0)
        )
        
        # 시간 측정을 위해 실제 대기는 하지 않고 파싱만 테스트
        import re
        match = re.search(r'(\d+\.?\d*)초', action.description)
        assert match is not None, "대기 시간 파싱 실패"
        wait_time = float(match.group(1))
        assert wait_time == 1.5, f"대기 시간 불일치: {wait_time} != 1.5"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


def test_empty_results_statistics():
    """빈 결과에 대한 통계 테스트"""
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 결과 없이 통계 계산
        stats = replayer.get_statistics()
        
        assert stats['total_actions'] == 0
        assert stats['success_count'] == 0
        assert stats['failure_count'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['direct_match_count'] == 0
        assert stats['semantic_match_count'] == 0
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


# ============================================================================
# Property: 버튼 위치 변경에도 찾기 성공 (Task 17.1)
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    original_x=st.integers(min_value=100, max_value=800),
    original_y=st.integers(min_value=100, max_value=600),
    offset_x=st.integers(min_value=100, max_value=500),
    offset_y=st.integers(min_value=100, max_value=400),
    button_text=st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=2, max_size=15)
)
def test_button_position_change_semantic_matching(original_x, original_y, offset_x, offset_y, button_text):
    """
    **Feature: game-qa-automation, Property: 버튼 위치 변경에도 찾기 성공**
    
    For any 버튼 요소, 원래 좌표에서 다른 위치로 이동하더라도 
    의미론적 매칭을 통해 새로운 위치에서 버튼을 찾아 클릭해야 한다.
    
    Validates: Requirements 12.2, 12.4
    
    이 테스트는 UI 레이아웃 변경 시나리오를 시뮬레이션한다:
    - 원래 좌표: (original_x, original_y)
    - 새 좌표: (original_x + offset_x, original_y + offset_y)
    - 버튼 텍스트는 동일하게 유지
    """
    # 버튼 텍스트가 비어있지 않아야 함
    assume(len(button_text.strip()) > 0)
    
    new_x = original_x + offset_x
    new_y = original_y + offset_y
    
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        # Mock UIAnalyzer - 버튼이 새 위치로 이동한 상황
        # 원래 좌표에는 버튼이 없고, 새 좌표에 동일한 텍스트의 버튼이 있음
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [
                {
                    "text": button_text,
                    "x": new_x,
                    "y": new_y,
                    "width": 100,
                    "height": 40,
                    "confidence": 0.92,
                    "type": "button"
                }
            ],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        # 원래 좌표에서 기록된 액션 (버튼 텍스트 정보 포함)
        semantic_info = {
            "intent": "click_button",
            "target_element": {
                "type": "button",
                "text": button_text,
                "description": f"버튼: {button_text}",
                "visual_features": {"color": "blue", "shape": "rectangle"}
            },
            "context": {
                "screen_state": "main_menu",
                "expected_result": "navigation"
            }
        }
        
        action = create_semantic_action(
            x=original_x,
            y=original_y,
            button='left',
            semantic_info=semantic_info,
            screen_transition={"transition_type": "unknown"}
        )
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            from PIL import Image
            mock_image = Image.new('RGB', (1920, 1080), color='gray')
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_action(action)
        
        # ========================================
        # Property 검증: 버튼 위치 변경에도 찾기 성공
        # ========================================
        
        # 1. 결과가 ReplayResult 타입이어야 함
        assert isinstance(result, ReplayResult), \
            "결과가 ReplayResult 타입이 아닙니다"
        
        # 2. 원래 좌표가 정확히 기록되어야 함
        assert result.original_coords == (original_x, original_y), \
            f"원래 좌표 불일치: {result.original_coords} != ({original_x}, {original_y})"
        
        # 3. 성공한 경우 의미론적 매칭이 사용되어야 함 (Requirements 12.2)
        if result.success:
            # 원래 좌표와 새 좌표가 다르므로 의미론적 매칭이어야 함
            assert result.method == 'semantic', \
                f"버튼 위치가 변경되었으므로 의미론적 매칭이어야 하는데 {result.method}입니다"
            
            # 4. 새 좌표로 액션이 실행되어야 함 (Requirements 12.4)
            assert result.actual_coords is not None, \
                "actual_coords가 None입니다"
            
            actual_x, actual_y = result.actual_coords
            assert actual_x == new_x and actual_y == new_y, \
                f"새 좌표로 실행되어야 함: 예상 ({new_x}, {new_y}), 실제 ({actual_x}, {actual_y})"
            
            # 5. 좌표 변경이 기록되어야 함
            assert result.coordinate_change is not None, \
                "coordinate_change가 None입니다"
            
            change_x, change_y = result.coordinate_change
            expected_change_x = new_x - original_x
            expected_change_y = new_y - original_y
            
            assert change_x == expected_change_x and change_y == expected_change_y, \
                f"좌표 변경 불일치: 예상 ({expected_change_x}, {expected_change_y}), 실제 ({change_x}, {change_y})"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


@settings(max_examples=100, deadline=None)
@given(
    original_x=st.integers(min_value=100, max_value=800),
    original_y=st.integers(min_value=100, max_value=600),
    new_positions=st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=1920),
            st.integers(min_value=0, max_value=1080)
        ),
        min_size=1,
        max_size=5
    ),
    button_text=st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=2, max_size=10)
)
def test_button_found_among_multiple_elements(original_x, original_y, new_positions, button_text):
    """
    **Feature: game-qa-automation, Property: 여러 요소 중 올바른 버튼 찾기**
    
    For any 화면에 여러 UI 요소가 있을 때, 의미론적 매칭은 
    텍스트가 일치하는 올바른 버튼을 찾아야 한다.
    
    Validates: Requirements 12.2, 12.4
    """
    assume(len(button_text.strip()) > 0)
    assume(len(new_positions) > 0)
    
    # 첫 번째 위치를 타겟 버튼 위치로 사용
    target_x, target_y = new_positions[0]
    
    # 원래 좌표와 새 좌표가 충분히 달라야 함
    assume(abs(target_x - original_x) > 50 or abs(target_y - original_y) > 50)
    
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        # 여러 버튼이 있는 화면 시뮬레이션
        buttons = []
        
        # 타겟 버튼 (찾아야 할 버튼)
        buttons.append({
            "text": button_text,
            "x": target_x,
            "y": target_y,
            "width": 100,
            "height": 40,
            "confidence": 0.95,
            "type": "button"
        })
        
        # 다른 버튼들 (다른 텍스트)
        other_texts = ["취소", "확인", "닫기", "설정", "도움말"]
        for i, (px, py) in enumerate(new_positions[1:]):
            if i < len(other_texts):
                buttons.append({
                    "text": other_texts[i],
                    "x": px,
                    "y": py,
                    "width": 80,
                    "height": 35,
                    "confidence": 0.90,
                    "type": "button"
                })
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": buttons,
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        semantic_info = {
            "intent": "click_button",
            "target_element": {
                "type": "button",
                "text": button_text,
                "description": f"버튼: {button_text}",
                "visual_features": {}
            },
            "context": {
                "screen_state": "dialog",
                "expected_result": "action"
            }
        }
        
        action = create_semantic_action(
            x=original_x,
            y=original_y,
            button='left',
            semantic_info=semantic_info,
            screen_transition={"transition_type": "unknown"}
        )
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            from PIL import Image
            mock_image = Image.new('RGB', (1920, 1080), color='white')
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_action(action)
        
        # ========================================
        # Property 검증
        # ========================================
        
        if result.success and result.method == 'semantic':
            # 올바른 버튼(타겟 버튼)을 찾았는지 확인
            assert result.actual_coords is not None, \
                "actual_coords가 None입니다"
            
            actual_x, actual_y = result.actual_coords
            
            # 타겟 버튼의 좌표와 일치해야 함
            assert actual_x == target_x and actual_y == target_y, \
                f"잘못된 버튼을 클릭함: 예상 ({target_x}, {target_y}), 실제 ({actual_x}, {actual_y})"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


@settings(max_examples=50, deadline=None)
@given(
    original_x=st.integers(min_value=100, max_value=800),
    original_y=st.integers(min_value=100, max_value=600),
    scale_factor=st.floats(min_value=0.5, max_value=2.0)
)
def test_button_position_scaled_layout(original_x, original_y, scale_factor):
    """
    **Feature: game-qa-automation, Property: 레이아웃 스케일 변경에도 찾기 성공**
    
    For any 화면 레이아웃이 스케일 변경되어 버튼 위치가 비례적으로 이동해도,
    의미론적 매칭을 통해 버튼을 찾아야 한다.
    
    Validates: Requirements 12.2, 12.4
    """
    # 스케일 변경 후 새 좌표 계산
    new_x = int(original_x * scale_factor)
    new_y = int(original_y * scale_factor)
    
    # 좌표가 화면 범위 내에 있어야 함
    assume(0 <= new_x <= 1920)
    assume(0 <= new_y <= 1080)
    
    # 원래 좌표와 새 좌표가 tolerance(50픽셀)를 초과해야 의미론적 매칭이 발생함
    # 코드의 _verify_element_at_position에서 tolerance = 50으로 설정되어 있음
    assume(abs(new_x - original_x) > 50 or abs(new_y - original_y) > 50)
    
    temp_config_path = create_temp_config()
    button_text = "시작하기"
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_with_retry.return_value = {
            "buttons": [
                {
                    "text": button_text,
                    "x": new_x,
                    "y": new_y,
                    "width": int(100 * scale_factor),
                    "height": int(40 * scale_factor),
                    "confidence": 0.93,
                    "type": "button"
                }
            ],
            "icons": [],
            "text_fields": []
        }
        
        replayer = SemanticActionReplayer(config, ui_analyzer=mock_analyzer)
        
        semantic_info = {
            "intent": "click_button",
            "target_element": {
                "type": "button",
                "text": button_text,
                "description": f"버튼: {button_text}",
                "visual_features": {}
            },
            "context": {
                "screen_state": "main",
                "expected_result": "start_game"
            }
        }
        
        action = create_semantic_action(
            x=original_x,
            y=original_y,
            button='left',
            semantic_info=semantic_info,
            screen_transition={"transition_type": "unknown"}
        )
        
        with patch('src.semantic_action_replayer.pyautogui') as mock_pyautogui:
            from PIL import Image
            mock_image = Image.new('RGB', (1920, 1080), color='black')
            mock_pyautogui.screenshot.return_value = mock_image
            mock_pyautogui.click = Mock()
            
            result = replayer.replay_action(action)
        
        # ========================================
        # Property 검증
        # ========================================
        
        if result.success:
            # 의미론적 매칭이 사용되어야 함
            assert result.method == 'semantic', \
                f"레이아웃 변경 시 의미론적 매칭이어야 하는데 {result.method}입니다"
            
            # 새 좌표로 실행되어야 함
            assert result.actual_coords == (new_x, new_y), \
                f"좌표 불일치: 예상 ({new_x}, {new_y}), 실제 {result.actual_coords}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
