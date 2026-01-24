"""
BVT CSV 파일 파서

BVT(Build Verification Test) CSV 파일을 파싱하여 BVTTestCase 객체로 변환하고,
BVTTestCase 리스트를 CSV 파일로 저장하는 기능을 제공한다.

Requirements: 1.1, 1.2, 1.3, 1.4
"""

import csv
import logging
from pathlib import Path
from typing import List, Optional

from .models import BVTTestCase


logger = logging.getLogger(__name__)


class BVTParseError(Exception):
    """BVT 파싱 오류
    
    BVT CSV 파일 파싱 중 발생하는 오류를 나타낸다.
    """
    pass


class BVTParser:
    """BVT CSV 파일 파서
    
    BVT CSV 파일을 파싱하여 BVTTestCase 객체 리스트로 변환하고,
    BVTTestCase 리스트를 CSV 파일로 저장한다.
    
    Requirements: 1.1, 1.2, 1.3, 1.4
    """
    
    # BVT CSV 파일의 필수 컬럼 (헤더 행에서 확인)
    REQUIRED_COLUMNS = ['No.', 'Category 1', 'Category 2', 'Category 3', 'Check']
    
    # 컬럼 인덱스 (0-based, 첫 번째 빈 컬럼 제외)
    COL_NO = 1
    COL_CATEGORY1 = 2
    COL_CATEGORY2 = 3
    COL_CATEGORY3 = 4
    COL_CHECK = 5
    COL_TEST_RESULT = 8  # 'Test Result (PC)' 컬럼
    COL_BTS_ID = 9
    COL_COMMENT = 10
    
    def __init__(self):
        """파서 초기화"""
        self._header_row_index: Optional[int] = None
    
    def parse(self, file_path: str) -> List[BVTTestCase]:
        """BVT CSV 파일을 파싱하여 테스트 케이스 리스트 반환
        
        Args:
            file_path: BVT CSV 파일 경로
            
        Returns:
            BVTTestCase 객체 리스트
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            BVTParseError: 파싱 실패 시
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"BVT 파일을 찾을 수 없습니다: {file_path}")
        
        if not path.is_file():
            raise BVTParseError(f"유효한 파일이 아닙니다: {file_path}")
        
        try:
            return self._parse_csv(path)
        except UnicodeDecodeError as e:
            raise BVTParseError(f"파일 인코딩 오류: {e}")
        except csv.Error as e:
            raise BVTParseError(f"CSV 파싱 오류: {e}")
    
    def _parse_csv(self, path: Path) -> List[BVTTestCase]:
        """CSV 파일 파싱 내부 구현
        
        Args:
            path: CSV 파일 경로
            
        Returns:
            BVTTestCase 객체 리스트
        """
        test_cases: List[BVTTestCase] = []
        
        # 여러 인코딩 시도
        encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr']
        content_lines: List[List[str]] = []
        
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding, newline='') as f:
                    reader = csv.reader(f)
                    content_lines = list(reader)
                break
            except UnicodeDecodeError:
                continue
        
        if not content_lines:
            raise BVTParseError("지원되는 인코딩으로 파일을 읽을 수 없습니다")
        
        # 헤더 행 찾기
        header_row_index = self._find_header_row(content_lines)
        if header_row_index is None:
            raise BVTParseError(
                f"필수 컬럼을 찾을 수 없습니다: {self.REQUIRED_COLUMNS}"
            )
        
        self._header_row_index = header_row_index
        
        # 데이터 행 파싱 (헤더 다음 행부터)
        for row_index, row in enumerate(content_lines[header_row_index + 1:], 
                                         start=header_row_index + 2):
            test_case = self._parse_row(row, row_index)
            if test_case is not None:
                test_cases.append(test_case)
        
        logger.info(f"BVT 파일 파싱 완료: {len(test_cases)}개 테스트 케이스")
        return test_cases
    
    def _find_header_row(self, lines: List[List[str]]) -> Optional[int]:
        """헤더 행 인덱스 찾기
        
        Args:
            lines: CSV 행 리스트
            
        Returns:
            헤더 행 인덱스 또는 None
        """
        for i, row in enumerate(lines):
            # 행을 문자열로 결합하여 필수 컬럼 확인
            row_text = ','.join(row)
            if all(col in row_text for col in self.REQUIRED_COLUMNS):
                return i
        return None
    
    def _parse_row(self, row: List[str], row_index: int) -> Optional[BVTTestCase]:
        """단일 행 파싱
        
        Args:
            row: CSV 행 데이터
            row_index: 행 번호 (1-based, 로깅용)
            
        Returns:
            BVTTestCase 객체 또는 None (유효하지 않은 행)
        """
        # 빈 행 또는 너무 짧은 행 건너뛰기
        if len(row) < self.COL_CHECK + 1:
            return None
        
        # No. 컬럼이 숫자가 아니면 건너뛰기 (요약 행 등)
        no_value = self._get_cell(row, self.COL_NO)
        if not no_value or not self._is_valid_no(no_value):
            return None
        
        try:
            no = int(no_value)
        except ValueError:
            return None
        
        # Check 컬럼이 비어있으면 건너뛰기
        check = self._get_cell(row, self.COL_CHECK)
        if not check:
            return None
        
        return BVTTestCase(
            no=no,
            category1=self._get_cell(row, self.COL_CATEGORY1),
            category2=self._get_cell(row, self.COL_CATEGORY2),
            category3=self._get_cell(row, self.COL_CATEGORY3),
            check=check,
            test_result=self._get_cell(row, self.COL_TEST_RESULT) or "Not Tested",
            bts_id=self._get_cell(row, self.COL_BTS_ID),
            comment=self._get_cell(row, self.COL_COMMENT)
        )
    
    def _get_cell(self, row: List[str], index: int) -> str:
        """셀 값 안전하게 가져오기
        
        Args:
            row: CSV 행 데이터
            index: 컬럼 인덱스
            
        Returns:
            셀 값 (없으면 빈 문자열)
        """
        if index < len(row):
            return row[index].strip()
        return ""
    
    def _is_valid_no(self, value: str) -> bool:
        """No. 값이 유효한지 확인
        
        Args:
            value: No. 컬럼 값
            
        Returns:
            유효 여부
        """
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def write(self, test_cases: List[BVTTestCase], output_path: str) -> None:
        """BVT 테스트 케이스를 CSV 파일로 저장
        
        Args:
            test_cases: 저장할 테스트 케이스 리스트
            output_path: 출력 파일 경로
            
        Raises:
            BVTParseError: 저장 실패 시
        """
        path = Path(output_path)
        
        # 디렉토리 생성
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                
                # 헤더 행 작성
                header = [
                    '',  # 첫 번째 빈 컬럼
                    'No.',
                    'Category 1',
                    'Category 2',
                    'Category 3',
                    'Check',
                    '',  # 빈 컬럼
                    '',  # 빈 컬럼
                    'Test Result (PC)',
                    'BTS ID',
                    'Comment'
                ]
                writer.writerow(header)
                
                # 데이터 행 작성
                for tc in test_cases:
                    row = [
                        '',  # 첫 번째 빈 컬럼
                        tc.no,
                        tc.category1,
                        tc.category2,
                        tc.category3,
                        tc.check,
                        '',  # 빈 컬럼
                        '',  # 빈 컬럼
                        tc.test_result,
                        tc.bts_id,
                        tc.comment
                    ]
                    writer.writerow(row)
                
                logger.info(f"BVT 파일 저장 완료: {output_path} ({len(test_cases)}개)")
                
        except IOError as e:
            raise BVTParseError(f"파일 저장 오류: {e}")
