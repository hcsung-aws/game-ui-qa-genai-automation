"""
Property-based tests for BVT Parser

**Feature: bvt-semantic-integration, Property 1: BVT 파싱 정확성**
**Feature: bvt-semantic-integration, Property 14: BVT 파일 round-trip**

Validates: Requirements 1.1, 1.2, 5.5, 5.7
"""

import os
import sys
import tempfile
from pathlib import Path
from hypothesis import given, settings, strategies as st, assume

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.bvt_integration.models import BVTTestCase
from src.bvt_integration.bvt_parser import BVTParser, BVTParseError


# ============================================================================
# Strategies (전략 정의)
# ============================================================================

# CSV 안전 텍스트 전략 (줄바꿈, 쉼표 제외)
csv_safe_text_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S'),
        blacklist_characters='\x00\n\r,'
    ),
    min_size=0,
    max_size=50
)

# 비어있지 않은 CSV 안전 텍스트
non_empty_csv_safe_text = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S'),
        blacklist_characters='\x00\n\r,'
    ),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != '')

# 테스트 결과 전략
test_result_strategy = st.sampled_from([
    "Not Tested", "PASS", "Fail", "N/A", "Block"
])

# BVTTestCase 전략 (CSV 안전 문자만 사용)
bvt_test_case_for_csv_strategy = st.builds(
    BVTTestCase,
    no=st.integers(min_value=1, max_value=10000),
    category1=csv_safe_text_strategy,
    category2=csv_safe_text_strategy,
    category3=csv_safe_text_strategy,
    check=non_empty_csv_safe_text,  # Check는 비어있으면 안됨
    test_result=test_result_strategy,
    bts_id=csv_safe_text_strategy,
    comment=csv_safe_text_strategy
)


# ============================================================================
# Property 1: BVT 파싱 정확성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(test_cases=st.lists(bvt_test_case_for_csv_strategy, min_size=1, max_size=20))
def test_bvt_parsing_accuracy(test_cases):
    """
    **Feature: bvt-semantic-integration, Property 1: BVT 파싱 정확성**
    
    *For any* 유효한 BVT CSV 파일, BVT_Parser로 파싱한 결과는 파일 내 모든 
    테스트 케이스 행을 포함하고, 각 BVT_Test_Case 객체는 No., Category 1~3, 
    Check, Test Result, BTS ID, Comment 필드를 정확히 포함해야 한다.
    
    **Validates: Requirements 1.1, 1.2**
    """
    # No. 값이 고유하도록 조정
    unique_test_cases = []
    seen_nos = set()
    for tc in test_cases:
        if tc.no not in seen_nos:
            seen_nos.add(tc.no)
            unique_test_cases.append(tc)
    
    assume(len(unique_test_cases) > 0)
    
    parser = BVTParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_bvt.csv"
        
        # CSV 파일 작성
        parser.write(unique_test_cases, str(csv_path))
        
        # CSV 파일 파싱
        parsed_cases = parser.parse(str(csv_path))
        
        # 파싱된 케이스 수 검증
        assert len(parsed_cases) == len(unique_test_cases), \
            f"파싱된 케이스 수 불일치: {len(parsed_cases)} != {len(unique_test_cases)}"
        
        # 각 케이스의 필드 검증
        for original, parsed in zip(unique_test_cases, parsed_cases):
            assert parsed.no == original.no, \
                f"No. 불일치: {parsed.no} != {original.no}"
            assert parsed.category1 == original.category1, \
                f"Category 1 불일치: {parsed.category1} != {original.category1}"
            assert parsed.category2 == original.category2, \
                f"Category 2 불일치: {parsed.category2} != {original.category2}"
            assert parsed.category3 == original.category3, \
                f"Category 3 불일치: {parsed.category3} != {original.category3}"
            assert parsed.check == original.check, \
                f"Check 불일치: {parsed.check} != {original.check}"
            assert parsed.test_result == original.test_result, \
                f"Test Result 불일치: {parsed.test_result} != {original.test_result}"
            assert parsed.bts_id == original.bts_id, \
                f"BTS ID 불일치: {parsed.bts_id} != {original.bts_id}"
            assert parsed.comment == original.comment, \
                f"Comment 불일치: {parsed.comment} != {original.comment}"


@settings(max_examples=100, deadline=None)
@given(test_cases=st.lists(bvt_test_case_for_csv_strategy, min_size=1, max_size=10))
def test_bvt_parsing_preserves_all_fields(test_cases):
    """
    **Feature: bvt-semantic-integration, Property 1 확장: 필드 보존**
    
    *For any* BVT 테스트 케이스, 파싱 후 모든 필수 필드가 보존되어야 한다.
    
    **Validates: Requirements 1.1, 1.2**
    """
    # No. 값이 고유하도록 조정
    unique_test_cases = []
    seen_nos = set()
    for tc in test_cases:
        if tc.no not in seen_nos:
            seen_nos.add(tc.no)
            unique_test_cases.append(tc)
    
    assume(len(unique_test_cases) > 0)
    
    parser = BVTParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_bvt.csv"
        
        # CSV 파일 작성
        parser.write(unique_test_cases, str(csv_path))
        
        # CSV 파일 파싱
        parsed_cases = parser.parse(str(csv_path))
        
        # 각 파싱된 케이스가 모든 필수 필드를 가지고 있는지 검증
        for parsed in parsed_cases:
            assert hasattr(parsed, 'no'), "no 필드 누락"
            assert hasattr(parsed, 'category1'), "category1 필드 누락"
            assert hasattr(parsed, 'category2'), "category2 필드 누락"
            assert hasattr(parsed, 'category3'), "category3 필드 누락"
            assert hasattr(parsed, 'check'), "check 필드 누락"
            assert hasattr(parsed, 'test_result'), "test_result 필드 누락"
            assert hasattr(parsed, 'bts_id'), "bts_id 필드 누락"
            assert hasattr(parsed, 'comment'), "comment 필드 누락"
            
            # 타입 검증
            assert isinstance(parsed.no, int), f"no는 int여야 함: {type(parsed.no)}"
            assert isinstance(parsed.category1, str), f"category1은 str이어야 함"
            assert isinstance(parsed.category2, str), f"category2는 str이어야 함"
            assert isinstance(parsed.category3, str), f"category3은 str이어야 함"
            assert isinstance(parsed.check, str), f"check는 str이어야 함"
            assert isinstance(parsed.test_result, str), f"test_result는 str이어야 함"
            assert isinstance(parsed.bts_id, str), f"bts_id는 str이어야 함"
            assert isinstance(parsed.comment, str), f"comment는 str이어야 함"


# ============================================================================
# Property 14: BVT 파일 round-trip
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(test_cases=st.lists(bvt_test_case_for_csv_strategy, min_size=1, max_size=20))
def test_bvt_file_round_trip(test_cases):
    """
    **Feature: bvt-semantic-integration, Property 14: BVT 파일 round-trip**
    
    *For any* BVT_Test_Case 리스트, BVTParser.write()로 CSV 파일을 생성한 후 
    BVTParser.parse()로 다시 파싱하면 원본과 동등한 리스트가 생성되어야 한다.
    
    **Validates: Requirements 5.5, 5.7**
    """
    # No. 값이 고유하도록 조정
    unique_test_cases = []
    seen_nos = set()
    for tc in test_cases:
        if tc.no not in seen_nos:
            seen_nos.add(tc.no)
            unique_test_cases.append(tc)
    
    assume(len(unique_test_cases) > 0)
    
    parser = BVTParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_bvt.csv"
        
        # 첫 번째 write
        parser.write(unique_test_cases, str(csv_path))
        
        # 첫 번째 parse
        parsed_cases = parser.parse(str(csv_path))
        
        # 원본과 파싱 결과 비교
        assert len(parsed_cases) == len(unique_test_cases), \
            f"케이스 수 불일치: {len(parsed_cases)} != {len(unique_test_cases)}"
        
        for original, parsed in zip(unique_test_cases, parsed_cases):
            assert parsed == original, \
                f"round-trip 후 케이스 불일치: {parsed} != {original}"


@settings(max_examples=100, deadline=None)
@given(test_cases=st.lists(bvt_test_case_for_csv_strategy, min_size=1, max_size=10))
def test_bvt_file_double_round_trip(test_cases):
    """
    **Feature: bvt-semantic-integration, Property 14 확장: 이중 round-trip**
    
    *For any* BVT_Test_Case 리스트, 두 번 연속 write/parse해도 결과가 동일해야 한다.
    
    **Validates: Requirements 5.5, 5.7**
    """
    # No. 값이 고유하도록 조정
    unique_test_cases = []
    seen_nos = set()
    for tc in test_cases:
        if tc.no not in seen_nos:
            seen_nos.add(tc.no)
            unique_test_cases.append(tc)
    
    assume(len(unique_test_cases) > 0)
    
    parser = BVTParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path1 = Path(tmpdir) / "test_bvt_1.csv"
        csv_path2 = Path(tmpdir) / "test_bvt_2.csv"
        
        # 첫 번째 round-trip
        parser.write(unique_test_cases, str(csv_path1))
        parsed_cases1 = parser.parse(str(csv_path1))
        
        # 두 번째 round-trip
        parser.write(parsed_cases1, str(csv_path2))
        parsed_cases2 = parser.parse(str(csv_path2))
        
        # 두 번째 결과가 첫 번째와 동일해야 함
        assert len(parsed_cases2) == len(parsed_cases1), \
            "이중 round-trip 후 케이스 수 불일치"
        
        for case1, case2 in zip(parsed_cases1, parsed_cases2):
            assert case2 == case1, \
                f"이중 round-trip 후 케이스 불일치: {case2} != {case1}"


# ============================================================================
# 단위 테스트
# ============================================================================

def test_parse_nonexistent_file():
    """존재하지 않는 파일 파싱 시 FileNotFoundError 발생"""
    parser = BVTParser()
    
    try:
        parser.parse("nonexistent_file.csv")
        assert False, "FileNotFoundError가 발생해야 함"
    except FileNotFoundError:
        pass


def test_parse_invalid_csv_format():
    """잘못된 형식의 CSV 파일 파싱 시 BVTParseError 발생"""
    parser = BVTParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "invalid.csv"
        
        # 필수 컬럼이 없는 CSV 파일 생성
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("col1,col2,col3\n")
            f.write("a,b,c\n")
        
        try:
            parser.parse(str(csv_path))
            assert False, "BVTParseError가 발생해야 함"
        except BVTParseError as e:
            assert "필수 컬럼" in str(e)


def test_parse_empty_csv():
    """빈 CSV 파일 파싱"""
    parser = BVTParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "empty.csv"
        
        # 빈 파일 생성
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("")
        
        try:
            parser.parse(str(csv_path))
            assert False, "BVTParseError가 발생해야 함"
        except BVTParseError:
            pass


def test_parse_header_only_csv():
    """헤더만 있는 CSV 파일 파싱"""
    parser = BVTParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "header_only.csv"
        
        # 헤더만 있는 파일 생성
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(",No.,Category 1,Category 2,Category 3,Check,,,Test Result (PC),BTS ID,Comment\n")
        
        result = parser.parse(str(csv_path))
        assert len(result) == 0, "헤더만 있는 파일은 빈 리스트를 반환해야 함"


def test_parse_skips_summary_rows():
    """요약 행을 건너뛰는지 확인"""
    parser = BVTParser()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "with_summary.csv"
        
        # 요약 행이 포함된 파일 생성
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(",Result,,Count,Rate,설명\n")
            f.write(",PASS,,0,0.00%,테스트 성공\n")
            f.write(",No.,Category 1,Category 2,Category 3,Check,,,Test Result (PC),BTS ID,Comment\n")
            f.write(",1,메인화면,공통 UI,최초 접속,테스트 항목,,,Not Tested,,\n")
        
        result = parser.parse(str(csv_path))
        assert len(result) == 1, f"테스트 케이스 1개만 파싱되어야 함: {len(result)}"
        assert result[0].no == 1
        assert result[0].category1 == "메인화면"


def test_write_creates_directory():
    """write 메서드가 디렉토리를 자동 생성하는지 확인"""
    parser = BVTParser()
    test_case = BVTTestCase(
        no=1, category1="Test", category2="", category3="",
        check="Check", test_result="Not Tested", bts_id="", comment=""
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "subdir" / "test.csv"
        
        parser.write([test_case], str(csv_path))
        
        assert csv_path.exists(), "파일이 생성되어야 함"
        assert csv_path.parent.exists(), "디렉토리가 생성되어야 함"


def test_parse_real_bvt_sample():
    """실제 BVT 샘플 파일 파싱 테스트"""
    parser = BVTParser()
    
    # 실제 BVT 파일 찾기 (예제 제외)
    sample_path = None
    for path in Path("bvt_samples").glob("BVT_*.csv"):
        if "example" not in path.name.lower():
            sample_path = path
            break
    
    # 실제 파일이 없으면 예제 파일 사용
    if sample_path is None:
        sample_path = Path("bvt_samples/BVT_example.csv")
    
    if not sample_path.exists():
        return  # 파일이 없으면 스킵
    
    result = parser.parse(str(sample_path))
    
    # 기본 검증
    assert len(result) > 0, "파싱된 케이스가 있어야 함"
    
    # 첫 번째 케이스 검증
    first_case = result[0]
    assert first_case.no == 1
    assert first_case.category1 == "메인화면"
    
    # 모든 케이스가 유효한 No.를 가지는지 확인
    for case in result:
        assert case.no > 0, f"No.는 양수여야 함: {case.no}"
        assert case.check, f"Check는 비어있으면 안됨: No.{case.no}"
