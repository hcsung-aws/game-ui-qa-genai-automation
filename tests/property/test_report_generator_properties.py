"""
Property-based tests for ReportGenerator

**Feature: bvt-semantic-integration, Property 15: 리포트 구조 정확성**
**Feature: bvt-semantic-integration, Property 16: 커버리지 계산 정확성**

Validates: Requirements 6.1, 6.2, 6.3, 6.4
"""

import os
import sys
import json
from hypothesis import given, settings, strategies as st, assume

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.bvt_integration.models import (
    BVTTestCase,
    MatchResult,
    ActionRange,
    MatchingReport
)
from src.bvt_integration.report_generator import ReportGenerator


# ============================================================================
# Strategies (전략 정의)
# ============================================================================

# 텍스트 전략 (유효한 문자열만)
safe_text_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\x00\n\r|'
    ),
    min_size=0,
    max_size=50
)

# 비어있지 않은 텍스트 전략
non_empty_text_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\x00\n\r|'
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

# ActionRange 전략
action_range_strategy = st.builds(
    ActionRange,
    start_index=st.integers(min_value=0, max_value=100),
    end_index=st.integers(min_value=0, max_value=100)
).filter(lambda ar: ar.start_index <= ar.end_index)


# 고신뢰도 MatchResult 전략 (매칭됨, 신뢰도 >= 0.7)
high_confidence_match_strategy = st.builds(
    MatchResult,
    bvt_case=bvt_test_case_strategy,
    matched_test_case=non_empty_text_strategy,
    action_range=st.one_of(st.none(), action_range_strategy),
    confidence_score=st.floats(min_value=0.7, max_value=1.0, allow_nan=False, allow_infinity=False),
    is_high_confidence=st.just(True),
    match_details=st.just({})
)

# 저신뢰도 MatchResult 전략 (매칭됨, 신뢰도 < 0.7)
low_confidence_match_strategy = st.builds(
    MatchResult,
    bvt_case=bvt_test_case_strategy,
    matched_test_case=non_empty_text_strategy,
    action_range=st.one_of(st.none(), action_range_strategy),
    confidence_score=st.floats(min_value=0.0, max_value=0.69, allow_nan=False, allow_infinity=False),
    is_high_confidence=st.just(False),
    match_details=st.just({})
)

# 미매칭 MatchResult 전략
unmatched_result_strategy = st.builds(
    MatchResult,
    bvt_case=bvt_test_case_strategy,
    matched_test_case=st.none(),
    action_range=st.none(),
    confidence_score=st.just(0.0),
    is_high_confidence=st.just(False),
    match_details=st.just({})
)

# 혼합 MatchResult 리스트 전략
mixed_match_results_strategy = st.lists(
    st.one_of(
        high_confidence_match_strategy,
        low_confidence_match_strategy,
        unmatched_result_strategy
    ),
    min_size=0,
    max_size=20,
    unique_by=lambda x: x.bvt_case.no
)


# ============================================================================
# Property 15: 리포트 구조 정확성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(match_results=mixed_match_results_strategy)
def test_report_structure_accuracy(match_results):
    """
    **Feature: bvt-semantic-integration, Property 15: 리포트 구조 정확성**
    
    *For any* Match_Result 리스트, ReportGenerator.generate()의 결과인 
    MatchingReport는 total_bvt_items, matched_items, unmatched_items 카운트를 
    포함하고, high_confidence_matches와 unmatched_bvt_cases 리스트를 포함해야 한다.
    
    **Validates: Requirements 6.1, 6.2, 6.3**
    """
    generator = ReportGenerator()
    report = generator.generate(match_results)
    
    # 필수 필드 존재 확인
    assert hasattr(report, 'total_bvt_items'), "total_bvt_items 필드 누락"
    assert hasattr(report, 'matched_items'), "matched_items 필드 누락"
    assert hasattr(report, 'unmatched_items'), "unmatched_items 필드 누락"
    assert hasattr(report, 'high_confidence_matches'), "high_confidence_matches 필드 누락"
    assert hasattr(report, 'low_confidence_matches'), "low_confidence_matches 필드 누락"
    assert hasattr(report, 'unmatched_bvt_cases'), "unmatched_bvt_cases 필드 누락"
    assert hasattr(report, 'coverage_percentage'), "coverage_percentage 필드 누락"
    assert hasattr(report, 'generated_at'), "generated_at 필드 누락"
    
    # 총 항목 수 검증
    assert report.total_bvt_items == len(match_results), \
        f"total_bvt_items 불일치: {report.total_bvt_items} != {len(match_results)}"
    
    # 매칭/미매칭 합계 검증
    assert report.matched_items + report.unmatched_items == report.total_bvt_items, \
        "matched_items + unmatched_items != total_bvt_items"
    
    # 리스트 길이 검증
    total_in_lists = (
        len(report.high_confidence_matches) + 
        len(report.low_confidence_matches) + 
        len(report.unmatched_bvt_cases)
    )
    assert total_in_lists == report.total_bvt_items, \
        f"리스트 합계 불일치: {total_in_lists} != {report.total_bvt_items}"


@settings(max_examples=100, deadline=None)
@given(match_results=mixed_match_results_strategy)
def test_report_categorization_accuracy(match_results):
    """
    **Feature: bvt-semantic-integration, Property 15 확장: 분류 정확성**
    
    각 MatchResult가 올바른 카테고리에 분류되어야 한다.
    
    **Validates: Requirements 6.2, 6.3**
    """
    generator = ReportGenerator()
    report = generator.generate(match_results)
    
    # 고신뢰도 매칭 검증
    for match in report.high_confidence_matches:
        assert match.is_matched, "고신뢰도 매칭에 미매칭 결과가 포함됨"
        assert match.is_high_confidence, "고신뢰도 매칭에 저신뢰도 결과가 포함됨"
    
    # 저신뢰도 매칭 검증
    for match in report.low_confidence_matches:
        assert match.is_matched, "저신뢰도 매칭에 미매칭 결과가 포함됨"
        assert not match.is_high_confidence, "저신뢰도 매칭에 고신뢰도 결과가 포함됨"
    
    # 미매칭 검증 - unmatched_bvt_cases는 BVTTestCase 리스트
    # 원본 match_results에서 미매칭인 것들의 bvt_case와 일치해야 함
    unmatched_nos = {case.no for case in report.unmatched_bvt_cases}
    for result in match_results:
        if not result.is_matched:
            assert result.bvt_case.no in unmatched_nos, \
                f"미매칭 결과 {result.bvt_case.no}가 unmatched_bvt_cases에 없음"


# ============================================================================
# Property 16: 커버리지 계산 정확성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(match_results=mixed_match_results_strategy)
def test_coverage_calculation_accuracy(match_results):
    """
    **Feature: bvt-semantic-integration, Property 16: 커버리지 계산 정확성**
    
    *For any* MatchingReport, coverage_percentage는 
    (matched_items / total_bvt_items) * 100과 같아야 한다.
    
    **Validates: Requirements 6.4**
    """
    generator = ReportGenerator()
    report = generator.generate(match_results)
    
    if report.total_bvt_items > 0:
        expected_coverage = (report.matched_items / report.total_bvt_items) * 100
        assert abs(report.coverage_percentage - expected_coverage) < 0.001, \
            f"커버리지 계산 오류: {report.coverage_percentage} != {expected_coverage}"
    else:
        assert report.coverage_percentage == 0.0, \
            "빈 결과의 커버리지가 0이 아님"


@settings(max_examples=100, deadline=None)
@given(
    high_count=st.integers(min_value=0, max_value=10),
    low_count=st.integers(min_value=0, max_value=10),
    unmatched_count=st.integers(min_value=0, max_value=10)
)
def test_coverage_calculation_with_known_counts(high_count, low_count, unmatched_count):
    """
    **Feature: bvt-semantic-integration, Property 16 확장: 알려진 카운트로 검증**
    
    정확한 카운트로 커버리지를 검증한다.
    
    **Validates: Requirements 6.4**
    """
    generator = ReportGenerator()
    
    # 테스트 데이터 생성
    match_results = []
    bvt_no = 1
    
    # 고신뢰도 매칭
    for _ in range(high_count):
        match_results.append(MatchResult(
            bvt_case=BVTTestCase(
                no=bvt_no, category1="Test", category2="", category3="",
                check="Check", test_result="Not Tested", bts_id="", comment=""
            ),
            matched_test_case="test_case",
            confidence_score=0.8,
            is_high_confidence=True
        ))
        bvt_no += 1
    
    # 저신뢰도 매칭
    for _ in range(low_count):
        match_results.append(MatchResult(
            bvt_case=BVTTestCase(
                no=bvt_no, category1="Test", category2="", category3="",
                check="Check", test_result="Not Tested", bts_id="", comment=""
            ),
            matched_test_case="test_case",
            confidence_score=0.5,
            is_high_confidence=False
        ))
        bvt_no += 1
    
    # 미매칭
    for _ in range(unmatched_count):
        match_results.append(MatchResult(
            bvt_case=BVTTestCase(
                no=bvt_no, category1="Test", category2="", category3="",
                check="Check", test_result="Not Tested", bts_id="", comment=""
            ),
            matched_test_case=None,
            confidence_score=0.0,
            is_high_confidence=False
        ))
        bvt_no += 1
    
    report = generator.generate(match_results)
    
    # 카운트 검증
    total = high_count + low_count + unmatched_count
    matched = high_count + low_count
    
    assert report.total_bvt_items == total
    assert report.matched_items == matched
    assert report.unmatched_items == unmatched_count
    assert len(report.high_confidence_matches) == high_count
    assert len(report.low_confidence_matches) == low_count
    assert len(report.unmatched_bvt_cases) == unmatched_count
    
    # 커버리지 검증
    if total > 0:
        expected_coverage = (matched / total) * 100
        assert abs(report.coverage_percentage - expected_coverage) < 0.001


@settings(max_examples=50, deadline=None)
@given(match_results=mixed_match_results_strategy)
def test_coverage_bounds(match_results):
    """
    커버리지는 항상 0~100 범위 내에 있어야 한다.
    
    **Validates: Requirements 6.4**
    """
    generator = ReportGenerator()
    report = generator.generate(match_results)
    
    assert 0.0 <= report.coverage_percentage <= 100.0, \
        f"커버리지가 범위를 벗어남: {report.coverage_percentage}"


# ============================================================================
# 출력 형식 테스트
# ============================================================================

@settings(max_examples=50, deadline=None)
@given(match_results=mixed_match_results_strategy)
def test_json_output_valid(match_results):
    """
    JSON 출력이 유효한 JSON 형식이어야 한다.
    
    **Validates: Requirements 6.5**
    """
    generator = ReportGenerator()
    report = generator.generate(match_results)
    
    json_str = generator.to_json(report)
    
    # JSON 파싱 가능해야 함
    parsed = json.loads(json_str)
    
    # 필수 필드 존재
    assert 'total_bvt_items' in parsed
    assert 'matched_items' in parsed
    assert 'unmatched_items' in parsed
    assert 'coverage_percentage' in parsed
    assert 'high_confidence_matches' in parsed
    assert 'unmatched_bvt_cases' in parsed


@settings(max_examples=50, deadline=None)
@given(match_results=mixed_match_results_strategy)
def test_markdown_output_structure(match_results):
    """
    Markdown 출력이 올바른 구조를 가져야 한다.
    
    **Validates: Requirements 6.5**
    """
    generator = ReportGenerator()
    report = generator.generate(match_results)
    
    md_str = generator.to_markdown(report)
    
    # 필수 섹션 존재
    assert "# BVT-Semantic 매칭 리포트" in md_str
    assert "## 요약" in md_str
    assert "## 고신뢰도 매칭" in md_str
    assert "## 미매칭 BVT 항목" in md_str
    
    # 통계 정보 포함
    assert f"총 BVT 항목: {report.total_bvt_items}" in md_str
    assert f"매칭된 항목: {report.matched_items}" in md_str
    assert f"미매칭 항목: {report.unmatched_items}" in md_str


# ============================================================================
# 단위 테스트
# ============================================================================

def test_generator_initialization():
    """ReportGenerator 초기화 테스트"""
    generator = ReportGenerator()
    assert generator is not None
    assert generator.HIGH_CONFIDENCE_THRESHOLD == 0.7


def test_empty_results():
    """빈 결과 처리 테스트"""
    generator = ReportGenerator()
    report = generator.generate([])
    
    assert report.total_bvt_items == 0
    assert report.matched_items == 0
    assert report.unmatched_items == 0
    assert report.coverage_percentage == 0.0
    assert len(report.high_confidence_matches) == 0
    assert len(report.low_confidence_matches) == 0
    assert len(report.unmatched_bvt_cases) == 0


def test_all_matched():
    """모든 항목이 매칭된 경우 테스트"""
    generator = ReportGenerator()
    
    match_results = [
        MatchResult(
            bvt_case=BVTTestCase(
                no=1, category1="Test", category2="", category3="",
                check="Check 1", test_result="Not Tested", bts_id="", comment=""
            ),
            matched_test_case="test_1",
            confidence_score=0.9,
            is_high_confidence=True
        ),
        MatchResult(
            bvt_case=BVTTestCase(
                no=2, category1="Test", category2="", category3="",
                check="Check 2", test_result="Not Tested", bts_id="", comment=""
            ),
            matched_test_case="test_2",
            confidence_score=0.85,
            is_high_confidence=True
        )
    ]
    
    report = generator.generate(match_results)
    
    assert report.total_bvt_items == 2
    assert report.matched_items == 2
    assert report.unmatched_items == 0
    assert report.coverage_percentage == 100.0


def test_all_unmatched():
    """모든 항목이 미매칭인 경우 테스트"""
    generator = ReportGenerator()
    
    match_results = [
        MatchResult(
            bvt_case=BVTTestCase(
                no=1, category1="Test", category2="", category3="",
                check="Check 1", test_result="Not Tested", bts_id="", comment=""
            ),
            matched_test_case=None,
            confidence_score=0.0,
            is_high_confidence=False
        ),
        MatchResult(
            bvt_case=BVTTestCase(
                no=2, category1="Test", category2="", category3="",
                check="Check 2", test_result="Not Tested", bts_id="", comment=""
            ),
            matched_test_case=None,
            confidence_score=0.0,
            is_high_confidence=False
        )
    ]
    
    report = generator.generate(match_results)
    
    assert report.total_bvt_items == 2
    assert report.matched_items == 0
    assert report.unmatched_items == 2
    assert report.coverage_percentage == 0.0


def test_category_formatting():
    """카테고리 포맷팅 테스트"""
    generator = ReportGenerator()
    
    # 모든 카테고리가 있는 경우
    bvt_case1 = BVTTestCase(
        no=1, category1="Main", category2="Sub", category3="Detail",
        check="Check", test_result="Not Tested", bts_id="", comment=""
    )
    assert generator._format_category(bvt_case1) == "Main > Sub > Detail"
    
    # 일부 카테고리만 있는 경우
    bvt_case2 = BVTTestCase(
        no=2, category1="Main", category2="", category3="",
        check="Check", test_result="Not Tested", bts_id="", comment=""
    )
    assert generator._format_category(bvt_case2) == "Main"
    
    # 카테고리가 없는 경우
    bvt_case3 = BVTTestCase(
        no=3, category1="", category2="", category3="",
        check="Check", test_result="Not Tested", bts_id="", comment=""
    )
    assert generator._format_category(bvt_case3) == "-"


def test_text_truncation():
    """텍스트 자르기 테스트"""
    generator = ReportGenerator()
    
    # 짧은 텍스트
    assert generator._truncate("Short", 10) == "Short"
    
    # 긴 텍스트
    long_text = "This is a very long text that should be truncated"
    truncated = generator._truncate(long_text, 20)
    assert len(truncated) == 20
    assert truncated.endswith("...")
