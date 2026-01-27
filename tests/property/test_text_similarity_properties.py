"""
Property-based tests for TextSimilarityCalculator

**Feature: bvt-semantic-integration, Property 6: 텍스트 유사도 계산 정확성**

Validates: Requirements 3.2, 3.3
"""

import os
import sys
from hypothesis import given, settings, strategies as st, assume

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.bvt_integration.text_similarity import TextSimilarityCalculator


# ============================================================================
# Strategies (전략 정의)
# ============================================================================

# 안전한 텍스트 전략 (유효한 문자열만)
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
        whitelist_categories=('L', 'N'),
        blacklist_characters='\x00'
    ),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != '')

# 단어 전략 (공백 없는 문자열)
word_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N'),
        blacklist_characters='\x00 '
    ),
    min_size=1,
    max_size=20
).filter(lambda x: x.strip() != '')

# 문장 전략 (여러 단어로 구성)
sentence_strategy = st.lists(
    word_strategy,
    min_size=1,
    max_size=10
).map(lambda words: ' '.join(words))

# 카테고리 전략
category_strategy = st.one_of(
    st.just(""),
    non_empty_text_strategy
)

# 카테고리 리스트 전략
categories_strategy = st.lists(
    category_strategy,
    min_size=0,
    max_size=3
)

# 액션 설명 리스트 전략
action_descriptions_strategy = st.lists(
    non_empty_text_strategy,
    min_size=0,
    max_size=10
)


# ============================================================================
# Property 6: 텍스트 유사도 계산 정확성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(text1=safe_text_strategy, text2=safe_text_strategy)
def test_similarity_score_range(text1, text2):
    """
    **Feature: bvt-semantic-integration, Property 6: 텍스트 유사도 계산 정확성**
    
    *For any* 두 텍스트 문자열, TextSimilarityCalculator.calculate()의 결과는 
    0.0에서 1.0 사이여야 한다.
    
    **Validates: Requirements 3.2, 3.3**
    """
    calculator = TextSimilarityCalculator()
    score = calculator.calculate(text1, text2)
    
    assert 0.0 <= score <= 1.0, \
        f"유사도 점수가 범위를 벗어남: {score}"


@settings(max_examples=100, deadline=None)
@given(text=non_empty_text_strategy)
def test_identical_strings_return_one(text):
    """
    **Feature: bvt-semantic-integration, Property 6: 동일 문자열 유사도**
    
    *For any* 동일한 문자열에 대해서는 1.0을 반환해야 한다.
    
    **Validates: Requirements 3.2**
    """
    calculator = TextSimilarityCalculator()
    score = calculator.calculate(text, text)
    
    assert score == 1.0, \
        f"동일 문자열의 유사도가 1.0이 아님: {score}"


@settings(max_examples=100, deadline=None)
@given(text1=sentence_strategy, text2=sentence_strategy)
def test_completely_different_strings_low_score(text1, text2):
    """
    **Feature: bvt-semantic-integration, Property 6: 완전히 다른 문자열 유사도**
    
    *For any* 완전히 다른 문자열에 대해서는 낮은 유사도를 반환해야 한다.
    (공통 토큰이 없는 경우)
    
    **Validates: Requirements 3.2**
    """
    calculator = TextSimilarityCalculator()
    
    # 두 문자열의 토큰이 완전히 다른 경우만 테스트
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    
    # 공통 토큰이 없는 경우에만 테스트
    assume(len(tokens1 & tokens2) == 0)
    assume(len(tokens1) > 0 and len(tokens2) > 0)
    
    score = calculator.calculate(text1, text2)
    
    # 완전히 다른 문자열은 낮은 점수를 가져야 함 (0.5 미만)
    assert score < 0.5, \
        f"완전히 다른 문자열의 유사도가 너무 높음: {score}"


@settings(max_examples=100, deadline=None)
@given(text1=safe_text_strategy, text2=safe_text_strategy)
def test_similarity_symmetry(text1, text2):
    """
    **Feature: bvt-semantic-integration, Property 6: 유사도 대칭성**
    
    *For any* 두 텍스트, calculate(text1, text2) == calculate(text2, text1)이어야 한다.
    
    **Validates: Requirements 3.2**
    """
    calculator = TextSimilarityCalculator()
    
    score1 = calculator.calculate(text1, text2)
    score2 = calculator.calculate(text2, text1)
    
    assert abs(score1 - score2) < 0.001, \
        f"유사도가 대칭적이지 않음: {score1} != {score2}"


@settings(max_examples=100, deadline=None)
@given(
    bvt_check=non_empty_text_strategy,
    categories=categories_strategy,
    action_descriptions=action_descriptions_strategy
)
def test_context_similarity_score_range(bvt_check, categories, action_descriptions):
    """
    **Feature: bvt-semantic-integration, Property 6: 컨텍스트 유사도 범위**
    
    *For any* BVT Check와 카테고리, 액션 설명 리스트에 대해 
    calculate_with_context()의 결과는 0.0에서 1.0 사이여야 한다.
    
    **Validates: Requirements 3.3**
    """
    calculator = TextSimilarityCalculator()
    score = calculator.calculate_with_context(bvt_check, categories, action_descriptions)
    
    assert 0.0 <= score <= 1.0, \
        f"컨텍스트 유사도 점수가 범위를 벗어남: {score}"


# ============================================================================
# 단위 테스트
# ============================================================================

def test_empty_string_returns_zero():
    """빈 문자열 처리 테스트"""
    calculator = TextSimilarityCalculator()
    
    assert calculator.calculate("", "test") == 0.0
    assert calculator.calculate("test", "") == 0.0
    assert calculator.calculate("", "") == 0.0


def test_none_handling():
    """None 입력 처리 테스트"""
    calculator = TextSimilarityCalculator()
    
    assert calculator.calculate(None, "test") == 0.0
    assert calculator.calculate("test", None) == 0.0
    assert calculator.calculate(None, None) == 0.0


def test_whitespace_only_returns_zero():
    """공백만 있는 문자열 처리 테스트"""
    calculator = TextSimilarityCalculator()
    
    assert calculator.calculate("   ", "test") == 0.0
    assert calculator.calculate("test", "   ") == 0.0


def test_partial_match():
    """부분 매칭 테스트"""
    calculator = TextSimilarityCalculator()
    
    # 일부 단어가 공통인 경우
    score = calculator.calculate("hello world", "hello there")
    
    # 부분 매칭이므로 0보다 크고 1보다 작아야 함
    assert 0.0 < score < 1.0


def test_case_insensitivity():
    """대소문자 무시 테스트"""
    calculator = TextSimilarityCalculator()
    
    score1 = calculator.calculate("Hello World", "hello world")
    score2 = calculator.calculate("HELLO WORLD", "hello world")
    
    # 대소문자만 다른 경우 동일한 점수
    assert score1 == 1.0
    assert score2 == 1.0


def test_special_characters_handling():
    """특수문자 처리 테스트"""
    calculator = TextSimilarityCalculator()
    
    # 특수문자가 포함된 경우에도 정상 동작
    score = calculator.calculate("hello, world!", "hello world")
    
    # 특수문자 제거 후 동일하므로 높은 점수
    assert score == 1.0


def test_korean_text():
    """한글 텍스트 처리 테스트"""
    calculator = TextSimilarityCalculator()
    
    # 동일한 한글 텍스트
    score = calculator.calculate("안녕하세요", "안녕하세요")
    assert score == 1.0
    
    # 부분 매칭 한글 텍스트
    score = calculator.calculate("메인 화면 버튼", "메인 화면 아이콘")
    assert 0.0 < score < 1.0


def test_context_with_empty_descriptions():
    """빈 액션 설명 리스트 처리 테스트"""
    calculator = TextSimilarityCalculator()
    
    score = calculator.calculate_with_context("test check", ["cat1", "cat2"], [])
    assert score == 0.0


def test_context_with_empty_check():
    """빈 BVT Check 처리 테스트"""
    calculator = TextSimilarityCalculator()
    
    score = calculator.calculate_with_context("", ["cat1"], ["description"])
    assert score == 0.0


def test_context_category_bonus():
    """카테고리 보너스 테스트"""
    calculator = TextSimilarityCalculator()
    
    # 카테고리와 매칭되는 설명
    score_with_match = calculator.calculate_with_context(
        "버튼 클릭",
        ["메인화면", "UI"],
        ["메인화면에서 버튼 클릭"]
    )
    
    # 카테고리와 매칭되지 않는 설명
    score_without_match = calculator.calculate_with_context(
        "버튼 클릭",
        ["설정", "옵션"],
        ["메인화면에서 버튼 클릭"]
    )
    
    # 카테고리 매칭이 있는 경우 더 높은 점수
    assert score_with_match >= score_without_match


def test_jaccard_weight_customization():
    """가중치 커스터마이징 테스트"""
    calc_default = TextSimilarityCalculator()
    calc_jaccard_heavy = TextSimilarityCalculator(jaccard_weight=0.9, substring_weight=0.1)
    calc_substring_heavy = TextSimilarityCalculator(jaccard_weight=0.1, substring_weight=0.9)
    
    text1 = "hello world test"
    text2 = "hello world"
    
    score_default = calc_default.calculate(text1, text2)
    score_jaccard = calc_jaccard_heavy.calculate(text1, text2)
    score_substring = calc_substring_heavy.calculate(text1, text2)
    
    # 모든 점수가 유효한 범위 내에 있어야 함
    assert 0.0 <= score_default <= 1.0
    assert 0.0 <= score_jaccard <= 1.0
    assert 0.0 <= score_substring <= 1.0
