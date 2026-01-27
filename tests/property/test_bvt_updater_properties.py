"""
Property-based tests for BVTUpdater

**Feature: bvt-semantic-integration, Property 12: BVT 업데이트 정확성**
**Feature: bvt-semantic-integration, Property 13: BTS ID 보존**

Validates: Requirements 5.1, 5.2, 5.3, 5.4
"""

import os
import sys
import tempfile
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.bvt_integration.models import (
    BVTTestCase,
    PlayTestResult,
    TestStatus
)
from src.bvt_integration.bvt_updater import BVTUpdater
from src.bvt_integration.bvt_parser import BVTParser


# ============================================================================
# Strategies (전략 정의)
# ============================================================================

# 텍스트 전략 (유효한 문자열만)
safe_text_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\x00\n\r'
    ),
    min_size=0,
    max_size=50
)

# 비어있지 않은 텍스트 전략
non_empty_text_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\x00\n\r'
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

# TestStatus 전략 (PASS, FAIL, BLOCKED만)
actionable_test_status_strategy = st.sampled_from([
    TestStatus.PASS, TestStatus.FAIL, TestStatus.BLOCKED
])

# PlayTestResult 전략
play_test_result_strategy = st.builds(
    PlayTestResult,
    play_test_name=non_empty_text_strategy,
    bvt_no=st.integers(min_value=1, max_value=10000),
    status=actionable_test_status_strategy,
    executed_actions=st.integers(min_value=0, max_value=100),
    failed_actions=st.integers(min_value=0, max_value=100),
    screenshots=st.lists(safe_text_strategy, min_size=0, max_size=5),
    error_message=st.one_of(st.none(), safe_text_strategy),
    execution_time=st.floats(min_value=0.0, max_value=3600.0, allow_nan=False, allow_infinity=False)
)


# ============================================================================
# Property 12: BVT 업데이트 정확성
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    bvt_case=bvt_test_case_strategy,
    status=actionable_test_status_strategy,
    error_message=st.one_of(st.none(), non_empty_text_strategy)
)
def test_bvt_update_accuracy_pass(bvt_case, status, error_message):
    """
    **Feature: bvt-semantic-integration, Property 12: BVT 업데이트 정확성**
    
    *For any* BVT_Test_Case와 PlayTestResult 쌍, BVTUpdater.update()의 결과는 
    PlayTestResult.status가 PASS이면 test_result가 "PASS"이고, 
    FAIL이면 test_result가 "Fail"이며 comment에 오류 정보가 추가되어야 한다.
    
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    updater = BVTUpdater()
    
    # 테스트 결과 생성
    result = PlayTestResult(
        play_test_name="test_play",
        bvt_no=bvt_case.no,
        status=status,
        executed_actions=5,
        failed_actions=0 if status == TestStatus.PASS else 1,
        screenshots=[],
        error_message=error_message,
        execution_time=1.0
    )
    
    # 업데이트 수행
    updated_cases = updater.update([bvt_case], [result])
    
    assert len(updated_cases) == 1
    updated = updated_cases[0]
    
    # 상태별 검증
    if status == TestStatus.PASS:
        assert updated.test_result == "PASS", \
            f"PASS 상태인데 test_result가 {updated.test_result}"
    elif status == TestStatus.FAIL:
        assert updated.test_result == "Fail", \
            f"FAIL 상태인데 test_result가 {updated.test_result}"
        # 오류 메시지가 있으면 코멘트에 포함되어야 함
        if error_message:
            assert "[Auto]" in updated.comment, \
                "FAIL 시 코멘트에 [Auto] 태그가 있어야 함"
    elif status == TestStatus.BLOCKED:
        assert updated.test_result == "Block", \
            f"BLOCKED 상태인데 test_result가 {updated.test_result}"


@settings(max_examples=100, deadline=None)
@given(
    bvt_cases=st.lists(bvt_test_case_strategy, min_size=1, max_size=10, unique_by=lambda x: x.no)
)
def test_bvt_update_multiple_cases(bvt_cases):
    """
    **Feature: bvt-semantic-integration, Property 12 확장: 다중 케이스 업데이트**
    
    여러 BVT 케이스를 업데이트할 때 각 케이스가 올바르게 업데이트되어야 한다.
    
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    updater = BVTUpdater()
    
    # 일부 케이스에 대해서만 결과 생성 (절반)
    results = []
    for i, bvt_case in enumerate(bvt_cases):
        if i % 2 == 0:
            results.append(PlayTestResult(
                play_test_name=f"test_{bvt_case.no}",
                bvt_no=bvt_case.no,
                status=TestStatus.PASS,
                executed_actions=5,
                failed_actions=0,
                screenshots=[],
                error_message=None,
                execution_time=1.0
            ))
    
    # 업데이트 수행
    updated_cases = updater.update(bvt_cases, results)
    
    # 결과 검증
    assert len(updated_cases) == len(bvt_cases)
    
    result_bvt_nos = {r.bvt_no for r in results}
    for i, updated in enumerate(updated_cases):
        original = bvt_cases[i]
        if original.no in result_bvt_nos:
            # 결과가 있는 케이스는 업데이트됨
            assert updated.test_result == "PASS"
        else:
            # 결과가 없는 케이스는 원본 유지
            assert updated.test_result == original.test_result


# ============================================================================
# Property 13: BTS ID 보존
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    bvt_case=bvt_test_case_strategy,
    status=actionable_test_status_strategy
)
def test_bts_id_preservation(bvt_case, status):
    """
    **Feature: bvt-semantic-integration, Property 13: BTS ID 보존**
    
    *For any* BVT_Test_Case와 PlayTestResult 쌍, BVTUpdater.update() 후에도 
    원본 BVT_Test_Case의 bts_id 값은 변경되지 않아야 한다.
    
    **Validates: Requirements 5.4**
    """
    updater = BVTUpdater()
    original_bts_id = bvt_case.bts_id
    
    # 테스트 결과 생성
    result = PlayTestResult(
        play_test_name="test_play",
        bvt_no=bvt_case.no,
        status=status,
        executed_actions=5,
        failed_actions=0 if status == TestStatus.PASS else 1,
        screenshots=[],
        error_message="Test error" if status == TestStatus.FAIL else None,
        execution_time=1.0
    )
    
    # 업데이트 수행
    updated_cases = updater.update([bvt_case], [result])
    
    assert len(updated_cases) == 1
    updated = updated_cases[0]
    
    # BTS ID 보존 검증
    assert updated.bts_id == original_bts_id, \
        f"BTS ID가 변경됨: {original_bts_id} -> {updated.bts_id}"


@settings(max_examples=100, deadline=None)
@given(
    bvt_cases=st.lists(bvt_test_case_strategy, min_size=1, max_size=10, unique_by=lambda x: x.no)
)
def test_bts_id_preservation_all_cases(bvt_cases):
    """
    **Feature: bvt-semantic-integration, Property 13 확장: 모든 케이스 BTS ID 보존**
    
    여러 BVT 케이스를 업데이트할 때 모든 케이스의 BTS ID가 보존되어야 한다.
    
    **Validates: Requirements 5.4**
    """
    updater = BVTUpdater()
    
    # 원본 BTS ID 저장
    original_bts_ids = {case.no: case.bts_id for case in bvt_cases}
    
    # 모든 케이스에 대해 결과 생성
    results = [
        PlayTestResult(
            play_test_name=f"test_{case.no}",
            bvt_no=case.no,
            status=TestStatus.PASS,
            executed_actions=5,
            failed_actions=0,
            screenshots=[],
            error_message=None,
            execution_time=1.0
        )
        for case in bvt_cases
    ]
    
    # 업데이트 수행
    updated_cases = updater.update(bvt_cases, results)
    
    # 모든 BTS ID 보존 검증
    for updated in updated_cases:
        original_bts_id = original_bts_ids[updated.no]
        assert updated.bts_id == original_bts_id, \
            f"BVT #{updated.no}의 BTS ID가 변경됨: {original_bts_id} -> {updated.bts_id}"


@settings(max_examples=100, deadline=None)
@given(bvt_case=bvt_test_case_strategy)
def test_bts_id_preservation_no_result(bvt_case):
    """
    **Feature: bvt-semantic-integration, Property 13 확장: 결과 없을 때 BTS ID 보존**
    
    테스트 결과가 없는 BVT 케이스도 BTS ID가 보존되어야 한다.
    
    **Validates: Requirements 5.4**
    """
    updater = BVTUpdater()
    original_bts_id = bvt_case.bts_id
    
    # 빈 결과로 업데이트
    updated_cases = updater.update([bvt_case], [])
    
    assert len(updated_cases) == 1
    updated = updated_cases[0]
    
    # BTS ID 보존 검증
    assert updated.bts_id == original_bts_id, \
        f"결과 없을 때 BTS ID가 변경됨: {original_bts_id} -> {updated.bts_id}"


# ============================================================================
# 추가 속성 테스트
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(bvt_case=bvt_test_case_strategy)
def test_update_preserves_other_fields(bvt_case):
    """
    업데이트 시 test_result, comment 외의 필드는 보존되어야 한다.
    
    **Validates: Requirements 5.4, 5.5**
    """
    updater = BVTUpdater()
    
    result = PlayTestResult(
        play_test_name="test_play",
        bvt_no=bvt_case.no,
        status=TestStatus.PASS,
        executed_actions=5,
        failed_actions=0,
        screenshots=[],
        error_message=None,
        execution_time=1.0
    )
    
    updated_cases = updater.update([bvt_case], [result])
    updated = updated_cases[0]
    
    # 변경되지 않아야 하는 필드 검증
    assert updated.no == bvt_case.no, "no 필드가 변경됨"
    assert updated.category1 == bvt_case.category1, "category1 필드가 변경됨"
    assert updated.category2 == bvt_case.category2, "category2 필드가 변경됨"
    assert updated.category3 == bvt_case.category3, "category3 필드가 변경됨"
    assert updated.check == bvt_case.check, "check 필드가 변경됨"
    assert updated.bts_id == bvt_case.bts_id, "bts_id 필드가 변경됨"


@settings(max_examples=50, deadline=None)
@given(
    bvt_case=bvt_test_case_strategy,
    original_comment=safe_text_strategy,
    error_message=non_empty_text_strategy
)
def test_fail_comment_appends_to_existing(bvt_case, original_comment, error_message):
    """
    FAIL 시 기존 코멘트에 오류 정보가 추가되어야 한다.
    
    **Validates: Requirements 5.3**
    """
    updater = BVTUpdater()
    
    # 기존 코멘트가 있는 BVT 케이스
    bvt_case_with_comment = BVTTestCase(
        no=bvt_case.no,
        category1=bvt_case.category1,
        category2=bvt_case.category2,
        category3=bvt_case.category3,
        check=bvt_case.check,
        test_result=bvt_case.test_result,
        bts_id=bvt_case.bts_id,
        comment=original_comment
    )
    
    result = PlayTestResult(
        play_test_name="test_play",
        bvt_no=bvt_case.no,
        status=TestStatus.FAIL,
        executed_actions=5,
        failed_actions=1,
        screenshots=[],
        error_message=error_message,
        execution_time=1.0
    )
    
    updated_cases = updater.update([bvt_case_with_comment], [result])
    updated = updated_cases[0]
    
    # 기존 코멘트가 있으면 보존되어야 함
    if original_comment:
        assert original_comment in updated.comment, \
            f"기존 코멘트가 보존되지 않음: '{original_comment}' not in '{updated.comment}'"
    
    # 오류 정보가 추가되어야 함
    assert "[Auto]" in updated.comment, "오류 정보 태그가 없음"


# ============================================================================
# 단위 테스트
# ============================================================================

def test_updater_initialization():
    """BVTUpdater 초기화 테스트"""
    # 기본 초기화
    updater1 = BVTUpdater()
    assert updater1.parser is not None
    
    # 커스텀 파서로 초기화
    custom_parser = BVTParser()
    updater2 = BVTUpdater(parser=custom_parser)
    assert updater2.parser is custom_parser


def test_update_empty_inputs():
    """빈 입력 처리 테스트"""
    updater = BVTUpdater()
    
    # 빈 BVT 케이스
    result = updater.update([], [])
    assert result == []
    
    # 빈 결과
    bvt_case = BVTTestCase(
        no=1, category1="Test", category2="", category3="",
        check="Check", test_result="Not Tested", bts_id="BUG-123", comment=""
    )
    result = updater.update([bvt_case], [])
    assert len(result) == 1
    assert result[0].bts_id == "BUG-123"


def test_save_creates_file():
    """save() 메서드가 파일을 생성하는지 테스트"""
    updater = BVTUpdater()
    
    bvt_cases = [
        BVTTestCase(
            no=1, category1="Test", category2="Sub", category3="",
            check="Check item", test_result="PASS", bts_id="", comment=""
        )
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = updater.save(bvt_cases, tmpdir)
        
        assert os.path.exists(output_path)
        assert "BVT_updated_" in output_path
        assert output_path.endswith(".csv")


def test_update_mismatched_bvt_no():
    """BVT 번호가 일치하지 않는 결과는 무시되어야 함"""
    updater = BVTUpdater()
    
    bvt_case = BVTTestCase(
        no=1, category1="Test", category2="", category3="",
        check="Check", test_result="Not Tested", bts_id="", comment=""
    )
    
    # 다른 BVT 번호의 결과
    result = PlayTestResult(
        play_test_name="test_play",
        bvt_no=999,  # 다른 번호
        status=TestStatus.PASS,
        executed_actions=5,
        failed_actions=0,
        screenshots=[],
        error_message=None,
        execution_time=1.0
    )
    
    updated_cases = updater.update([bvt_case], [result])
    
    # 원본 상태 유지
    assert updated_cases[0].test_result == "Not Tested"
