"""
BVT 문서 업데이터

테스트 결과를 BVT 문서에 반영하여 새로운 BVT 파일을 생성한다.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from .models import BVTTestCase, PlayTestResult, TestStatus
from .bvt_parser import BVTParser


logger = logging.getLogger(__name__)


class BVTUpdater:
    """BVT 문서 업데이터
    
    테스트 결과를 BVT 케이스에 반영하고 새로운 BVT 파일을 생성한다.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
    """
    
    def __init__(self, parser: Optional[BVTParser] = None):
        """업데이터 초기화
        
        Args:
            parser: BVT 파서 인스턴스 (None이면 새로 생성)
        """
        self.parser = parser or BVTParser()
    
    def update(
        self, 
        bvt_cases: List[BVTTestCase], 
        results: List[PlayTestResult]
    ) -> List[BVTTestCase]:
        """테스트 결과를 BVT 케이스에 반영
        
        Args:
            bvt_cases: 원본 BVT 케이스 리스트
            results: 플레이 테스트 결과 리스트
            
        Returns:
            업데이트된 BVT 케이스 리스트
            
        Requirements: 5.1, 5.2, 5.3, 5.4
        """
        # 결과를 BVT 번호로 인덱싱
        results_by_bvt_no: Dict[int, PlayTestResult] = {
            result.bvt_no: result for result in results
        }
        
        updated_cases: List[BVTTestCase] = []
        
        for bvt_case in bvt_cases:
            result = results_by_bvt_no.get(bvt_case.no)
            
            if result is not None:
                # 테스트 결과가 있는 경우 업데이트
                updated_case = self._apply_result(bvt_case, result)
            else:
                # 테스트 결과가 없는 경우 원본 유지 (BTS ID 보존)
                updated_case = BVTTestCase(
                    no=bvt_case.no,
                    category1=bvt_case.category1,
                    category2=bvt_case.category2,
                    category3=bvt_case.category3,
                    check=bvt_case.check,
                    test_result=bvt_case.test_result,
                    bts_id=bvt_case.bts_id,  # BTS ID 보존
                    comment=bvt_case.comment
                )
            
            updated_cases.append(updated_case)
        
        logger.info(
            f"BVT 업데이트 완료: {len(results)}개 결과 반영, "
            f"총 {len(updated_cases)}개 케이스"
        )
        
        return updated_cases
    
    def _apply_result(
        self, 
        bvt_case: BVTTestCase, 
        result: PlayTestResult
    ) -> BVTTestCase:
        """단일 BVT 케이스에 테스트 결과 적용
        
        Args:
            bvt_case: 원본 BVT 케이스
            result: 플레이 테스트 결과
            
        Returns:
            업데이트된 BVT 케이스
            
        Requirements: 5.1, 5.2, 5.3, 5.4
        """
        # 테스트 결과 설정
        if result.status == TestStatus.PASS:
            test_result = "PASS"
            comment = bvt_case.comment  # 성공 시 기존 코멘트 유지
        elif result.status == TestStatus.FAIL:
            test_result = "Fail"
            # 실패 시 오류 정보를 코멘트에 추가
            error_info = result.error_message or "자동 테스트 실패"
            if bvt_case.comment:
                comment = f"{bvt_case.comment} | [Auto] {error_info}"
            else:
                comment = f"[Auto] {error_info}"
        elif result.status == TestStatus.BLOCKED:
            test_result = "Block"
            error_info = result.error_message or "테스트 차단됨"
            if bvt_case.comment:
                comment = f"{bvt_case.comment} | [Auto] {error_info}"
            else:
                comment = f"[Auto] {error_info}"
        else:
            # NOT_TESTED 또는 기타
            test_result = bvt_case.test_result
            comment = bvt_case.comment
        
        return BVTTestCase(
            no=bvt_case.no,
            category1=bvt_case.category1,
            category2=bvt_case.category2,
            category3=bvt_case.category3,
            check=bvt_case.check,
            test_result=test_result,
            bts_id=bvt_case.bts_id,  # BTS ID 보존 (Requirements 5.4)
            comment=comment
        )
    
    def save(
        self, 
        bvt_cases: List[BVTTestCase], 
        output_dir: str
    ) -> str:
        """업데이트된 BVT를 파일로 저장
        
        파일명에 타임스탬프를 포함하여 저장한다.
        
        Args:
            bvt_cases: 저장할 BVT 케이스 리스트
            output_dir: 출력 디렉토리
            
        Returns:
            저장된 파일 경로
            
        Requirements: 5.5, 5.6
        """
        # 출력 디렉토리 생성
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 타임스탬프 포함 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"BVT_updated_{timestamp}.csv"
        file_path = output_path / filename
        
        # CSV 파일로 저장
        self.parser.write(bvt_cases, str(file_path))
        
        logger.info(f"업데이트된 BVT 파일 저장: {file_path}")
        
        return str(file_path)
