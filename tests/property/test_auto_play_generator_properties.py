"""
Property-based tests for AutoPlayGenerator

**Feature: bvt-semantic-integration, Property 10: Play_Test_Case 생성 정확성**

Validates: Requirements 4.1, 4.2, 4.3, 4.7
"""

import os
import sys
from datetime import datetime
from hypothesis import given, settings, strategies as st, assume

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.bvt_integration.models import (
    BVTTestCase,
    MatchResult,
    ActionRange,
    SemanticAction,
    SemanticTestCase,
    PlayTestCase,
    BVTReference
)
from src.bvt_integration.auto_play_generator import AutoPlayGenerator


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
    max_size=50
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

# 좌표 전략
coordinate_strategy = st.integers(min_value=0, max_value=1920)

# SemanticAction 전략 (간소화)
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
    semantic_info=st.just({}),
    screen_transition=st.just({})
)


# ============================================================================
# 복합 전략: 유효한 MatchResult + SemanticTestCase 쌍 생성
# ============================================================================

@st.composite
def valid_match_result_with_test_case(draw):
    """유효한 MatchResult와 SemanticTestCase 쌍 생성
    
    - 고신뢰도 매칭 (confidence >= 0.7)
    - 유효한 액션 범위
    - 테스트 케이스에 충분한 액션 포함
    """
    # 액션 수 결정 (최소 1개)
    num_actions = draw(st.integers(min_value=1, max_value=10))
    
    # 액션 리스트 생성
    actions = draw(st.lists(
        semantic_action_strategy,
        min_size=num_actions,
        max_size=num_actions
    ))
    
    # 유효한 액션 범위 생성
    start_index = draw(st.integers(min_value=0, max_value=max(0, num_actions - 1)))
    end_index = draw(st.integers(min_value=start_index, max_value=num_actions - 1))
    
    action_range = ActionRange(start_index=start_index, end_index=end_index)
    
    # 테스트 케이스 이름
    tc_name = draw(non_empty_text_strategy)
    
    # SemanticTestCase 생성
    test_case = SemanticTestCase(
        name=tc_name,
        created_at=datetime.now().isoformat(),
        actions=actions,
        json_path=f"test_cases/{tc_name}.json"
    )
    
    # BVTTestCase 생성
    bvt_case = draw(bvt_test_case_strategy)
    
    # 고신뢰도 MatchResult 생성
    confidence = draw(st.floats(min_value=0.7, max_value=1.0, allow_nan=False))
    
    match_result = MatchResult(
        bvt_case=bvt_case,
        matched_test_case=tc_name,
        action_range=action_range,
        confidence_score=confidence,
        is_high_confidence=True,
        match_details={"method": "test"}
    )
    
    return match_result, test_case


@st.composite
def low_confidence_match_result(draw):
    """저신뢰도 MatchResult 생성 (confidence < 0.7)"""
    bvt_case = draw(bvt_test_case_strategy)
    tc_name = draw(non_empty_text_strategy)
    
    # 저신뢰도
    confidence = draw(st.floats(min_value=0.0, max_value=0.69, allow_nan=False))
    
    action_range = ActionRange(start_index=0, end_index=0)
    
    return MatchResult(
        bvt_case=bvt_case,
        matched_test_case=tc_name,
        action_range=action_range,
        confidence_score=confidence,
        is_high_confidence=False,
        match_details={}
    )


# ============================================================================
# Property 10: Play_Test_Case 생성 정확성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(data=valid_match_result_with_test_case())
def test_play_test_case_generation_accuracy(data):
    """
    **Feature: bvt-semantic-integration, Property 10: Play_Test_Case 생성 정확성**
    
    *For any* 고신뢰도 Match_Result, AutoPlayGenerator.generate()의 결과인 
    Play_Test_Case는 Match_Result의 action_range에 해당하는 액션들만 포함하고, 
    BVT 참조 정보(no, categories, check)를 포함해야 한다.
    
    **Validates: Requirements 4.1, 4.2, 4.3, 4.7**
    """
    match_result, test_case = data
    
    # AutoPlayGenerator 생성
    generator = AutoPlayGenerator()
    
    # 테스트 케이스 캐시에 추가
    generator.cache_test_case(test_case)
    
    # PlayTestCase 생성
    play_test = generator.generate_from_test_case(match_result, test_case)
    
    # 생성 성공 확인
    assert play_test is not None, "고신뢰도 매칭에서 PlayTestCase 생성 실패"
    
    # 1. 액션 범위 검증 (Requirements: 4.2)
    expected_action_count = match_result.action_range.length
    actual_action_count = len(play_test.actions)
    
    assert actual_action_count == expected_action_count, \
        f"액션 수 불일치: 예상 {expected_action_count}, 실제 {actual_action_count}"
    
    # 2. 액션 내용 검증 - 범위 내 액션만 포함
    start_idx = match_result.action_range.start_index
    end_idx = match_result.action_range.end_index
    expected_actions = test_case.actions[start_idx:end_idx + 1]
    
    for i, (expected, actual) in enumerate(zip(expected_actions, play_test.actions)):
        assert expected == actual, f"액션 {i} 불일치"
    
    # 3. BVT 참조 정보 검증 (Requirements: 4.3)
    bvt_ref = play_test.bvt_reference
    bvt_case = match_result.bvt_case
    
    assert bvt_ref.no == bvt_case.no, \
        f"BVT no 불일치: {bvt_ref.no} != {bvt_case.no}"
    assert bvt_ref.category1 == bvt_case.category1, \
        f"category1 불일치: {bvt_ref.category1} != {bvt_case.category1}"
    assert bvt_ref.category2 == bvt_case.category2, \
        f"category2 불일치: {bvt_ref.category2} != {bvt_case.category2}"
    assert bvt_ref.category3 == bvt_case.category3, \
        f"category3 불일치: {bvt_ref.category3} != {bvt_case.category3}"
    assert bvt_ref.check == bvt_case.check, \
        f"check 불일치: {bvt_ref.check} != {bvt_case.check}"
    
    # 4. 원본 테스트 케이스 참조 검증
    assert play_test.source_test_case == test_case.name, \
        f"source_test_case 불일치: {play_test.source_test_case} != {test_case.name}"


@settings(max_examples=100, deadline=None)
@given(match_result=low_confidence_match_result())
def test_low_confidence_match_rejected(match_result):
    """
    **Feature: bvt-semantic-integration, Property 10 확장: 저신뢰도 매칭 거부**
    
    *For any* 저신뢰도 Match_Result (confidence < 0.7), 
    AutoPlayGenerator.generate()는 None을 반환해야 한다.
    
    **Validates: Requirements 4.1**
    """
    generator = AutoPlayGenerator()
    
    # 저신뢰도 매칭은 생성 실패해야 함
    play_test = generator.generate(match_result)
    
    assert play_test is None, \
        f"저신뢰도 매칭({match_result.confidence_score:.2f})에서 " \
        f"PlayTestCase가 생성됨"


@settings(max_examples=100, deadline=None)
@given(data=valid_match_result_with_test_case())
def test_play_test_case_has_valid_name(data):
    """
    **Feature: bvt-semantic-integration, Property 10 확장: 유효한 이름 생성**
    
    *For any* 고신뢰도 Match_Result, 생성된 Play_Test_Case는 
    BVT 번호를 포함하는 유효한 이름을 가져야 한다.
    
    **Validates: Requirements 4.7**
    """
    match_result, test_case = data
    
    generator = AutoPlayGenerator()
    generator.cache_test_case(test_case)
    
    play_test = generator.generate_from_test_case(match_result, test_case)
    
    assert play_test is not None
    
    # 이름에 BVT 번호 포함 확인
    bvt_no = match_result.bvt_case.no
    assert f"bvt_{bvt_no:04d}" in play_test.name, \
        f"PlayTestCase 이름에 BVT 번호가 없음: {play_test.name}"
    
    # 이름이 비어있지 않음
    assert len(play_test.name) > 0, "PlayTestCase 이름이 비어있음"


@settings(max_examples=100, deadline=None)
@given(data=valid_match_result_with_test_case())
def test_play_test_case_has_created_at(data):
    """
    **Feature: bvt-semantic-integration, Property 10 확장: 생성 시간 포함**
    
    *For any* 고신뢰도 Match_Result, 생성된 Play_Test_Case는 
    유효한 created_at 타임스탬프를 가져야 한다.
    
    **Validates: Requirements 4.7**
    """
    match_result, test_case = data
    
    generator = AutoPlayGenerator()
    generator.cache_test_case(test_case)
    
    play_test = generator.generate_from_test_case(match_result, test_case)
    
    assert play_test is not None
    
    # created_at이 비어있지 않음
    assert play_test.created_at, "created_at이 비어있음"
    
    # ISO 형식 파싱 가능
    try:
        datetime.fromisoformat(play_test.created_at)
    except ValueError:
        assert False, f"created_at이 ISO 형식이 아님: {play_test.created_at}"


@settings(max_examples=100, deadline=None)
@given(data=valid_match_result_with_test_case())
def test_play_test_case_action_range_boundary(data):
    """
    **Feature: bvt-semantic-integration, Property 10 확장: 액션 범위 경계 검증**
    
    *For any* 고신뢰도 Match_Result, 생성된 Play_Test_Case의 액션은 
    정확히 action_range의 start_index부터 end_index까지만 포함해야 한다.
    
    **Validates: Requirements 4.2**
    """
    match_result, test_case = data
    
    generator = AutoPlayGenerator()
    generator.cache_test_case(test_case)
    
    play_test = generator.generate_from_test_case(match_result, test_case)
    
    assert play_test is not None
    
    start_idx = match_result.action_range.start_index
    end_idx = match_result.action_range.end_index
    
    # 첫 번째 액션이 start_index의 액션과 일치
    if len(play_test.actions) > 0:
        assert play_test.actions[0] == test_case.actions[start_idx], \
            "첫 번째 액션이 start_index의 액션과 불일치"
    
    # 마지막 액션이 end_index의 액션과 일치
    if len(play_test.actions) > 0:
        assert play_test.actions[-1] == test_case.actions[end_idx], \
            "마지막 액션이 end_index의 액션과 불일치"


@settings(max_examples=50, deadline=None)
@given(data=valid_match_result_with_test_case())
def test_play_test_case_bvt_reference_complete(data):
    """
    **Feature: bvt-semantic-integration, Property 10 확장: BVT 참조 완전성**
    
    *For any* 고신뢰도 Match_Result, 생성된 Play_Test_Case의 bvt_reference는 
    모든 필수 필드(no, category1, category2, category3, check)를 포함해야 한다.
    
    **Validates: Requirements 4.3**
    """
    match_result, test_case = data
    
    generator = AutoPlayGenerator()
    generator.cache_test_case(test_case)
    
    play_test = generator.generate_from_test_case(match_result, test_case)
    
    assert play_test is not None
    
    bvt_ref = play_test.bvt_reference
    
    # 모든 필수 필드 존재 확인
    assert hasattr(bvt_ref, 'no'), "bvt_reference에 no 필드 없음"
    assert hasattr(bvt_ref, 'category1'), "bvt_reference에 category1 필드 없음"
    assert hasattr(bvt_ref, 'category2'), "bvt_reference에 category2 필드 없음"
    assert hasattr(bvt_ref, 'category3'), "bvt_reference에 category3 필드 없음"
    assert hasattr(bvt_ref, 'check'), "bvt_reference에 check 필드 없음"
    
    # BVTReference 타입 확인
    assert isinstance(bvt_ref, BVTReference), \
        f"bvt_reference 타입 불일치: {type(bvt_ref)}"


# ============================================================================
# 단위 테스트
# ============================================================================

def test_generator_initialization():
    """AutoPlayGenerator 초기화 테스트"""
    generator = AutoPlayGenerator()
    
    assert generator.replayer is None
    assert generator.config is None
    assert generator.tc_loader is not None
    assert generator.screenshot_dir == "screenshots"


def test_generator_with_custom_screenshot_dir():
    """커스텀 스크린샷 디렉토리 설정 테스트"""
    generator = AutoPlayGenerator(screenshot_dir="custom_screenshots")
    
    assert generator.screenshot_dir == "custom_screenshots"


def test_cache_test_case():
    """테스트 케이스 캐싱 테스트"""
    generator = AutoPlayGenerator()
    
    test_case = SemanticTestCase(
        name="test_case_1",
        created_at=datetime.now().isoformat(),
        actions=[],
        json_path="test_cases/test_case_1.json"
    )
    
    generator.cache_test_case(test_case)
    
    assert test_case.json_path in generator._test_cases_cache
    assert generator._test_cases_cache[test_case.json_path] == test_case


def test_clear_cache():
    """캐시 초기화 테스트"""
    generator = AutoPlayGenerator()
    
    test_case = SemanticTestCase(
        name="test_case_1",
        created_at=datetime.now().isoformat(),
        actions=[],
        json_path="test_cases/test_case_1.json"
    )
    
    generator.cache_test_case(test_case)
    assert len(generator._test_cases_cache) > 0
    
    generator.clear_cache()
    assert len(generator._test_cases_cache) == 0


def test_generate_with_no_action_range():
    """액션 범위 없는 매칭 결과 처리 테스트"""
    generator = AutoPlayGenerator()
    
    bvt_case = BVTTestCase(
        no=1, category1="Test", category2="", category3="",
        check="Check", test_result="Not Tested", bts_id="", comment=""
    )
    
    match_result = MatchResult(
        bvt_case=bvt_case,
        matched_test_case="test_case",
        action_range=None,  # 액션 범위 없음
        confidence_score=0.8,
        is_high_confidence=True
    )
    
    play_test = generator.generate(match_result)
    
    assert play_test is None


def test_generate_with_unmatched_result():
    """매칭되지 않은 결과 처리 테스트"""
    generator = AutoPlayGenerator()
    
    bvt_case = BVTTestCase(
        no=1, category1="Test", category2="", category3="",
        check="Check", test_result="Not Tested", bts_id="", comment=""
    )
    
    match_result = MatchResult(
        bvt_case=bvt_case,
        matched_test_case=None,  # 매칭 없음
        action_range=ActionRange(0, 0),
        confidence_score=0.0,
        is_high_confidence=False
    )
    
    play_test = generator.generate(match_result)
    
    assert play_test is None


def test_play_test_name_format():
    """플레이 테스트 이름 형식 테스트"""
    generator = AutoPlayGenerator()
    
    bvt_case = BVTTestCase(
        no=42, category1="Test", category2="", category3="",
        check="Check", test_result="Not Tested", bts_id="", comment=""
    )
    
    match_result = MatchResult(
        bvt_case=bvt_case,
        matched_test_case="test_case",
        action_range=ActionRange(0, 0),
        confidence_score=0.8,
        is_high_confidence=True
    )
    
    name = generator._generate_play_test_name(match_result)
    
    # 이름 형식: bvt_XXXX_play_YYYYMMDD_HHMMSS
    assert name.startswith("bvt_0042_play_")
    assert len(name) > len("bvt_0042_play_")
