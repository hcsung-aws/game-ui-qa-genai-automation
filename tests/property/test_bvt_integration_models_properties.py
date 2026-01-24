"""
Property-based tests for BVT-Semantic Integration Data Models

**Feature: bvt-semantic-integration, Property 2: BVT_Test_Case round-trip**
**Feature: bvt-semantic-integration, Property 4: Semantic_Test_Case round-trip**
**Feature: bvt-semantic-integration, Property 11: Play_Test_Case round-trip**

Validates: Requirements 1.5, 2.7, 4.8
"""

import os
import sys
from datetime import datetime
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.bvt_integration.models import (
    BVTTestCase,
    ActionSummary,
    SemanticSummary,
    ActionRange,
    BVTReference,
    MatchResult,
    SemanticAction,
    SemanticTestCase,
    PlayTestCase,
    PlayTestResult,
    TestStatus,
    MatchingReport,
    PipelineResult
)


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
    max_size=100
)

# 비어있지 않은 텍스트 전략
non_empty_text_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\x00'
    ),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip() != '')

# 테스트 결과 전략
test_result_strategy = st.sampled_from([
    "Not Tested", "PASS", "Fail", "N/A", "Block"
])

# BVTTestCase 전략
bvt_test_case_strategy = st.builds(
    BVTTestCase,
    no=st.integers(min_value=1, max_value=10000),
    category1=safe_text_strategy,
    category2=safe_text_strategy,
    category3=safe_text_strategy,
    check=safe_text_strategy,
    test_result=test_result_strategy,
    bts_id=safe_text_strategy,
    comment=safe_text_strategy
)

# ActionSummary 전략
action_summary_strategy = st.builds(
    ActionSummary,
    test_case_name=non_empty_text_strategy,
    intents=st.lists(safe_text_strategy, min_size=0, max_size=10),
    target_elements=st.lists(safe_text_strategy, min_size=0, max_size=10),
    screen_states=st.lists(safe_text_strategy, min_size=0, max_size=10),
    action_descriptions=st.lists(safe_text_strategy, min_size=0, max_size=10),
    action_count=st.integers(min_value=0, max_value=1000)
)

# ActionRange 전략
action_range_strategy = st.builds(
    ActionRange,
    start_index=st.integers(min_value=0, max_value=100),
    end_index=st.integers(min_value=0, max_value=100)
).filter(lambda ar: ar.start_index <= ar.end_index)

# BVTReference 전략
bvt_reference_strategy = st.builds(
    BVTReference,
    no=st.integers(min_value=1, max_value=10000),
    category1=safe_text_strategy,
    category2=safe_text_strategy,
    category3=safe_text_strategy,
    check=safe_text_strategy
)

# 좌표 전략
coordinate_strategy = st.integers(min_value=0, max_value=3840)

# SemanticAction 전략
semantic_action_strategy = st.builds(
    SemanticAction,
    timestamp=st.datetimes().map(lambda dt: dt.isoformat()),
    action_type=st.sampled_from(['click', 'key_press', 'scroll', 'wait']),
    x=coordinate_strategy,
    y=coordinate_strategy,
    description=safe_text_strategy,
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
    semantic_info=st.fixed_dictionaries({
        "intent": safe_text_strategy,
        "target_element": st.fixed_dictionaries({
            "type": st.sampled_from(['button', 'icon', 'text_field', 'unknown']),
            "text": safe_text_strategy
        }),
        "context": st.fixed_dictionaries({
            "screen_state": safe_text_strategy
        })
    }),
    screen_transition=st.fixed_dictionaries({
        "before_state": safe_text_strategy,
        "after_state": safe_text_strategy,
        "transition_type": st.sampled_from(['none', 'minor_change', 'full_transition'])
    })
)

# SemanticTestCase 전략
semantic_test_case_strategy = st.builds(
    SemanticTestCase,
    name=non_empty_text_strategy,
    created_at=st.datetimes().map(lambda dt: dt.isoformat()),
    actions=st.lists(semantic_action_strategy, min_size=0, max_size=5),
    json_path=safe_text_strategy
)

# PlayTestCase 전략
play_test_case_strategy = st.builds(
    PlayTestCase,
    name=non_empty_text_strategy,
    bvt_reference=bvt_reference_strategy,
    source_test_case=non_empty_text_strategy,
    actions=st.lists(semantic_action_strategy, min_size=0, max_size=5),
    created_at=st.datetimes().map(lambda dt: dt.isoformat())
)

# TestStatus 전략
test_status_strategy = st.sampled_from(list(TestStatus))

# PlayTestResult 전략
play_test_result_strategy = st.builds(
    PlayTestResult,
    play_test_name=non_empty_text_strategy,
    bvt_no=st.integers(min_value=1, max_value=10000),
    status=test_status_strategy,
    executed_actions=st.integers(min_value=0, max_value=100),
    failed_actions=st.integers(min_value=0, max_value=100),
    screenshots=st.lists(safe_text_strategy, min_size=0, max_size=10),
    error_message=st.one_of(st.none(), safe_text_strategy),
    execution_time=st.floats(min_value=0.0, max_value=3600.0, allow_nan=False, allow_infinity=False)
)

# MatchResult 전략
match_result_strategy = st.builds(
    MatchResult,
    bvt_case=bvt_test_case_strategy,
    matched_test_case=st.one_of(st.none(), non_empty_text_strategy),
    action_range=st.one_of(st.none(), action_range_strategy),
    confidence_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    is_high_confidence=st.booleans(),
    match_details=st.fixed_dictionaries({
        "method": st.sampled_from(['text_similarity', 'category_match']),
        "score_breakdown": st.fixed_dictionaries({
            "text_score": st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
        })
    })
)

# SemanticSummary 전략
semantic_summary_strategy = st.builds(
    SemanticSummary,
    generated_at=st.datetimes().map(lambda dt: dt.isoformat()),
    test_case_summaries=st.lists(action_summary_strategy, min_size=0, max_size=5),
    total_test_cases=st.integers(min_value=0, max_value=100),
    total_actions=st.integers(min_value=0, max_value=1000)
)

# MatchingReport 전략
matching_report_strategy = st.builds(
    MatchingReport,
    generated_at=st.datetimes().map(lambda dt: dt.isoformat()),
    total_bvt_items=st.integers(min_value=0, max_value=1000),
    matched_items=st.integers(min_value=0, max_value=1000),
    unmatched_items=st.integers(min_value=0, max_value=1000),
    high_confidence_matches=st.lists(match_result_strategy, min_size=0, max_size=3),
    low_confidence_matches=st.lists(match_result_strategy, min_size=0, max_size=3),
    unmatched_bvt_cases=st.lists(bvt_test_case_strategy, min_size=0, max_size=3),
    coverage_percentage=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
)

# PipelineResult 전략
pipeline_result_strategy = st.builds(
    PipelineResult,
    success=st.booleans(),
    bvt_output_path=st.one_of(st.none(), safe_text_strategy),
    report_json_path=st.one_of(st.none(), safe_text_strategy),
    report_md_path=st.one_of(st.none(), safe_text_strategy),
    play_tests_dir=st.one_of(st.none(), safe_text_strategy),
    matching_report=st.one_of(st.none(), matching_report_strategy),
    error_message=st.one_of(st.none(), safe_text_strategy),
    execution_time=st.floats(min_value=0.0, max_value=3600.0, allow_nan=False, allow_infinity=False)
)


# ============================================================================
# Property 2: BVT_Test_Case round-trip
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(bvt_case=bvt_test_case_strategy)
def test_bvt_test_case_round_trip(bvt_case):
    """
    **Feature: bvt-semantic-integration, Property 2: BVT_Test_Case round-trip**
    
    *For any* 유효한 BVT_Test_Case 객체, to_dict()로 직렬화한 후 
    from_dict()로 역직렬화하면 원본과 동등한 객체가 생성되어야 한다.
    
    **Validates: Requirements 1.5**
    """
    # 직렬화
    serialized = bvt_case.to_dict()
    
    # 역직렬화
    restored = BVTTestCase.from_dict(serialized)
    
    # 동등성 검증
    assert restored == bvt_case, \
        f"BVTTestCase round-trip 실패: {restored} != {bvt_case}"
    
    # 개별 필드 검증
    assert restored.no == bvt_case.no, f"no 불일치: {restored.no} != {bvt_case.no}"
    assert restored.category1 == bvt_case.category1, f"category1 불일치"
    assert restored.category2 == bvt_case.category2, f"category2 불일치"
    assert restored.category3 == bvt_case.category3, f"category3 불일치"
    assert restored.check == bvt_case.check, f"check 불일치"
    assert restored.test_result == bvt_case.test_result, f"test_result 불일치"
    assert restored.bts_id == bvt_case.bts_id, f"bts_id 불일치"
    assert restored.comment == bvt_case.comment, f"comment 불일치"


@settings(max_examples=100, deadline=None)
@given(bvt_case=bvt_test_case_strategy)
def test_bvt_test_case_double_round_trip(bvt_case):
    """
    **Feature: bvt-semantic-integration, Property 2 확장: 이중 round-trip**
    
    *For any* BVT_Test_Case, 두 번 연속 직렬화/역직렬화해도 결과가 동일해야 한다.
    
    **Validates: Requirements 1.5**
    """
    # 첫 번째 round-trip
    serialized1 = bvt_case.to_dict()
    restored1 = BVTTestCase.from_dict(serialized1)
    
    # 두 번째 round-trip
    serialized2 = restored1.to_dict()
    restored2 = BVTTestCase.from_dict(serialized2)
    
    # 두 번째 결과가 첫 번째와 동일해야 함
    assert restored2 == restored1, "이중 round-trip 후 결과가 다릅니다"
    assert serialized2 == serialized1, "이중 round-trip 후 직렬화 결과가 다릅니다"


# ============================================================================
# Property 4: Semantic_Test_Case round-trip
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(test_case=semantic_test_case_strategy)
def test_semantic_test_case_round_trip(test_case):
    """
    **Feature: bvt-semantic-integration, Property 4: Semantic_Test_Case round-trip**
    
    *For any* 유효한 Semantic_Test_Case 객체, to_dict()로 직렬화한 후 
    from_dict()로 역직렬화하면 원본과 동등한 객체가 생성되어야 한다.
    
    **Validates: Requirements 2.7**
    """
    # 직렬화
    serialized = test_case.to_dict()
    
    # 역직렬화
    restored = SemanticTestCase.from_dict(serialized)
    
    # 동등성 검증
    assert restored == test_case, \
        f"SemanticTestCase round-trip 실패"
    
    # 개별 필드 검증
    assert restored.name == test_case.name, f"name 불일치"
    assert restored.created_at == test_case.created_at, f"created_at 불일치"
    assert restored.json_path == test_case.json_path, f"json_path 불일치"
    assert len(restored.actions) == len(test_case.actions), f"actions 길이 불일치"
    
    # 각 액션 검증
    for i, (orig_action, rest_action) in enumerate(zip(test_case.actions, restored.actions)):
        assert rest_action == orig_action, f"action[{i}] 불일치"


@settings(max_examples=100, deadline=None)
@given(test_case=semantic_test_case_strategy)
def test_semantic_test_case_double_round_trip(test_case):
    """
    **Feature: bvt-semantic-integration, Property 4 확장: 이중 round-trip**
    
    *For any* Semantic_Test_Case, 두 번 연속 직렬화/역직렬화해도 결과가 동일해야 한다.
    
    **Validates: Requirements 2.7**
    """
    # 첫 번째 round-trip
    serialized1 = test_case.to_dict()
    restored1 = SemanticTestCase.from_dict(serialized1)
    
    # 두 번째 round-trip
    serialized2 = restored1.to_dict()
    restored2 = SemanticTestCase.from_dict(serialized2)
    
    # 두 번째 결과가 첫 번째와 동일해야 함
    assert restored2 == restored1, "이중 round-trip 후 결과가 다릅니다"


# ============================================================================
# Property 11: Play_Test_Case round-trip
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(play_test=play_test_case_strategy)
def test_play_test_case_round_trip(play_test):
    """
    **Feature: bvt-semantic-integration, Property 11: Play_Test_Case round-trip**
    
    *For any* 유효한 Play_Test_Case 객체, to_dict()로 직렬화한 후 
    from_dict()로 역직렬화하면 원본과 동등한 객체가 생성되어야 한다.
    
    **Validates: Requirements 4.8**
    """
    # 직렬화
    serialized = play_test.to_dict()
    
    # 역직렬화
    restored = PlayTestCase.from_dict(serialized)
    
    # 동등성 검증
    assert restored == play_test, \
        f"PlayTestCase round-trip 실패"
    
    # 개별 필드 검증
    assert restored.name == play_test.name, f"name 불일치"
    assert restored.source_test_case == play_test.source_test_case, f"source_test_case 불일치"
    assert restored.created_at == play_test.created_at, f"created_at 불일치"
    
    # BVT Reference 검증
    assert restored.bvt_reference == play_test.bvt_reference, f"bvt_reference 불일치"
    
    # 액션 검증
    assert len(restored.actions) == len(play_test.actions), f"actions 길이 불일치"
    for i, (orig_action, rest_action) in enumerate(zip(play_test.actions, restored.actions)):
        assert rest_action == orig_action, f"action[{i}] 불일치"


@settings(max_examples=100, deadline=None)
@given(play_test=play_test_case_strategy)
def test_play_test_case_double_round_trip(play_test):
    """
    **Feature: bvt-semantic-integration, Property 11 확장: 이중 round-trip**
    
    *For any* Play_Test_Case, 두 번 연속 직렬화/역직렬화해도 결과가 동일해야 한다.
    
    **Validates: Requirements 4.8**
    """
    # 첫 번째 round-trip
    serialized1 = play_test.to_dict()
    restored1 = PlayTestCase.from_dict(serialized1)
    
    # 두 번째 round-trip
    serialized2 = restored1.to_dict()
    restored2 = PlayTestCase.from_dict(serialized2)
    
    # 두 번째 결과가 첫 번째와 동일해야 함
    assert restored2 == restored1, "이중 round-trip 후 결과가 다릅니다"


# ============================================================================
# 추가 데이터 모델 round-trip 테스트
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(action_summary=action_summary_strategy)
def test_action_summary_round_trip(action_summary):
    """
    ActionSummary round-trip 테스트
    
    **Validates: Requirements 2.4**
    """
    serialized = action_summary.to_dict()
    restored = ActionSummary.from_dict(serialized)
    
    assert restored == action_summary, "ActionSummary round-trip 실패"


@settings(max_examples=100, deadline=None)
@given(semantic_summary=semantic_summary_strategy)
def test_semantic_summary_round_trip(semantic_summary):
    """
    SemanticSummary round-trip 테스트
    
    **Validates: Requirements 2.4**
    """
    serialized = semantic_summary.to_dict()
    restored = SemanticSummary.from_dict(serialized)
    
    assert restored == semantic_summary, "SemanticSummary round-trip 실패"


@settings(max_examples=100, deadline=None)
@given(action_range=action_range_strategy)
def test_action_range_round_trip(action_range):
    """
    ActionRange round-trip 테스트
    
    **Validates: Requirements 3.1**
    """
    serialized = action_range.to_dict()
    restored = ActionRange.from_dict(serialized)
    
    assert restored == action_range, "ActionRange round-trip 실패"
    assert restored.length == action_range.length, "ActionRange length 불일치"


@settings(max_examples=100, deadline=None)
@given(bvt_ref=bvt_reference_strategy)
def test_bvt_reference_round_trip(bvt_ref):
    """
    BVTReference round-trip 테스트
    
    **Validates: Requirements 4.1**
    """
    serialized = bvt_ref.to_dict()
    restored = BVTReference.from_dict(serialized)
    
    assert restored == bvt_ref, "BVTReference round-trip 실패"


@settings(max_examples=100, deadline=None)
@given(match_result=match_result_strategy)
def test_match_result_round_trip(match_result):
    """
    MatchResult round-trip 테스트
    
    **Validates: Requirements 3.1**
    """
    serialized = match_result.to_dict()
    restored = MatchResult.from_dict(serialized)
    
    assert restored == match_result, "MatchResult round-trip 실패"
    assert restored.is_matched == match_result.is_matched, "is_matched 불일치"


@settings(max_examples=100, deadline=None)
@given(play_result=play_test_result_strategy)
def test_play_test_result_round_trip(play_result):
    """
    PlayTestResult round-trip 테스트
    
    **Validates: Requirements 5.1**
    """
    serialized = play_result.to_dict()
    restored = PlayTestResult.from_dict(serialized)
    
    assert restored == play_result, "PlayTestResult round-trip 실패"


@settings(max_examples=100, deadline=None)
@given(report=matching_report_strategy)
def test_matching_report_round_trip(report):
    """
    MatchingReport round-trip 테스트
    
    **Validates: Requirements 6.1**
    """
    serialized = report.to_dict()
    restored = MatchingReport.from_dict(serialized)
    
    assert restored == report, "MatchingReport round-trip 실패"


@settings(max_examples=100, deadline=None)
@given(result=pipeline_result_strategy)
def test_pipeline_result_round_trip(result):
    """
    PipelineResult round-trip 테스트
    
    **Validates: Requirements 7.1**
    """
    serialized = result.to_dict()
    restored = PipelineResult.from_dict(serialized)
    
    assert restored == result, "PipelineResult round-trip 실패"


@settings(max_examples=100, deadline=None)
@given(action=semantic_action_strategy)
def test_semantic_action_round_trip(action):
    """
    SemanticAction round-trip 테스트
    
    **Validates: Requirements 4.1**
    """
    serialized = action.to_dict()
    restored = SemanticAction.from_dict(serialized)
    
    assert restored == action, "SemanticAction round-trip 실패"


# ============================================================================
# 단위 테스트
# ============================================================================

def test_test_status_values():
    """TestStatus 열거형 값 테스트"""
    assert TestStatus.PASS.value == "PASS"
    assert TestStatus.FAIL.value == "Fail"
    assert TestStatus.BLOCKED.value == "Block"
    assert TestStatus.NOT_TESTED.value == "Not Tested"
    assert TestStatus.NA.value == "N/A"


def test_action_range_length():
    """ActionRange length 속성 테스트"""
    ar = ActionRange(start_index=0, end_index=5)
    assert ar.length == 6
    
    ar2 = ActionRange(start_index=3, end_index=3)
    assert ar2.length == 1


def test_match_result_is_matched():
    """MatchResult is_matched 속성 테스트"""
    bvt_case = BVTTestCase(
        no=1, category1="Test", category2="", category3="",
        check="Check", test_result="Not Tested", bts_id="", comment=""
    )
    
    # 매칭된 경우
    matched = MatchResult(
        bvt_case=bvt_case,
        matched_test_case="test_case_1",
        confidence_score=0.8
    )
    assert matched.is_matched is True
    
    # 매칭되지 않은 경우
    unmatched = MatchResult(
        bvt_case=bvt_case,
        matched_test_case=None,
        confidence_score=0.0
    )
    assert unmatched.is_matched is False


def test_play_test_result_status_from_string():
    """PlayTestResult status 문자열 변환 테스트"""
    data = {
        "play_test_name": "test",
        "bvt_no": 1,
        "status": "PASS"
    }
    result = PlayTestResult.from_dict(data)
    assert result.status == TestStatus.PASS
    
    data["status"] = "Fail"
    result = PlayTestResult.from_dict(data)
    assert result.status == TestStatus.FAIL
    
    # 잘못된 상태는 NOT_TESTED로 처리
    data["status"] = "Invalid"
    result = PlayTestResult.from_dict(data)
    assert result.status == TestStatus.NOT_TESTED
