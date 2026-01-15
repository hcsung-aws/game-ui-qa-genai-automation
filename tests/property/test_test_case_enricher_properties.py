"""
Property-based tests for TestCaseEnricher

**Feature: semantic-test-replay, Property 5: 보강 시 기존 데이터 보존**
**Feature: semantic-test-replay, Property 6: 레거시 테스트 케이스 감지 정확성**

Validates: Requirements 5.1, 5.6
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
from src.test_case_enricher import TestCaseEnricher, EnrichmentResult


# ============================================================================
# Strategies (전략 정의)
# ============================================================================

# 좌표 전략
coordinate_strategy = st.integers(min_value=0, max_value=3840)

# 타임스탬프 전략
timestamp_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('N', 'P')),
    min_size=10,
    max_size=30
).map(lambda _: datetime.now().isoformat())

# 설명 전략
description_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Z')),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip() != '')

# bounding_box 전략
bounding_box_strategy = st.fixed_dictionaries({
    "x": st.integers(min_value=0, max_value=3840),
    "y": st.integers(min_value=0, max_value=2160),
    "width": st.integers(min_value=0, max_value=500),
    "height": st.integers(min_value=0, max_value=500)
})

# 신뢰도 전략
confidence_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# 유효한 target_element 전략 (semantic_info가 있는 경우)
valid_target_element_strategy = st.fixed_dictionaries({
    "type": st.sampled_from(['button', 'icon', 'text_field']),
    "text": st.text(min_size=1, max_size=50),
    "description": st.text(min_size=0, max_size=100),
    "bounding_box": bounding_box_strategy,
    "confidence": confidence_strategy
})

# 유효한 semantic_info 전략 (레거시가 아닌 경우)
valid_semantic_info_strategy = st.fixed_dictionaries({
    "intent": st.sampled_from(['click_button', 'text_input', 'scroll_content']),
    "target_element": valid_target_element_strategy,
    "context": st.fixed_dictionaries({
        "screen_state": st.sampled_from(['lobby', 'game', 'menu']),
        "expected_result": st.sampled_from(['navigation', 'dialog', 'none'])
    })
})

# 빈 semantic_info 전략 (레거시인 경우)
empty_semantic_info_strategy = st.sampled_from([
    None,
    {},
    {"intent": "click_button"},  # target_element 없음
    {"intent": "click_button", "target_element": None},  # target_element가 None
    {"intent": "click_button", "target_element": {}},  # target_element가 빈 딕셔너리
])

# 클릭 액션 전략 (레거시)
legacy_click_action_strategy = st.fixed_dictionaries({
    "timestamp": timestamp_strategy,
    "action_type": st.just("click"),
    "x": coordinate_strategy,
    "y": coordinate_strategy,
    "description": description_strategy,
    "screenshot_path": st.text(min_size=5, max_size=50).map(lambda x: f"screenshots/{x}.png"),
    "button": st.sampled_from(['left', 'right', 'middle']),
    "semantic_info": empty_semantic_info_strategy
})

# 클릭 액션 전략 (유효한 semantic_info 포함)
valid_click_action_strategy = st.fixed_dictionaries({
    "timestamp": timestamp_strategy,
    "action_type": st.just("click"),
    "x": coordinate_strategy,
    "y": coordinate_strategy,
    "description": description_strategy,
    "screenshot_path": st.text(min_size=5, max_size=50).map(lambda x: f"screenshots/{x}.png"),
    "button": st.sampled_from(['left', 'right', 'middle']),
    "semantic_info": valid_semantic_info_strategy
})

# 대기 액션 전략 (클릭이 아닌 액션)
wait_action_strategy = st.fixed_dictionaries({
    "timestamp": timestamp_strategy,
    "action_type": st.just("wait"),
    "x": st.just(0),
    "y": st.just(0),
    "description": st.text(min_size=1, max_size=50).map(lambda x: f"{x}초 대기")
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
    
    def find_element_side_effect(ui_data, x, y, tolerance=100):
        """좌표에 따라 적절한 요소 반환"""
        for button in ui_data.get("buttons", []):
            result = button.copy()
            result["element_type"] = "button"
            return result
        return None
    
    mock_analyzer.find_element_at_position.side_effect = find_element_side_effect
    return mock_analyzer


# ============================================================================
# Property 6: 레거시 테스트 케이스 감지 정확성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    legacy_actions=st.lists(legacy_click_action_strategy, min_size=1, max_size=5),
    wait_actions=st.lists(wait_action_strategy, min_size=0, max_size=3)
)
def test_legacy_test_case_detection_with_missing_semantic_info(legacy_actions, wait_actions):
    """
    **Feature: semantic-test-replay, Property 6: 레거시 테스트 케이스 감지 정확성**
    
    *For any* 테스트 케이스에 대해, semantic_info 필드가 없거나 비어있는 
    클릭 액션이 하나라도 있으면 레거시로 감지되어야 한다.
    
    **Validates: Requirements 5.1**
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        # 레거시 클릭 액션과 대기 액션을 섞어서 테스트 케이스 생성
        all_actions = legacy_actions + wait_actions
        
        test_case = {
            "name": "test_legacy_detection",
            "version": "1.0",
            "actions": all_actions
        }
        
        # 레거시 감지 수행
        is_legacy = enricher.is_legacy_test_case(test_case)
        
        # 레거시 클릭 액션이 있으므로 반드시 레거시로 감지되어야 함
        assert is_legacy is True, \
            f"semantic_info가 없거나 비어있는 클릭 액션이 있는데 레거시로 감지되지 않았습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


@settings(max_examples=100, deadline=None)
@given(
    valid_actions=st.lists(valid_click_action_strategy, min_size=1, max_size=5),
    wait_actions=st.lists(wait_action_strategy, min_size=0, max_size=3)
)
def test_non_legacy_test_case_detection(valid_actions, wait_actions):
    """
    **Feature: semantic-test-replay, Property 6 확장: 유효한 테스트 케이스는 레거시가 아님**
    
    *For any* 테스트 케이스에 대해, 모든 클릭 액션에 유효한 semantic_info가 있으면
    레거시로 감지되지 않아야 한다.
    
    **Validates: Requirements 5.1**
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        # 유효한 클릭 액션과 대기 액션을 섞어서 테스트 케이스 생성
        all_actions = valid_actions + wait_actions
        
        test_case = {
            "name": "test_valid_detection",
            "version": "2.0",
            "actions": all_actions
        }
        
        # 레거시 감지 수행
        is_legacy = enricher.is_legacy_test_case(test_case)
        
        # 모든 클릭 액션에 유효한 semantic_info가 있으므로 레거시가 아니어야 함
        assert is_legacy is False, \
            f"모든 클릭 액션에 유효한 semantic_info가 있는데 레거시로 감지되었습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


@settings(max_examples=50, deadline=None)
@given(
    valid_actions=st.lists(valid_click_action_strategy, min_size=1, max_size=3),
    legacy_actions=st.lists(legacy_click_action_strategy, min_size=1, max_size=2)
)
def test_mixed_test_case_is_legacy(valid_actions, legacy_actions):
    """
    **Feature: semantic-test-replay, Property 6 확장: 혼합 테스트 케이스는 레거시**
    
    *For any* 테스트 케이스에 대해, 유효한 클릭 액션과 레거시 클릭 액션이 
    섞여 있으면 레거시로 감지되어야 한다.
    
    **Validates: Requirements 5.1**
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        # 유효한 액션과 레거시 액션을 섞어서 테스트 케이스 생성
        all_actions = valid_actions + legacy_actions
        
        test_case = {
            "name": "test_mixed_detection",
            "version": "1.5",
            "actions": all_actions
        }
        
        # 레거시 감지 수행
        is_legacy = enricher.is_legacy_test_case(test_case)
        
        # 레거시 클릭 액션이 하나라도 있으므로 레거시로 감지되어야 함
        assert is_legacy is True, \
            f"레거시 클릭 액션이 섞여 있는데 레거시로 감지되지 않았습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


@settings(max_examples=50, deadline=None)
@given(
    wait_actions=st.lists(wait_action_strategy, min_size=1, max_size=5)
)
def test_no_click_actions_is_not_legacy(wait_actions):
    """
    **Feature: semantic-test-replay, Property 6 확장: 클릭 액션이 없으면 레거시가 아님**
    
    *For any* 테스트 케이스에 대해, 클릭 액션이 없으면 레거시로 감지되지 않아야 한다.
    
    **Validates: Requirements 5.1**
    """
    temp_config_path = create_temp_config()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        test_case = {
            "name": "test_no_clicks",
            "version": "1.0",
            "actions": wait_actions
        }
        
        # 레거시 감지 수행
        is_legacy = enricher.is_legacy_test_case(test_case)
        
        # 클릭 액션이 없으므로 레거시가 아니어야 함
        assert is_legacy is False, \
            f"클릭 액션이 없는데 레거시로 감지되었습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


# ============================================================================
# Property 5: 보강 시 기존 데이터 보존
# ============================================================================

@settings(max_examples=50, deadline=None)
@given(
    legacy_action=legacy_click_action_strategy
)
def test_enrichment_preserves_existing_data(legacy_action):
    """
    **Feature: semantic-test-replay, Property 5: 보강 시 기존 데이터 보존**
    
    *For any* 레거시 테스트 케이스에 대해, 보강 후에도 기존의 
    screenshot_path, timestamp, x, y, description 등의 필드는 변경되지 않아야 한다.
    
    **Validates: Requirements 5.6**
    """
    temp_config_path = create_temp_config()
    temp_screenshot_dir = tempfile.mkdtemp()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        # 원본 값 저장
        original_timestamp = legacy_action.get("timestamp")
        original_x = legacy_action.get("x")
        original_y = legacy_action.get("y")
        original_description = legacy_action.get("description")
        original_screenshot_path = legacy_action.get("screenshot_path")
        original_button = legacy_action.get("button")
        original_action_type = legacy_action.get("action_type")
        
        test_case = {
            "name": "test_preservation",
            "version": "1.0",
            "actions": [legacy_action]
        }
        
        # 보강 수행 (스크린샷이 없으므로 스킵될 것임)
        enriched_test_case, result = enricher.enrich_test_case(test_case, temp_screenshot_dir)
        
        # 보강된 액션 가져오기
        enriched_action = enriched_test_case["actions"][0]
        
        # ========================================
        # 기존 필드 보존 검증 (Requirements: 5.6)
        # ========================================
        assert enriched_action.get("timestamp") == original_timestamp, \
            f"timestamp가 변경되었습니다: {enriched_action.get('timestamp')} != {original_timestamp}"
        
        assert enriched_action.get("x") == original_x, \
            f"x가 변경되었습니다: {enriched_action.get('x')} != {original_x}"
        
        assert enriched_action.get("y") == original_y, \
            f"y가 변경되었습니다: {enriched_action.get('y')} != {original_y}"
        
        assert enriched_action.get("description") == original_description, \
            f"description이 변경되었습니다: {enriched_action.get('description')} != {original_description}"
        
        assert enriched_action.get("screenshot_path") == original_screenshot_path, \
            f"screenshot_path가 변경되었습니다: {enriched_action.get('screenshot_path')} != {original_screenshot_path}"
        
        assert enriched_action.get("button") == original_button, \
            f"button이 변경되었습니다: {enriched_action.get('button')} != {original_button}"
        
        assert enriched_action.get("action_type") == original_action_type, \
            f"action_type이 변경되었습니다: {enriched_action.get('action_type')} != {original_action_type}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        import shutil
        if os.path.exists(temp_screenshot_dir):
            shutil.rmtree(temp_screenshot_dir, ignore_errors=True)


@settings(max_examples=50, deadline=None)
@given(
    valid_action=valid_click_action_strategy
)
def test_enrichment_preserves_existing_semantic_info(valid_action):
    """
    **Feature: semantic-test-replay, Property 5 확장: 이미 유효한 semantic_info는 보존**
    
    *For any* 이미 유효한 semantic_info가 있는 액션에 대해, 
    보강 시 기존 semantic_info를 덮어쓰지 않아야 한다.
    
    **Validates: Requirements 5.6**
    """
    temp_config_path = create_temp_config()
    temp_screenshot_dir = tempfile.mkdtemp()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        # 원본 semantic_info 저장
        original_semantic_info = valid_action.get("semantic_info")
        
        test_case = {
            "name": "test_semantic_preservation",
            "version": "2.0",
            "actions": [valid_action]
        }
        
        # 보강 수행
        enriched_test_case, result = enricher.enrich_test_case(test_case, temp_screenshot_dir)
        
        # 보강된 액션 가져오기
        enriched_action = enriched_test_case["actions"][0]
        
        # ========================================
        # 기존 semantic_info 보존 검증
        # ========================================
        enriched_semantic_info = enriched_action.get("semantic_info")
        
        # 이미 유효한 semantic_info가 있었으므로 스킵되어야 함
        assert enriched_semantic_info is not None, "semantic_info가 None이 되었습니다"
        
        # 원본 intent 보존
        assert enriched_semantic_info.get("intent") == original_semantic_info.get("intent"), \
            f"intent가 변경되었습니다"
        
        # 원본 target_element 보존
        orig_target = original_semantic_info.get("target_element", {})
        enr_target = enriched_semantic_info.get("target_element", {})
        
        assert enr_target.get("type") == orig_target.get("type"), \
            f"target_element.type이 변경되었습니다"
        assert enr_target.get("text") == orig_target.get("text"), \
            f"target_element.text가 변경되었습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        import shutil
        if os.path.exists(temp_screenshot_dir):
            shutil.rmtree(temp_screenshot_dir, ignore_errors=True)


@settings(max_examples=30, deadline=None)
@given(
    legacy_actions=st.lists(legacy_click_action_strategy, min_size=1, max_size=3),
    wait_actions=st.lists(wait_action_strategy, min_size=1, max_size=2)
)
def test_enrichment_result_counts_consistency(legacy_actions, wait_actions):
    """
    **Feature: semantic-test-replay, Property 5 확장: 보강 결과 카운트 일관성**
    
    *For any* 테스트 케이스에 대해, 보강 결과의 
    enriched_count + skipped_count + failed_count == total_actions 이어야 한다.
    
    **Validates: Requirements 5.4, 5.5**
    """
    temp_config_path = create_temp_config()
    temp_screenshot_dir = tempfile.mkdtemp()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        all_actions = legacy_actions + wait_actions
        
        test_case = {
            "name": "test_counts",
            "version": "1.0",
            "actions": all_actions
        }
        
        # 보강 수행
        enriched_test_case, result = enricher.enrich_test_case(test_case, temp_screenshot_dir)
        
        # ========================================
        # 카운트 일관성 검증
        # ========================================
        total_from_result = result.enriched_count + result.skipped_count + result.failed_count
        
        assert total_from_result == result.total_actions, \
            f"카운트 합계 불일치: {result.enriched_count} + {result.skipped_count} + {result.failed_count} = {total_from_result} != {result.total_actions}"
        
        assert result.total_actions == len(all_actions), \
            f"total_actions 불일치: {result.total_actions} != {len(all_actions)}"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        import shutil
        if os.path.exists(temp_screenshot_dir):
            shutil.rmtree(temp_screenshot_dir, ignore_errors=True)


@settings(max_examples=30, deadline=None)
@given(
    version=st.sampled_from(["1.0", "1.5", "2.0", "2.3", "10.0"])
)
def test_enrichment_increments_version(version):
    """
    **Feature: semantic-test-replay, Property 5 확장: 보강 시 버전 증가**
    
    *For any* 테스트 케이스에 대해, 보강 후 버전이 증가해야 한다.
    
    **Validates: Requirements 5.4**
    """
    temp_config_path = create_temp_config()
    temp_screenshot_dir = tempfile.mkdtemp()
    
    try:
        config = ConfigManager(temp_config_path)
        config.load_config()
        
        mock_analyzer = create_mock_ui_analyzer()
        enricher = TestCaseEnricher(config, ui_analyzer=mock_analyzer)
        
        test_case = {
            "name": "test_version",
            "version": version,
            "actions": []
        }
        
        # 보강 수행
        enriched_test_case, result = enricher.enrich_test_case(test_case, temp_screenshot_dir)
        
        # ========================================
        # 버전 증가 검증
        # ========================================
        new_version = enriched_test_case.get("version")
        
        assert new_version != version, \
            f"버전이 변경되지 않았습니다: {new_version}"
        
        # 버전 형식 검증 (X.Y 형식)
        parts = new_version.split(".")
        assert len(parts) >= 2, f"버전 형식이 올바르지 않습니다: {new_version}"
        
        # enriched_at 필드 존재 검증
        assert "enriched_at" in enriched_test_case, \
            "enriched_at 필드가 없습니다"
        
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        import shutil
        if os.path.exists(temp_screenshot_dir):
            shutil.rmtree(temp_screenshot_dir, ignore_errors=True)
