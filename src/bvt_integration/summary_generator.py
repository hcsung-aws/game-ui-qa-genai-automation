"""
의미론적 요약 문서 생성기

테스트 케이스들의 의미론적 정보를 종합한 요약 문서를 생성한다.

Requirements: 2.4, 2.5, 2.6
"""

from datetime import datetime
from typing import List

from .models import (
    SemanticTestCase,
    SemanticSummary,
    ActionSummary,
    SemanticAction
)


class SemanticSummaryGenerator:
    """의미론적 요약 문서 생성기
    
    테스트 케이스들로부터 매칭 분석에 활용할 수 있는 
    구조화된 요약 문서를 생성한다.
    
    Requirements: 2.4, 2.5, 2.6
    """
    
    def generate(self, test_cases: List[SemanticTestCase]) -> SemanticSummary:
        """테스트 케이스들로부터 요약 문서 생성
        
        Args:
            test_cases: 테스트 케이스 리스트
            
        Returns:
            SemanticSummary 객체
        """
        summaries: List[ActionSummary] = []
        total_actions = 0
        
        for test_case in test_cases:
            summary = self.extract_action_summary(test_case)
            summaries.append(summary)
            total_actions += summary.action_count
        
        return SemanticSummary(
            generated_at=datetime.now().isoformat(),
            test_case_summaries=summaries,
            total_test_cases=len(test_cases),
            total_actions=total_actions
        )
    
    def extract_action_summary(self, test_case: SemanticTestCase) -> ActionSummary:
        """단일 테스트 케이스의 액션 요약 추출
        
        Args:
            test_case: 테스트 케이스
            
        Returns:
            ActionSummary 객체
        """
        intents: List[str] = []
        target_elements: List[str] = []
        screen_states: List[str] = []
        action_descriptions: List[str] = []
        
        for action in test_case.actions:
            # 액션 설명 추출
            if action.description:
                action_descriptions.append(action.description)
            
            # semantic_info에서 정보 추출
            semantic_info = action.semantic_info
            if semantic_info:
                # intent 추출
                intent = semantic_info.get("intent", "")
                if intent and intent not in intents:
                    intents.append(intent)
                
                # target_element 추출
                target = semantic_info.get("target_element", "")
                if target and target not in target_elements:
                    target_elements.append(target)
                
                # context (screen_state) 추출
                context = semantic_info.get("context", "")
                if context and context not in screen_states:
                    screen_states.append(context)
            
            # screen_transition에서 추가 정보 추출
            screen_transition = action.screen_transition
            if screen_transition:
                before_state = screen_transition.get("before_state", "")
                after_state = screen_transition.get("after_state", "")
                
                if before_state and before_state not in screen_states:
                    screen_states.append(before_state)
                if after_state and after_state not in screen_states:
                    screen_states.append(after_state)
        
        return ActionSummary(
            test_case_name=test_case.name,
            intents=intents,
            target_elements=target_elements,
            screen_states=screen_states,
            action_descriptions=action_descriptions,
            action_count=len(test_case.actions)
        )
