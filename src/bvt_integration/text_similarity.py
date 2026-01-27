"""
텍스트 유사도 계산기

두 텍스트 간의 유사도를 계산하는 컴포넌트.
Jaccard 유사도와 부분 문자열 매칭을 조합하여 사용한다.

Requirements: 3.2, 3.3
"""

import re
from typing import List, Set


class TextSimilarityCalculator:
    """텍스트 유사도 계산기
    
    BVT Check 설명과 테스트 케이스의 의미론적 정보 간
    유사도를 계산한다.
    
    Requirements: 3.2, 3.3
    """
    
    def __init__(self, jaccard_weight: float = 0.6, substring_weight: float = 0.4):
        """초기화
        
        Args:
            jaccard_weight: Jaccard 유사도 가중치 (기본값 0.6)
            substring_weight: 부분 문자열 매칭 가중치 (기본값 0.4)
        """
        self._jaccard_weight = jaccard_weight
        self._substring_weight = substring_weight
    
    def calculate(self, text1: str, text2: str) -> float:
        """두 텍스트 간 유사도 계산
        
        Jaccard 유사도와 부분 문자열 매칭을 조합하여 계산한다.
        
        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            
        Returns:
            유사도 점수 (0.0 ~ 1.0)
        """
        # None 또는 빈 문자열 처리
        if not text1 or not text2:
            return 0.0
        
        # 동일한 문자열인 경우
        if text1 == text2:
            return 1.0
        
        # 정규화
        norm_text1 = self._normalize(text1)
        norm_text2 = self._normalize(text2)
        
        # 정규화 후 동일한 경우
        if norm_text1 == norm_text2:
            return 1.0
        
        # 정규화 후 빈 문자열인 경우
        if not norm_text1 or not norm_text2:
            return 0.0
        
        # Jaccard 유사도 계산
        jaccard_score = self._calculate_jaccard(norm_text1, norm_text2)
        
        # 부분 문자열 매칭 점수 계산
        substring_score = self._calculate_substring_match(norm_text1, norm_text2)
        
        # 가중 평균
        combined_score = (
            self._jaccard_weight * jaccard_score + 
            self._substring_weight * substring_score
        )
        
        # 0.0 ~ 1.0 범위로 클램핑
        return max(0.0, min(1.0, combined_score))
    
    def calculate_with_context(
        self, 
        bvt_check: str, 
        categories: List[str],
        action_descriptions: List[str]
    ) -> float:
        """컨텍스트를 고려한 유사도 계산
        
        Category 계층 구조를 고려하여 유사도를 계산한다.
        
        Args:
            bvt_check: BVT Check 설명
            categories: BVT Category 리스트 [Category1, Category2, Category3]
            action_descriptions: 액션 설명 리스트
            
        Returns:
            유사도 점수 (0.0 ~ 1.0)
        """
        if not bvt_check or not action_descriptions:
            return 0.0
        
        # 카테고리 컨텍스트 문자열 생성
        category_context = " ".join(cat for cat in categories if cat)
        
        # BVT 전체 컨텍스트 (카테고리 + 체크 설명)
        bvt_full_context = f"{category_context} {bvt_check}".strip()
        
        # 각 액션 설명과의 유사도 계산
        max_score = 0.0
        total_score = 0.0
        
        for description in action_descriptions:
            if not description:
                continue
            
            # 기본 유사도
            base_score = self.calculate(bvt_check, description)
            
            # 컨텍스트 포함 유사도
            context_score = self.calculate(bvt_full_context, description)
            
            # 카테고리 매칭 보너스
            category_bonus = self._calculate_category_bonus(categories, description)
            
            # 최종 점수 (컨텍스트 점수에 카테고리 보너스 추가)
            final_score = context_score + category_bonus * 0.2
            final_score = max(0.0, min(1.0, final_score))
            
            max_score = max(max_score, final_score)
            total_score += final_score
        
        # 최대 점수와 평균 점수의 가중 평균
        if len(action_descriptions) > 0:
            avg_score = total_score / len(action_descriptions)
            return max_score * 0.7 + avg_score * 0.3
        
        return 0.0
    
    def _normalize(self, text: str) -> str:
        """텍스트 정규화
        
        소문자 변환, 특수문자 제거, 공백 정규화를 수행한다.
        
        Args:
            text: 원본 텍스트
            
        Returns:
            정규화된 텍스트
        """
        if not text:
            return ""
        
        # 소문자 변환
        normalized = text.lower()
        
        # 특수문자를 공백으로 대체 (한글, 영문, 숫자 제외)
        normalized = re.sub(r'[^\w\s가-힣]', ' ', normalized)
        
        # 연속 공백을 단일 공백으로
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # 앞뒤 공백 제거
        return normalized.strip()
    
    def _tokenize(self, text: str) -> Set[str]:
        """텍스트를 토큰 집합으로 변환
        
        Args:
            text: 정규화된 텍스트
            
        Returns:
            토큰 집합
        """
        if not text:
            return set()
        
        # 공백으로 분리
        tokens = text.split()
        
        # 빈 토큰 제거
        return {token for token in tokens if token}
    
    def _calculate_jaccard(self, text1: str, text2: str) -> float:
        """Jaccard 유사도 계산
        
        Args:
            text1: 첫 번째 정규화된 텍스트
            text2: 두 번째 정규화된 텍스트
            
        Returns:
            Jaccard 유사도 (0.0 ~ 1.0)
        """
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _calculate_substring_match(self, text1: str, text2: str) -> float:
        """부분 문자열 매칭 점수 계산
        
        한 텍스트가 다른 텍스트에 포함되는 정도를 계산한다.
        
        Args:
            text1: 첫 번째 정규화된 텍스트
            text2: 두 번째 정규화된 텍스트
            
        Returns:
            부분 문자열 매칭 점수 (0.0 ~ 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # 짧은 텍스트가 긴 텍스트에 포함되는지 확인
        shorter = text1 if len(text1) <= len(text2) else text2
        longer = text2 if len(text1) <= len(text2) else text1
        
        # 완전 포함
        if shorter in longer:
            return len(shorter) / len(longer)
        
        # 토큰 단위 포함 확인
        shorter_tokens = self._tokenize(shorter)
        longer_tokens = self._tokenize(longer)
        
        if not shorter_tokens or not longer_tokens:
            return 0.0
        
        # 짧은 텍스트의 토큰 중 긴 텍스트에 포함된 비율
        matched_tokens = shorter_tokens & longer_tokens
        return len(matched_tokens) / len(shorter_tokens)
    
    def _calculate_category_bonus(
        self, 
        categories: List[str], 
        description: str
    ) -> float:
        """카테고리 매칭 보너스 계산
        
        액션 설명에 카테고리 키워드가 포함된 정도를 계산한다.
        
        Args:
            categories: BVT Category 리스트
            description: 액션 설명
            
        Returns:
            카테고리 보너스 점수 (0.0 ~ 1.0)
        """
        if not categories or not description:
            return 0.0
        
        norm_description = self._normalize(description)
        description_tokens = self._tokenize(norm_description)
        
        if not description_tokens:
            return 0.0
        
        matched_count = 0
        total_categories = 0
        
        for category in categories:
            if not category:
                continue
            
            total_categories += 1
            norm_category = self._normalize(category)
            category_tokens = self._tokenize(norm_category)
            
            # 카테고리 토큰 중 하나라도 설명에 포함되면 매칭
            if category_tokens & description_tokens:
                matched_count += 1
        
        if total_categories == 0:
            return 0.0
        
        return matched_count / total_categories
