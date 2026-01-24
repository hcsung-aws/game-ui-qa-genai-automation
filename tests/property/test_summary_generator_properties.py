"""
Property-based tests for SemanticSummaryGenerator

**Feature: bvt-semantic-integration, Property 3: Semantic_Summary 생성 정확성**

Validates: Requirements 2.1, 2.4, 2.5, 2.6
"""

import os
import sys
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.bvt_integration.models import (
    SemanticTestCase,
    SemanticAction,
    SemanticSummary,
    ActionSummary
)
from src.bvt_integration.summary_generator import SemanticSummaryGenerator


# ============================================================================
# Strategies (전략 정의)
# ============================================================================

# 텍스트 전략 (유효한 문자열만)
safe_text_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\x00'
    ),
    min_size=0,
    max_size=50
)

# 비어있지 않은 텍스트 전략
non_empty_text_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\x00'
    ),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != '')

# 좌표 전략
coordinate_strategy = st.integers(min_value=0, max_value=1920)

# semantic_info 전략 (intent, target_element, context 포함)
semantic_info_strategy = st.fixed_dictionaries({
    "intent": non_empty_text_strategy,
    "target_element": non_empty_text_strategy,
    "context": non_empty_text_strategy
})

# screen_transition 전략
screen_transition_strategy = st.fixed_dictionaries({
    "before_state": safe_text_strategy,
    "after_state": safe_text_strategy,
    "transition_type": st.sampled_from(['none', 'minor_change', 'full_transition'])
})

# SemanticAction 전략 (semantic_info 포함)
semantic_action_with_info_strategy = st.builds(
    SemanticAction,
    timestamp=st.datetimes().map(lambda dt: dt.isoformat()),
    action_type=st.sampled_from(['click', 'key_press', 'scroll', 'wait']),
    x=coordinate_strategy,
    y=coordinate_strategy,
    description=non_empty_text_strategy,
    screenshot_path=st.one_of(st.none(), safe_text_strategy),
    button=st.one_of(st.none(), st.sampled_from(['left', 'right', 'middle'])),
    key=st.one_of(st.none(), st.sampled_from(['a', 'Enter', 'Space', 'Escape'])),
    scroll_dx=st.one_of(st.none(), st.integers(min_value=-100, max_value=100)),
    scroll_dy=st.one_of(st.none(), st.integers(min_value=-100, max_value=100)),
    screenshot_before_path=st.one_of(st.none(), safe_text_strategy),
    screenshot_after_path=st.one_of(st.none(), safe_text_strategy),
    click_region_crop_path=st.one_of(st.none(), safe_text_strategy),
    ui_state_hash_before=st.one_of(st.none(), safe_text_strategy),
    ui_state_hash_after=st.one_of(st.none(), safe_text_strategy),
    semantic_info=semantic_info_strategy,
    screen_transition=screen_transition_strategy
)

# SemanticAction 전략 (semantic_info 없음)
semantic_action_without_info_strategy = st.builds(
    SemanticAction,
    timestamp=st.datetimes().map(lambda dt: dt.isoformat()),
    action_type=st.sampled_from(['click', 'key_press', 'scroll', 'wait']),
    x=coordinate_strategy,
    y=coordinate_strategy,
    description=non_empty_text_strategy,
    screenshot_path=st.one_of(st.none(), safe_text_strategy),
    button=st.one_of(st.none(), st.sampled_from(['left', 'right', 'middle'])),
    key=st.one_of(st.none(), st.sampled_from(['a', 'Enter', 'Space', 'Escape'])),
    scroll_dx=st.one_of(st.none(), st.integers(min_value=-100, max_value=100)),
    scroll_dy=st.one_of(st.none(), st.integers(min_value=-100, max_value=100)),
    screenshot_before_path=st.one_of(st.none(), safe_text_strategy),
    screenshot_after_path=st.one_of(st.none(), safe_text_strategy),
    click_region_crop_path=st.one_of(st.none(), safe_text_strategy),
    ui_state_hash_before=st.one_of(st.none(), safe_text_strategy),
    ui_state_hash_after=st.one_of(st.none(), safe_text_strategy),
    semantic_info=st.just({}),
    screen_transition=st.just({})
)

# SemanticTestCase 전략 (semantic_info 포함 액션)
semantic_test_case_with_info_strategy = st.builds(
    SemanticTestCase,
    name=non_empty_text_strategy,
    created_at=st.datetimes().map(lambda dt: dt.isoformat()),
    actions=st.lists(semantic_action_with_info_strategy, min_size=1, max_size=5),
    json_path=safe_text_strategy
)

# SemanticTestCase 전략 (혼합 액션)
semantic_test_case_mixed_strategy = st.builds(
    SemanticTestCase,
    name=non_empty_text_strategy,
    created_at=st.datetimes().map(lambda dt: dt.isoformat()),
    actions=st.lists(
        st.one_of(semantic_action_with_info_strategy, semantic_action_without_info_strategy),
        min_size=0,
        max_size=5
    ),
    json_path=safe_text_strategy
)


# ============================================================================
# Property 3: Semantic_Summary 생성 정확성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(test_cases=st.lists(semantic_test_case_with_info_strategy, min_size=0, max_size=5))
def test_semantic_summary_generation_accuracy(test_cases):
    """
    **Feature: bvt-semantic-integration, Property 3: Semantic_Summary 생성 정확성**
    
    *For any* Semantic_Test_Case 리스트, SemanticSummaryGenerator로 생성한 
    Semantic_Summary는 각 테스트 케이스의 intent, target_element, context 정보를 
    포함하는 ActionSummary를 가져야 하고, total_test_cases는 입력 리스트의 길이와 같아야 한다.
    
    **Validates: Requirements 2.1, 2.4, 2.5, 2.6**
    """
    generator = SemanticSummaryGenerator()
    summary = generator.generate(test_cases)
    
    # total_test_cases는 입력 리스트의 길이와 같아야 함
    assert summary.total_test_cases == len(test_cases), \
        f"total_test_cases 불일치: {summary.total_test_cases} != {len(test_cases)}"
    
    # test_case_summaries 개수도 입력 리스트 길이와 같아야 함
    assert len(summary.test_case_summaries) == len(test_cases), \
        f"test_case_summaries 길이 불일치: {len(summary.test_case_summaries)} != {len(test_cases)}"
    
    # 각 테스트 케이스에 대한 ActionSummary 검증
    for i, (test_case, action_summary) in enumerate(zip(test_cases, summary.test_case_summaries)):
        # 테스트 케이스 이름 일치
        assert action_summary.test_case_name == test_case.name, \
            f"test_case_name 불일치 at index {i}"
        
        # 액션 수 일치
        assert action_summary.action_count == len(test_case.actions), \
            f"action_count 불일치 at index {i}: {action_summary.action_count} != {len(test_case.actions)}"


@settings(max_examples=100, deadline=None)
@given(test_cases=st.lists(semantic_test_case_with_info_strategy, min_size=1, max_size=5))
def test_semantic_summary_contains_intent_info(test_cases):
    """
    **Feature: bvt-semantic-integration, Property 3 확장: intent 정보 포함**
    
    *For any* semantic_info가 있는 테스트 케이스, 생성된 ActionSummary는 
    해당 intent 정보를 포함해야 한다.
    
    **Validates: Requirements 2.4, 2.5**
    """
    generator = SemanticSummaryGenerator()
    summary = generator.generate(test_cases)
    
    for test_case, action_summary in zip(test_cases, summary.test_case_summaries):
        # 테스트 케이스의 모든 intent 수집
        expected_intents = set()
        for action in test_case.actions:
            if action.semantic_info:
                intent = action.semantic_info.get("intent", "")
                if intent:
                    expected_intents.add(intent)
        
        # ActionSummary의 intents에 모든 expected_intents가 포함되어야 함
        actual_intents = set(action_summary.intents)
        assert expected_intents.issubset(actual_intents), \
            f"intent 누락: expected {expected_intents}, got {actual_intents}"


@settings(max_examples=100, deadline=None)
@given(test_cases=st.lists(semantic_test_case_with_info_strategy, min_size=1, max_size=5))
def test_semantic_summary_contains_target_element_info(test_cases):
    """
    **Feature: bvt-semantic-integration, Property 3 확장: target_element 정보 포함**
    
    *For any* semantic_info가 있는 테스트 케이스, 생성된 ActionSummary는 
    해당 target_element 정보를 포함해야 한다.
    
    **Validates: Requirements 2.4, 2.5**
    """
    generator = SemanticSummaryGenerator()
    summary = generator.generate(test_cases)
    
    for test_case, action_summary in zip(test_cases, summary.test_case_summaries):
        # 테스트 케이스의 모든 target_element 수집
        expected_targets = set()
        for action in test_case.actions:
            if action.semantic_info:
                target = action.semantic_info.get("target_element", "")
                if target:
                    expected_targets.add(target)
        
        # ActionSummary의 target_elements에 모든 expected_targets가 포함되어야 함
        actual_targets = set(action_summary.target_elements)
        assert expected_targets.issubset(actual_targets), \
            f"target_element 누락: expected {expected_targets}, got {actual_targets}"


@settings(max_examples=100, deadline=None)
@given(test_cases=st.lists(semantic_test_case_with_info_strategy, min_size=1, max_size=5))
def test_semantic_summary_contains_context_info(test_cases):
    """
    **Feature: bvt-semantic-integration, Property 3 확장: context 정보 포함**
    
    *For any* semantic_info가 있는 테스트 케이스, 생성된 ActionSummary는 
    해당 context 정보를 포함해야 한다.
    
    **Validates: Requirements 2.4, 2.5**
    """
    generator = SemanticSummaryGenerator()
    summary = generator.generate(test_cases)
    
    for test_case, action_summary in zip(test_cases, summary.test_case_summaries):
        # 테스트 케이스의 모든 context 수집
        expected_contexts = set()
        for action in test_case.actions:
            if action.semantic_info:
                context = action.semantic_info.get("context", "")
                if context:
                    expected_contexts.add(context)
        
        # ActionSummary의 screen_states에 모든 expected_contexts가 포함되어야 함
        actual_contexts = set(action_summary.screen_states)
        assert expected_contexts.issubset(actual_contexts), \
            f"context 누락: expected {expected_contexts}, got {actual_contexts}"


@settings(max_examples=100, deadline=None)
@given(test_cases=st.lists(semantic_test_case_mixed_strategy, min_size=0, max_size=5))
def test_semantic_summary_total_actions_count(test_cases):
    """
    **Feature: bvt-semantic-integration, Property 3 확장: total_actions 정확성**
    
    *For any* 테스트 케이스 리스트, total_actions는 모든 테스트 케이스의 
    액션 수 합계와 같아야 한다.
    
    **Validates: Requirements 2.4**
    """
    generator = SemanticSummaryGenerator()
    summary = generator.generate(test_cases)
    
    expected_total = sum(len(tc.actions) for tc in test_cases)
    
    assert summary.total_actions == expected_total, \
        f"total_actions 불일치: {summary.total_actions} != {expected_total}"


@settings(max_examples=100, deadline=None)
@given(test_cases=st.lists(semantic_test_case_mixed_strategy, min_size=1, max_size=5))
def test_semantic_summary_action_descriptions(test_cases):
    """
    **Feature: bvt-semantic-integration, Property 3 확장: action_descriptions 포함**
    
    *For any* 테스트 케이스, 생성된 ActionSummary는 모든 액션의 description을 포함해야 한다.
    
    **Validates: Requirements 2.5**
    """
    generator = SemanticSummaryGenerator()
    summary = generator.generate(test_cases)
    
    for test_case, action_summary in zip(test_cases, summary.test_case_summaries):
        # 테스트 케이스의 모든 description 수집
        expected_descriptions = []
        for action in test_case.actions:
            if action.description:
                expected_descriptions.append(action.description)
        
        # ActionSummary의 action_descriptions에 모든 expected_descriptions가 포함되어야 함
        assert action_summary.action_descriptions == expected_descriptions, \
            f"action_descriptions 불일치"


@settings(max_examples=100, deadline=None)
@given(test_case=semantic_test_case_with_info_strategy)
def test_extract_action_summary_single(test_case):
    """
    **Feature: bvt-semantic-integration, Property 3 확장: 단일 테스트 케이스 요약**
    
    *For any* 단일 테스트 케이스, extract_action_summary()는 올바른 ActionSummary를 반환해야 한다.
    
    **Validates: Requirements 2.4, 2.5, 2.6**
    """
    generator = SemanticSummaryGenerator()
    action_summary = generator.extract_action_summary(test_case)
    
    # 테스트 케이스 이름 일치
    assert action_summary.test_case_name == test_case.name
    
    # 액션 수 일치
    assert action_summary.action_count == len(test_case.actions)
    
    # ActionSummary는 유효한 구조여야 함
    assert isinstance(action_summary.intents, list)
    assert isinstance(action_summary.target_elements, list)
    assert isinstance(action_summary.screen_states, list)
    assert isinstance(action_summary.action_descriptions, list)


# ============================================================================
# 단위 테스트
# ============================================================================

def test_empty_test_cases_list():
    """빈 테스트 케이스 리스트 처리 테스트"""
    generator = SemanticSummaryGenerator()
    summary = generator.generate([])
    
    assert summary.total_test_cases == 0
    assert summary.total_actions == 0
    assert len(summary.test_case_summaries) == 0
    assert summary.generated_at != ""


def test_test_case_without_actions():
    """액션이 없는 테스트 케이스 처리 테스트"""
    test_case = SemanticTestCase(
        name="empty_test",
        created_at="2026-01-24T00:00:00",
        actions=[],
        json_path="test.json"
    )
    
    generator = SemanticSummaryGenerator()
    summary = generator.generate([test_case])
    
    assert summary.total_test_cases == 1
    assert summary.total_actions == 0
    assert len(summary.test_case_summaries) == 1
    assert summary.test_case_summaries[0].action_count == 0


def test_test_case_without_semantic_info():
    """semantic_info가 없는 액션 처리 테스트"""
    action = SemanticAction(
        timestamp="2026-01-24T00:00:00",
        action_type="click",
        x=100,
        y=200,
        description="클릭 테스트",
        semantic_info={},
        screen_transition={}
    )
    
    test_case = SemanticTestCase(
        name="no_semantic_test",
        created_at="2026-01-24T00:00:00",
        actions=[action],
        json_path="test.json"
    )
    
    generator = SemanticSummaryGenerator()
    summary = generator.generate([test_case])
    
    assert summary.total_test_cases == 1
    assert summary.total_actions == 1
    
    action_summary = summary.test_case_summaries[0]
    assert action_summary.action_count == 1
    assert action_summary.action_descriptions == ["클릭 테스트"]
    assert action_summary.intents == []
    assert action_summary.target_elements == []


def test_duplicate_intent_handling():
    """중복 intent 처리 테스트 - 중복 제거 확인"""
    actions = [
        SemanticAction(
            timestamp="2026-01-24T00:00:00",
            action_type="click",
            x=100,
            y=200,
            description="클릭 1",
            semantic_info={"intent": "navigate", "target_element": "button", "context": "main"}
        ),
        SemanticAction(
            timestamp="2026-01-24T00:00:01",
            action_type="click",
            x=150,
            y=250,
            description="클릭 2",
            semantic_info={"intent": "navigate", "target_element": "icon", "context": "main"}
        )
    ]
    
    test_case = SemanticTestCase(
        name="duplicate_test",
        created_at="2026-01-24T00:00:00",
        actions=actions,
        json_path="test.json"
    )
    
    generator = SemanticSummaryGenerator()
    action_summary = generator.extract_action_summary(test_case)
    
    # 중복 intent는 한 번만 포함되어야 함
    assert action_summary.intents.count("navigate") == 1
    
    # target_elements는 각각 포함되어야 함
    assert "button" in action_summary.target_elements
    assert "icon" in action_summary.target_elements
