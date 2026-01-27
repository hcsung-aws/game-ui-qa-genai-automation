"""
BVT-테스트케이스 매칭 분석기

BVT 항목과 Semantic_Summary를 비교하여 매칭 결과를 생성한다.

Requirements: 3.1, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9
"""

from typing import List, Optional, Dict, Any

from .models import (
    BVTTestCase,
    SemanticSummary,
    ActionSummary,
    MatchResult,
    ActionRange
)
from .text_similarity import TextSimilarityCalculator


# 고신뢰도 임계값
HIGH_CONFIDENCE_THRESHOLD = 0.7


class MatchingAnalyzer:
    """BVT-테스트케이스 매칭 분석기
    
    BVT 테스트 케이스와 의미론적 요약 문서를 비교하여
    매칭 결과를 생성한다.
    
    Requirements: 3.1, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9
    """
    
    def __init__(
        self, 
        similarity_calculator: Optional[TextSimilarityCalculator] = None
    ):
        """초기화
        
        Args:
            similarity_calculator: 텍스트 유사도 계산기 (기본값: 새 인스턴스 생성)
        """
        self._similarity_calculator = similarity_calculator or TextSimilarityCalculator()
    
    def analyze(
        self, 
        bvt_cases: List[BVTTestCase], 
        summary: SemanticSummary
    ) -> List[MatchResult]:
        """BVT 항목들과 요약 문서를 비교 분석
        
        Args:
            bvt_cases: BVT 테스트 케이스 리스트
            summary: 의미론적 요약 문서
            
        Returns:
            MatchResult 리스트 (신뢰도 내림차순 정렬)
        """
        results: List[MatchResult] = []
        
        for bvt_case in bvt_cases:
            match_result = self._analyze_single_bvt(bvt_case, summary)
            results.append(match_result)
        
        # 신뢰도 내림차순 정렬
        results.sort(key=lambda r: r.confidence_score, reverse=True)
        
        return results
    
    def find_matching_actions(
        self, 
        bvt_case: BVTTestCase, 
        test_case_summary: ActionSummary
    ) -> Optional[ActionRange]:
        """BVT 항목에 해당하는 액션 범위 찾기
        
        Args:
            bvt_case: BVT 테스트 케이스
            test_case_summary: 테스트 케이스 요약
            
        Returns:
            ActionRange 또는 None
        """
        if test_case_summary.action_count == 0:
            return None
        
        # BVT Check와 카테고리 정보
        bvt_check = bvt_case.check
        categories = [
            bvt_case.category1,
            bvt_case.category2,
            bvt_case.category3
        ]
        
        # 각 액션 설명과의 유사도 계산
        action_scores: List[float] = []
        for description in test_case_summary.action_descriptions:
            score = self._similarity_calculator.calculate_with_context(
                bvt_check,
                categories,
                [description]
            )
            action_scores.append(score)
        
        if not action_scores:
            return None
        
        # 가장 높은 유사도를 가진 액션 범위 찾기
        best_range = self._find_best_action_range(action_scores)
        
        return best_range
    
    def _analyze_single_bvt(
        self, 
        bvt_case: BVTTestCase, 
        summary: SemanticSummary
    ) -> MatchResult:
        """단일 BVT 케이스 분석
        
        Args:
            bvt_case: BVT 테스트 케이스
            summary: 의미론적 요약 문서
            
        Returns:
            MatchResult
        """
        best_match: Optional[str] = None
        best_score: float = 0.0
        best_action_range: Optional[ActionRange] = None
        best_details: Dict[str, Any] = {}
        
        # BVT 카테고리 정보
        categories = [
            bvt_case.category1,
            bvt_case.category2,
            bvt_case.category3
        ]
        
        for test_case_summary in summary.test_case_summaries:
            # 유사도 계산
            score = self._calculate_match_score(bvt_case, test_case_summary)
            
            if score > best_score:
                best_score = score
                best_match = test_case_summary.test_case_name
                best_action_range = self.find_matching_actions(bvt_case, test_case_summary)
                best_details = self._build_match_details(
                    bvt_case, 
                    test_case_summary, 
                    score
                )
        
        # 고신뢰도 판정
        is_high_confidence = best_score >= HIGH_CONFIDENCE_THRESHOLD
        
        # 매칭되지 않은 경우 처리
        if best_score == 0.0:
            best_match = None
            best_action_range = None
        
        return MatchResult(
            bvt_case=bvt_case,
            matched_test_case=best_match,
            action_range=best_action_range,
            confidence_score=best_score,
            is_high_confidence=is_high_confidence,
            match_details=best_details
        )
    
    def _calculate_match_score(
        self, 
        bvt_case: BVTTestCase, 
        test_case_summary: ActionSummary
    ) -> float:
        """매칭 점수 계산
        
        Args:
            bvt_case: BVT 테스트 케이스
            test_case_summary: 테스트 케이스 요약
            
        Returns:
            매칭 점수 (0.0 ~ 1.0)
        """
        categories = [
            bvt_case.category1,
            bvt_case.category2,
            bvt_case.category3
        ]
        
        # 1. Check 설명과 액션 설명 간 유사도
        action_score = self._similarity_calculator.calculate_with_context(
            bvt_case.check,
            categories,
            test_case_summary.action_descriptions
        )
        
        # 2. Check 설명과 intent 간 유사도
        intent_score = 0.0
        if test_case_summary.intents:
            intent_scores = [
                self._similarity_calculator.calculate(bvt_case.check, intent)
                for intent in test_case_summary.intents
            ]
            intent_score = max(intent_scores) if intent_scores else 0.0
        
        # 3. Check 설명과 target_element 간 유사도
        target_score = 0.0
        if test_case_summary.target_elements:
            target_scores = [
                self._similarity_calculator.calculate(bvt_case.check, target)
                for target in test_case_summary.target_elements
            ]
            target_score = max(target_scores) if target_scores else 0.0
        
        # 가중 평균 (액션 설명 50%, intent 30%, target 20%)
        combined_score = (
            action_score * 0.5 +
            intent_score * 0.3 +
            target_score * 0.2
        )
        
        return min(1.0, max(0.0, combined_score))
    
    def _find_best_action_range(
        self, 
        action_scores: List[float]
    ) -> Optional[ActionRange]:
        """가장 높은 유사도를 가진 액션 범위 찾기
        
        연속된 고점수 액션들을 하나의 범위로 묶는다.
        
        Args:
            action_scores: 각 액션의 유사도 점수 리스트
            
        Returns:
            ActionRange 또는 None
        """
        if not action_scores:
            return None
        
        # 최고 점수 찾기
        max_score = max(action_scores)
        if max_score == 0.0:
            return None
        
        # 임계값 (최고 점수의 50% 이상)
        threshold = max_score * 0.5
        
        # 연속된 고점수 구간 찾기
        best_start = 0
        best_end = 0
        best_sum = 0.0
        
        current_start = -1
        current_sum = 0.0
        
        for i, score in enumerate(action_scores):
            if score >= threshold:
                if current_start == -1:
                    current_start = i
                    current_sum = score
                else:
                    current_sum += score
                
                # 현재 구간이 더 좋은지 확인
                if current_sum > best_sum:
                    best_start = current_start
                    best_end = i
                    best_sum = current_sum
            else:
                current_start = -1
                current_sum = 0.0
        
        return ActionRange(start_index=best_start, end_index=best_end)
    
    def _build_match_details(
        self, 
        bvt_case: BVTTestCase, 
        test_case_summary: ActionSummary,
        score: float
    ) -> Dict[str, Any]:
        """매칭 세부 정보 생성
        
        Args:
            bvt_case: BVT 테스트 케이스
            test_case_summary: 테스트 케이스 요약
            score: 매칭 점수
            
        Returns:
            매칭 세부 정보 딕셔너리
        """
        return {
            "bvt_no": bvt_case.no,
            "bvt_check": bvt_case.check,
            "bvt_categories": [
                bvt_case.category1,
                bvt_case.category2,
                bvt_case.category3
            ],
            "matched_test_case": test_case_summary.test_case_name,
            "matched_intents": test_case_summary.intents,
            "matched_targets": test_case_summary.target_elements,
            "action_count": test_case_summary.action_count,
            "score": score
        }
