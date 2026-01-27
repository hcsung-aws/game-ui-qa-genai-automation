"""
Property-based tests for MatchingAnalyzer

**Feature: bvt-semantic-integration**
- Property 5: Match_Result 구조 정확성
- Property 7: 고신뢰도 임계값 일관성
- Property 8: 매칭 결과 정렬
- Property 9: 매칭 분석 결정론성

Validates: Requirements 3.1, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9
"""

import os
import sys
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.bvt_integration.models import (
    BVTTestCase,
    SemanticSummary,
    ActionSummary,
    MatchResult,
    ActionRange
)
from src.bvt_integration.matching_analyzer import MatchingAnalyzer, HIGH_CONFIDENCE_THRESHOLD
from src.bvt_integration.text_similarity import TextSimilarityCalculator


# ============================================================================
# Strategies (전략 정의)
# ============================================================================

# 안전한 텍스트 전략
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
        whitelist_categories=('L', 'N'),
        blacklist_characters='\x00'
    ),
    min_size=1,
    max_size=30
).filter(lambda x: x.strip() != '')

# BVTTestCase 전략
bvt_test_case_strategy = st.builds(
    BVTTestCase,
    no=st.integers(min_value=1, max_value=1000),
    category1=non_empty_text_strategy,
    category2=safe_text_strategy,
    category3=safe_text_strategy,
    check=non_empty_text_strategy,
    test_result=st.sampled_from(["Not Tested", "PASS", "Fail", "N/A", "Block"]),
    bts_id=safe_text_strategy,
    comment=safe_text_strategy
)

# ActionSummary 전략
action_summary_strategy = st.builds(
    ActionSummary,
    test_case_name=non_empty_text_strategy,
    intents=st.lists(non_empty_text_strategy, min_size=0, max_size=5),
    target_elements=st.lists(non_empty_text_strategy, min_size=0, max_size=5),
    screen_states=st.lists(safe_text_strategy, min_size=0, max_size=5),
    action_descriptions=st.lists(non_empty_text_strategy, min_size=1, max_size=10),
    action_count=st.integers(min_value=1, max_value=20)
)

# SemanticSummary 전략
semantic_summary_strategy = st.builds(
    SemanticSummary,
    generated_at=st.datetimes().map(lambda dt: dt.isoformat()),
    test_case_summaries=st.lists(action_summary_strategy, min_size=0, max_size=5),
    total_test_cases=st.integers(min_value=0, max_value=10),
    total_actions=st.integers(min_value=0, max_value=100)
)

# 비어있지 않은 SemanticSummary 전략
non_empty_semantic_summary_strategy = st.builds(
    SemanticSummary,
    generated_at=st.datetimes().map(lambda dt: dt.isoformat()),
    test_case_summaries=st.lists(action_summary_strategy, min_size=1, max_size=5),
    total_test_cases=st.integers(min_value=1, max_value=10),
    total_actions=st.integers(min_value=1, max_value=100)
)


# ============================================================================
# Property 5: Match_Result 구조 정확성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    bvt_cases=st.lists(bvt_test_case_strategy, min_size=1, max_size=5),
    summary=semantic_summary_strategy
)
def test_match_result_structure_accuracy(bvt_cases, summary):
    """
    **Feature: bvt-semantic-integration, Property 5: Match_Result 구조 정확성**
    
    *For any* BVT_Test_Case와 Semantic_Summary 쌍, MatchingAnalyzer.analyze()의 
    결과인 Match_Result는 confidence_score(0.0~1.0), bvt_case 참조, 그리고 
    매칭된 경우 matched_test_case와 action_range를 포함해야 한다.
    
    **Validates: Requirements 3.1, 3.6, 3.7, 3.8**
    """
    analyzer = MatchingAnalyzer()
    results = analyzer.analyze(bvt_cases, summary)
    
    # 결과 개수는 입력 BVT 케이스 개수와 같아야 함
    assert len(results) == len(bvt_cases), \
        f"결과 개수 불일치: {len(results)} != {len(bvt_cases)}"
    
    for result in results:
        # confidence_score는 0.0 ~ 1.0 범위
        assert 0.0 <= result.confidence_score <= 1.0, \
            f"confidence_score 범위 오류: {result.confidence_score}"
        
        # bvt_case 참조 존재
        assert result.bvt_case is not None, "bvt_case가 None"
        assert isinstance(result.bvt_case, BVTTestCase), "bvt_case 타입 오류"
        
        # 매칭된 경우 검증
        if result.is_matched:
            assert result.matched_test_case is not None, \
                "매칭되었으나 matched_test_case가 None"
            assert isinstance(result.matched_test_case, str), \
                "matched_test_case 타입 오류"


@settings(max_examples=100, deadline=None)
@given(
    bvt_case=bvt_test_case_strategy,
    summary=non_empty_semantic_summary_strategy
)
def test_match_result_contains_bvt_reference(bvt_case, summary):
    """
    **Feature: bvt-semantic-integration, Property 5 확장: BVT 참조 포함**
    
    *For any* 매칭 결과, bvt_case 필드는 원본 BVT 케이스와 동일해야 한다.
    
    **Validates: Requirements 3.8**
    """
    analyzer = MatchingAnalyzer()
    results = analyzer.analyze([bvt_case], summary)
    
    assert len(results) == 1
    result = results[0]
    
    # bvt_case가 원본과 동일
    assert result.bvt_case.no == bvt_case.no
    assert result.bvt_case.check == bvt_case.check
    assert result.bvt_case.category1 == bvt_case.category1


# ============================================================================
# Property 7: 고신뢰도 임계값 일관성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    bvt_cases=st.lists(bvt_test_case_strategy, min_size=1, max_size=5),
    summary=semantic_summary_strategy
)
def test_high_confidence_threshold_consistency(bvt_cases, summary):
    """
    **Feature: bvt-semantic-integration, Property 7: 고신뢰도 임계값 일관성**
    
    *For any* Match_Result, confidence_score가 0.7 이상이면 is_high_confidence가 True이고,
    0.7 미만이면 is_high_confidence가 False여야 한다.
    
    **Validates: Requirements 3.4**
    """
    analyzer = MatchingAnalyzer()
    results = analyzer.analyze(bvt_cases, summary)
    
    for result in results:
        if result.confidence_score >= HIGH_CONFIDENCE_THRESHOLD:
            assert result.is_high_confidence is True, \
                f"confidence_score {result.confidence_score} >= {HIGH_CONFIDENCE_THRESHOLD}이나 is_high_confidence가 False"
        else:
            assert result.is_high_confidence is False, \
                f"confidence_score {result.confidence_score} < {HIGH_CONFIDENCE_THRESHOLD}이나 is_high_confidence가 True"


# ============================================================================
# Property 8: 매칭 결과 정렬
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    bvt_cases=st.lists(bvt_test_case_strategy, min_size=2, max_size=10),
    summary=non_empty_semantic_summary_strategy
)
def test_matching_results_sorted_by_confidence(bvt_cases, summary):
    """
    **Feature: bvt-semantic-integration, Property 8: 매칭 결과 정렬**
    
    *For any* BVT_Test_Case에 대한 여러 매칭 결과, 반환된 리스트는 
    confidence_score 내림차순으로 정렬되어 있어야 한다.
    
    **Validates: Requirements 3.5**
    """
    analyzer = MatchingAnalyzer()
    results = analyzer.analyze(bvt_cases, summary)
    
    # 결과가 2개 이상인 경우 정렬 확인
    if len(results) >= 2:
        for i in range(len(results) - 1):
            assert results[i].confidence_score >= results[i + 1].confidence_score, \
                f"정렬 오류: {results[i].confidence_score} < {results[i + 1].confidence_score}"


# ============================================================================
# Property 9: 매칭 분석 결정론성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    bvt_cases=st.lists(bvt_test_case_strategy, min_size=1, max_size=5),
    summary=semantic_summary_strategy
)
def test_matching_analysis_determinism(bvt_cases, summary):
    """
    **Feature: bvt-semantic-integration, Property 9: 매칭 분석 결정론성**
    
    *For any* 동일한 BVT_Test_Case 리스트와 Semantic_Summary, 
    MatchingAnalyzer.analyze()를 여러 번 호출해도 항상 동일한 Match_Result 리스트를 반환해야 한다.
    
    **Validates: Requirements 3.9**
    """
    analyzer = MatchingAnalyzer()
    
    # 동일한 입력으로 3번 호출
    results1 = analyzer.analyze(bvt_cases, summary)
    results2 = analyzer.analyze(bvt_cases, summary)
    results3 = analyzer.analyze(bvt_cases, summary)
    
    # 결과 개수 동일
    assert len(results1) == len(results2) == len(results3)
    
    # 각 결과 비교
    for r1, r2, r3 in zip(results1, results2, results3):
        assert r1.confidence_score == r2.confidence_score == r3.confidence_score, \
            "confidence_score가 일관되지 않음"
        assert r1.matched_test_case == r2.matched_test_case == r3.matched_test_case, \
            "matched_test_case가 일관되지 않음"
        assert r1.is_high_confidence == r2.is_high_confidence == r3.is_high_confidence, \
            "is_high_confidence가 일관되지 않음"


# ============================================================================
# 단위 테스트
# ============================================================================

def test_empty_bvt_cases():
    """빈 BVT 케이스 리스트 처리 테스트"""
    analyzer = MatchingAnalyzer()
    summary = SemanticSummary(
        generated_at="2026-01-24T00:00:00",
        test_case_summaries=[],
        total_test_cases=0,
        total_actions=0
    )
    
    results = analyzer.analyze([], summary)
    assert results == []


def test_empty_summary():
    """빈 요약 문서 처리 테스트"""
    analyzer = MatchingAnalyzer()
    bvt_case = BVTTestCase(
        no=1,
        category1="메인화면",
        category2="UI",
        category3="",
        check="버튼 클릭 테스트",
        test_result="Not Tested",
        bts_id="",
        comment=""
    )
    summary = SemanticSummary(
        generated_at="2026-01-24T00:00:00",
        test_case_summaries=[],
        total_test_cases=0,
        total_actions=0
    )
    
    results = analyzer.analyze([bvt_case], summary)
    
    assert len(results) == 1
    assert results[0].confidence_score == 0.0
    assert results[0].is_matched is False


def test_exact_match():
    """정확한 매칭 테스트"""
    analyzer = MatchingAnalyzer()
    
    bvt_case = BVTTestCase(
        no=1,
        category1="메인화면",
        category2="버튼",
        category3="",
        check="시작 버튼 클릭",
        test_result="Not Tested",
        bts_id="",
        comment=""
    )
    
    action_summary = ActionSummary(
        test_case_name="start_button_test",
        intents=["시작 버튼 클릭"],
        target_elements=["시작 버튼"],
        screen_states=["메인화면"],
        action_descriptions=["메인화면에서 시작 버튼 클릭"],
        action_count=1
    )
    
    summary = SemanticSummary(
        generated_at="2026-01-24T00:00:00",
        test_case_summaries=[action_summary],
        total_test_cases=1,
        total_actions=1
    )
    
    results = analyzer.analyze([bvt_case], summary)
    
    assert len(results) == 1
    assert results[0].is_matched is True
    assert results[0].matched_test_case == "start_button_test"
    # 정확한 매칭이므로 높은 점수
    assert results[0].confidence_score > 0.5


def test_no_match():
    """매칭 없음 테스트"""
    analyzer = MatchingAnalyzer()
    
    bvt_case = BVTTestCase(
        no=1,
        category1="설정",
        category2="옵션",
        category3="",
        check="볼륨 조절",
        test_result="Not Tested",
        bts_id="",
        comment=""
    )
    
    action_summary = ActionSummary(
        test_case_name="login_test",
        intents=["로그인"],
        target_elements=["로그인 버튼"],
        screen_states=["로그인 화면"],
        action_descriptions=["로그인 화면에서 로그인 버튼 클릭"],
        action_count=1
    )
    
    summary = SemanticSummary(
        generated_at="2026-01-24T00:00:00",
        test_case_summaries=[action_summary],
        total_test_cases=1,
        total_actions=1
    )
    
    results = analyzer.analyze([bvt_case], summary)
    
    assert len(results) == 1
    # 완전히 다른 내용이므로 낮은 점수
    assert results[0].confidence_score < HIGH_CONFIDENCE_THRESHOLD


def test_find_matching_actions():
    """액션 범위 찾기 테스트"""
    analyzer = MatchingAnalyzer()
    
    bvt_case = BVTTestCase(
        no=1,
        category1="메인화면",
        category2="",
        category3="",
        check="버튼 클릭",
        test_result="Not Tested",
        bts_id="",
        comment=""
    )
    
    action_summary = ActionSummary(
        test_case_name="test",
        intents=[],
        target_elements=[],
        screen_states=[],
        action_descriptions=[
            "화면 로딩",
            "메인화면 버튼 클릭",
            "결과 확인"
        ],
        action_count=3
    )
    
    action_range = analyzer.find_matching_actions(bvt_case, action_summary)
    
    # 액션 범위가 반환되어야 함
    assert action_range is not None
    assert isinstance(action_range, ActionRange)
    assert action_range.start_index >= 0
    assert action_range.end_index >= action_range.start_index


def test_find_matching_actions_empty():
    """빈 액션 리스트에서 범위 찾기 테스트"""
    analyzer = MatchingAnalyzer()
    
    bvt_case = BVTTestCase(
        no=1,
        category1="",
        category2="",
        category3="",
        check="테스트",
        test_result="Not Tested",
        bts_id="",
        comment=""
    )
    
    action_summary = ActionSummary(
        test_case_name="test",
        intents=[],
        target_elements=[],
        screen_states=[],
        action_descriptions=[],
        action_count=0
    )
    
    action_range = analyzer.find_matching_actions(bvt_case, action_summary)
    
    assert action_range is None


def test_multiple_bvt_cases_sorted():
    """여러 BVT 케이스 정렬 테스트"""
    analyzer = MatchingAnalyzer()
    
    # 서로 다른 매칭 점수를 가질 BVT 케이스들
    bvt_cases = [
        BVTTestCase(no=1, category1="A", category2="", category3="", 
                   check="완전히 다른 내용", test_result="Not Tested", bts_id="", comment=""),
        BVTTestCase(no=2, category1="메인", category2="", category3="", 
                   check="메인 화면 버튼", test_result="Not Tested", bts_id="", comment=""),
        BVTTestCase(no=3, category1="X", category2="", category3="", 
                   check="xyz", test_result="Not Tested", bts_id="", comment=""),
    ]
    
    action_summary = ActionSummary(
        test_case_name="main_test",
        intents=["메인 화면 버튼 클릭"],
        target_elements=["메인 버튼"],
        screen_states=["메인 화면"],
        action_descriptions=["메인 화면에서 버튼 클릭"],
        action_count=1
    )
    
    summary = SemanticSummary(
        generated_at="2026-01-24T00:00:00",
        test_case_summaries=[action_summary],
        total_test_cases=1,
        total_actions=1
    )
    
    results = analyzer.analyze(bvt_cases, summary)
    
    # 결과가 신뢰도 내림차순으로 정렬되어야 함
    for i in range(len(results) - 1):
        assert results[i].confidence_score >= results[i + 1].confidence_score


def test_custom_similarity_calculator():
    """커스텀 유사도 계산기 사용 테스트"""
    custom_calculator = TextSimilarityCalculator(
        jaccard_weight=0.8,
        substring_weight=0.2
    )
    analyzer = MatchingAnalyzer(similarity_calculator=custom_calculator)
    
    bvt_case = BVTTestCase(
        no=1,
        category1="테스트",
        category2="",
        category3="",
        check="버튼 클릭",
        test_result="Not Tested",
        bts_id="",
        comment=""
    )
    
    summary = SemanticSummary(
        generated_at="2026-01-24T00:00:00",
        test_case_summaries=[],
        total_test_cases=0,
        total_actions=0
    )
    
    # 오류 없이 실행되어야 함
    results = analyzer.analyze([bvt_case], summary)
    assert len(results) == 1
