"""
매칭 리포트 생성기

매칭 분석 결과를 바탕으로 리포트를 생성한다.
JSON과 Markdown 형식을 지원한다.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import json
import logging
from datetime import datetime
from typing import List

from .models import MatchResult, MatchingReport, BVTTestCase


logger = logging.getLogger(__name__)


class ReportGenerator:
    """매칭 리포트 생성기
    
    매칭 결과로부터 리포트를 생성하고 다양한 형식으로 출력한다.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    
    HIGH_CONFIDENCE_THRESHOLD = 0.7
    
    def generate(self, match_results: List[MatchResult]) -> MatchingReport:
        """매칭 결과로부터 리포트 생성
        
        Args:
            match_results: 매칭 결과 리스트
            
        Returns:
            MatchingReport 객체
            
        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        # 고신뢰도/저신뢰도/미매칭 분류
        high_confidence_matches: List[MatchResult] = []
        low_confidence_matches: List[MatchResult] = []
        unmatched_bvt_cases: List[BVTTestCase] = []
        
        for result in match_results:
            if result.is_matched:
                if result.is_high_confidence:
                    high_confidence_matches.append(result)
                else:
                    low_confidence_matches.append(result)
            else:
                unmatched_bvt_cases.append(result.bvt_case)
        
        # 통계 계산
        total_bvt_items = len(match_results)
        matched_items = len(high_confidence_matches) + len(low_confidence_matches)
        unmatched_items = len(unmatched_bvt_cases)
        
        # 커버리지 계산 (Requirements 6.4)
        if total_bvt_items > 0:
            coverage_percentage = (matched_items / total_bvt_items) * 100
        else:
            coverage_percentage = 0.0
        
        report = MatchingReport(
            generated_at=datetime.now().isoformat(),
            total_bvt_items=total_bvt_items,
            matched_items=matched_items,
            unmatched_items=unmatched_items,
            high_confidence_matches=high_confidence_matches,
            low_confidence_matches=low_confidence_matches,
            unmatched_bvt_cases=unmatched_bvt_cases,
            coverage_percentage=coverage_percentage
        )
        
        logger.info(
            f"리포트 생성 완료: 총 {total_bvt_items}개 중 "
            f"{matched_items}개 매칭 (커버리지: {coverage_percentage:.1f}%)"
        )
        
        return report
    
    def to_json(self, report: MatchingReport) -> str:
        """리포트를 JSON 문자열로 변환
        
        Args:
            report: 매칭 리포트
            
        Returns:
            JSON 문자열
            
        Requirements: 6.5
        """
        return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    
    def to_markdown(self, report: MatchingReport) -> str:
        """리포트를 Markdown 문자열로 변환
        
        Args:
            report: 매칭 리포트
            
        Returns:
            Markdown 문자열
            
        Requirements: 6.5
        """
        lines = []
        
        # 헤더
        lines.append("# BVT-Semantic 매칭 리포트")
        lines.append("")
        lines.append(f"생성 시간: {report.generated_at}")
        lines.append("")
        
        # 요약 통계
        lines.append("## 요약")
        lines.append("")
        lines.append(f"- 총 BVT 항목: {report.total_bvt_items}")
        lines.append(f"- 매칭된 항목: {report.matched_items}")
        lines.append(f"- 미매칭 항목: {report.unmatched_items}")
        lines.append(f"- 커버리지: {report.coverage_percentage:.1f}%")
        lines.append("")
        
        # 고신뢰도 매칭 (Requirements 6.2)
        lines.append("## 고신뢰도 매칭")
        lines.append("")
        if report.high_confidence_matches:
            lines.append("| BVT No. | Category | Check | 매칭 테스트 케이스 | 신뢰도 |")
            lines.append("|---------|----------|-------|-------------------|--------|")
            for match in report.high_confidence_matches:
                category = self._format_category(match.bvt_case)
                check = self._truncate(match.bvt_case.check, 50)
                tc_name = match.matched_test_case or "-"
                score = f"{match.confidence_score:.2f}"
                lines.append(f"| {match.bvt_case.no} | {category} | {check} | {tc_name} | {score} |")
        else:
            lines.append("고신뢰도 매칭이 없습니다.")
        lines.append("")
        
        # 저신뢰도 매칭
        lines.append("## 저신뢰도 매칭")
        lines.append("")
        if report.low_confidence_matches:
            lines.append("| BVT No. | Category | Check | 매칭 테스트 케이스 | 신뢰도 |")
            lines.append("|---------|----------|-------|-------------------|--------|")
            for match in report.low_confidence_matches:
                category = self._format_category(match.bvt_case)
                check = self._truncate(match.bvt_case.check, 50)
                tc_name = match.matched_test_case or "-"
                score = f"{match.confidence_score:.2f}"
                lines.append(f"| {match.bvt_case.no} | {category} | {check} | {tc_name} | {score} |")
        else:
            lines.append("저신뢰도 매칭이 없습니다.")
        lines.append("")
        
        # 미매칭 BVT 항목 (Requirements 6.3)
        lines.append("## 미매칭 BVT 항목")
        lines.append("")
        if report.unmatched_bvt_cases:
            lines.append("| BVT No. | Category | Check |")
            lines.append("|---------|----------|-------|")
            for bvt_case in report.unmatched_bvt_cases:
                category = self._format_category(bvt_case)
                check = self._truncate(bvt_case.check, 50)
                lines.append(f"| {bvt_case.no} | {category} | {check} |")
        else:
            lines.append("모든 BVT 항목이 매칭되었습니다.")
        lines.append("")
        
        return "\n".join(lines)
    
    def _format_category(self, bvt_case: BVTTestCase) -> str:
        """카테고리 포맷팅
        
        Args:
            bvt_case: BVT 테스트 케이스
            
        Returns:
            포맷된 카테고리 문자열
        """
        categories = [
            bvt_case.category1,
            bvt_case.category2,
            bvt_case.category3
        ]
        # 빈 문자열 제외하고 결합
        non_empty = [c for c in categories if c]
        return " > ".join(non_empty) if non_empty else "-"
    
    def _truncate(self, text: str, max_length: int) -> str:
        """텍스트 자르기
        
        Args:
            text: 원본 텍스트
            max_length: 최대 길이
            
        Returns:
            잘린 텍스트
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
