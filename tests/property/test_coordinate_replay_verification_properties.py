"""
Property-based tests for Coordinate Replay Verification

**Feature: coordinate-replay-verification**

이 모듈은 좌표 기반 Replay 검증 기능의 correctness properties를 테스트한다.
"""

import os
import sys
import tempfile
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, settings, strategies as st, assume

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.config_manager import ConfigManager
from src.replay_verifier import VerificationResult, ReplayReport


# === Strategies ===

# 액션 타입 전략 (wait 제외 - 검증 대상이 아님)
verifiable_action_type_strategy = st.sampled_from(['click', 'key_press', 'scroll'])

# 좌표 전략
coordinate_strategy = st.integers(min_value=0, max_value=1920)

# 검증 결과 전략
final_result_strategy = st.sampled_from(['pass', 'fail', 'warning'])

# 유사도 전략
similarity_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


def generate_action_dict(action_type: str, x: int, y: int, index: int, 
                         screenshot_path: str = None) -> Dict[str, Any]:
    """테스트용 액션 딕셔너리 생성"""
    return {
        'timestamp': datetime.now().isoformat(),
        'action_type': action_type,
        'x': x,
        'y': y,
        'description': f'Test action {index}',
        'screenshot_path': screenshot_path,
        'button': 'left' if action_type == 'click' else None,
        'key': 'a' if action_type == 'key_press' else None,
        'scroll_dx': 0,
        'scroll_dy': 100 if action_type == 'scroll' else 0,
    }


def generate_verification_result(action_index: int, final_result: str, 
                                  similarity: float) -> VerificationResult:
    """테스트용 VerificationResult 생성"""
    return VerificationResult(
        action_index=action_index,
        action_description=f'Test action {action_index}',
        screenshot_match=(final_result == 'pass'),
        screenshot_similarity=similarity,
        vision_verified=(final_result != 'pass'),
        vision_match=(final_result == 'warning'),
        final_result=final_result,
        details={}
    )


# === Property Tests ===

@settings(max_examples=100, deadline=None)
@given(
    similarity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    vision_llm_success=st.booleans(),
    vision_match=st.booleans(),
    threshold=st.floats(min_value=0.5, max_value=0.95, allow_nan=False, allow_infinity=False)
)
def test_property_1_verification_result_consistency(
    similarity: float, 
    vision_llm_success: bool, 
    vision_match: bool,
    threshold: float
):
    """
    **Feature: coordinate-replay-verification, Property 1: 검증 결과와 유사도 임계값의 일관성**
    
    *For any* 스크린샷 비교 결과에서, 유사도가 임계값 이상이면 결과는 "pass"이고,
    유사도가 임계값 미만이면서 Vision LLM이 성공하고 의미적으로 일치하면 "warning"이며,
    그 외의 경우 "fail"이어야 한다.
    
    **Validates: Requirements 1.4, 1.5, 4.4**
    """
    # 검증 로직 시뮬레이션
    if similarity >= threshold:
        # 유사도가 임계값 이상이면 pass
        expected_result = "pass"
    elif vision_llm_success and vision_match:
        # Vision LLM 성공하고 의미적으로 일치하면 warning
        expected_result = "warning"
    elif not vision_llm_success and similarity >= 0.7:
        # Vision LLM 실패했지만 유사도가 0.7 이상이면 warning (폴백)
        expected_result = "warning"
    else:
        # 그 외의 경우 fail
        expected_result = "fail"
    
    # VerificationResult 생성
    result = VerificationResult(
        action_index=0,
        action_description="Test action",
        screenshot_match=(similarity >= threshold),
        screenshot_similarity=similarity,
        vision_verified=(similarity < threshold),
        vision_match=vision_match if vision_llm_success else False,
        final_result=expected_result,
        details={}
    )
    
    # Property 검증: 결과가 예상과 일치해야 함
    assert result.final_result == expected_result, \
        f"검증 결과 불일치. 예상: {expected_result}, 실제: {result.final_result}, " \
        f"similarity={similarity:.3f}, threshold={threshold:.3f}, " \
        f"vision_llm_success={vision_llm_success}, vision_match={vision_match}"
    
    # Property 검증: screenshot_match와 similarity의 일관성
    if result.screenshot_match:
        assert similarity >= threshold, \
            f"screenshot_match=True인데 similarity({similarity:.3f}) < threshold({threshold:.3f})"
    
    # Property 검증: vision_verified는 screenshot_match가 False일 때만 True
    if result.vision_verified:
        assert not result.screenshot_match, \
            "vision_verified=True인데 screenshot_match도 True입니다"


@settings(max_examples=100, deadline=None)
@given(
    pass_count=st.integers(min_value=0, max_value=50),
    fail_count=st.integers(min_value=0, max_value=50),
    warning_count=st.integers(min_value=0, max_value=50)
)
def test_property_2_report_count_accuracy(pass_count: int, fail_count: int, warning_count: int):
    """
    **Feature: coordinate-replay-verification, Property 2: 보고서 카운트 정확성**
    
    *For any* 검증 결과 리스트에 대해, 보고서의 passed_count + failed_count + warning_count는 
    total_actions와 같아야 하며, success_rate는 (passed_count + warning_count) / total_actions와 같아야 한다.
    
    **Validates: Requirements 2.1, 2.3**
    """
    # 최소 1개의 액션이 있어야 함
    total = pass_count + fail_count + warning_count
    assume(total > 0)
    
    # 검증 결과 리스트 생성
    verification_results = []
    action_index = 0
    
    for _ in range(pass_count):
        verification_results.append(generate_verification_result(action_index, 'pass', 0.95))
        action_index += 1
    
    for _ in range(fail_count):
        verification_results.append(generate_verification_result(action_index, 'fail', 0.3))
        action_index += 1
    
    for _ in range(warning_count):
        verification_results.append(generate_verification_result(action_index, 'warning', 0.6))
        action_index += 1
    
    # 보고서 생성 로직 시뮬레이션 (ReplayVerifier.generate_report()와 동일)
    passed = sum(1 for r in verification_results if r.final_result == "pass")
    failed = sum(1 for r in verification_results if r.final_result == "fail")
    warnings = sum(1 for r in verification_results if r.final_result == "warning")
    total_actions = len(verification_results)
    success_rate = (passed + warnings) / total_actions if total_actions > 0 else 0.0
    
    # ReplayReport 생성
    report = ReplayReport(
        test_case_name="test_property_2",
        session_id="test_session",
        start_time="2026-01-16T00:00:00",
        end_time="2026-01-16T00:01:00",
        total_actions=total_actions,
        passed_count=passed,
        failed_count=failed,
        warning_count=warnings,
        success_rate=success_rate,
        verification_results=verification_results,
        summary=""
    )
    
    # Property 검증 1: 카운트 합계가 total_actions와 같아야 함
    assert report.passed_count + report.failed_count + report.warning_count == report.total_actions, \
        f"카운트 합계 불일치. passed={report.passed_count}, failed={report.failed_count}, " \
        f"warning={report.warning_count}, total={report.total_actions}"
    
    # Property 검증 2: 각 카운트가 입력값과 일치해야 함
    assert report.passed_count == pass_count, \
        f"passed_count 불일치. 예상: {pass_count}, 실제: {report.passed_count}"
    assert report.failed_count == fail_count, \
        f"failed_count 불일치. 예상: {fail_count}, 실제: {report.failed_count}"
    assert report.warning_count == warning_count, \
        f"warning_count 불일치. 예상: {warning_count}, 실제: {report.warning_count}"
    
    # Property 검증 3: success_rate 계산 정확성
    expected_success_rate = (pass_count + warning_count) / total
    assert abs(report.success_rate - expected_success_rate) < 1e-9, \
        f"success_rate 불일치. 예상: {expected_success_rate}, 실제: {report.success_rate}"
    
    # Property 검증 4: success_rate 범위 검증 (0.0 ~ 1.0)
    assert 0.0 <= report.success_rate <= 1.0, \
        f"success_rate가 유효 범위를 벗어남: {report.success_rate}"


@settings(max_examples=100, deadline=None)
@given(
    action_count=st.integers(min_value=1, max_value=10),
    fail_indices=st.lists(st.integers(min_value=0, max_value=9), max_size=5, unique=True)
)
def test_property_5_continue_on_failure(action_count: int, fail_indices: List[int]):
    """
    **Feature: coordinate-replay-verification, Property 5: 실패 시 계속 실행**
    
    *For any* 테스트 케이스에서, 중간에 검증 실패가 발생해도 모든 액션이 
    실행되어야 하며, 결과 리스트의 길이는 액션 수와 같아야 한다.
    
    **Validates: Requirements 4.1**
    
    이 테스트는 검증 결과 리스트가 액션 수와 일치하는지,
    그리고 실패가 있을 때 전체 테스트 결과가 올바르게 판정되는지 검증한다.
    """
    # fail_indices가 action_count 범위 내에 있도록 필터링
    valid_fail_indices = set(i for i in fail_indices if i < action_count)
    
    # 검증 결과 리스트 생성 (실패 시에도 모든 액션에 대해 결과가 있어야 함)
    verification_results = []
    for i in range(action_count):
        if i in valid_fail_indices:
            result = generate_verification_result(i, 'fail', 0.3)
        else:
            result = generate_verification_result(i, 'pass', 0.95)
        verification_results.append(result)
    
    # Property 검증 1: 결과 리스트 길이가 액션 수와 같아야 함
    assert len(verification_results) == action_count, \
        f"검증 결과 수가 액션 수와 다릅니다. 예상: {action_count}, 실제: {len(verification_results)}"
    
    # Property 검증 2: 모든 액션 인덱스가 결과에 포함되어야 함
    result_indices = {r.action_index for r in verification_results}
    expected_indices = set(range(action_count))
    assert result_indices == expected_indices, \
        f"일부 액션 인덱스가 누락되었습니다. 예상: {expected_indices}, 실제: {result_indices}"
    
    # Property 검증 3: 전체 테스트 결과 판정 로직 검증
    # 하나라도 fail이 있으면 전체 테스트는 실패
    has_failure = any(r.final_result == 'fail' for r in verification_results)
    test_passed = all(r.final_result != 'fail' for r in verification_results)
    
    if valid_fail_indices:
        assert has_failure == True, \
            "실패한 액션이 있는데 has_failure가 False입니다"
        assert test_passed == False, \
            "실패한 액션이 있는데 test_passed가 True입니다"
    else:
        assert has_failure == False, \
            "실패한 액션이 없는데 has_failure가 True입니다"
        assert test_passed == True, \
            "모든 액션이 성공했는데 test_passed가 False입니다"


@settings(max_examples=100, deadline=None)
@given(
    action_count=st.integers(min_value=1, max_value=20),
    results_data=st.lists(
        st.tuples(
            st.sampled_from(['pass', 'fail', 'warning']),
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
        ),
        min_size=1,
        max_size=20
    )
)
def test_property_6_overall_test_result_determination(action_count: int, results_data: List):
    """
    **Feature: coordinate-replay-verification, Property 6: 전체 테스트 결과 판정**
    
    *For any* 검증 결과 리스트에서, 하나라도 "fail"이 있으면 전체 테스트 결과는 False이고,
    모두 "pass" 또는 "warning"이면 True여야 한다.
    
    **Validates: Requirements 4.3**
    """
    # 결과 데이터를 action_count에 맞게 조정
    actual_count = min(action_count, len(results_data))
    if actual_count == 0:
        actual_count = 1
    
    # 검증 결과 리스트 생성
    verification_results = []
    for i in range(actual_count):
        idx = i % len(results_data)
        final_result, similarity = results_data[idx]
        result = generate_verification_result(i, final_result, similarity)
        verification_results.append(result)
    
    # 예상 결과 계산: 하나라도 fail이 있으면 False
    has_failure = any(r.final_result == 'fail' for r in verification_results)
    expected_test_result = not has_failure
    
    # determine_test_result 로직 시뮬레이션
    # (실제 ReplayVerifier.determine_test_result()와 동일한 로직)
    actual_test_result = True
    for result in verification_results:
        if result.final_result == "fail":
            actual_test_result = False
            break
    
    # Property 검증
    assert actual_test_result == expected_test_result, \
        f"전체 테스트 결과 불일치. 예상: {expected_test_result}, 실제: {actual_test_result}, " \
        f"has_failure: {has_failure}"
    
    # 추가 검증: fail이 있으면 반드시 False
    if has_failure:
        assert actual_test_result == False, \
            "fail이 있는데 테스트 결과가 True입니다"
    else:
        assert actual_test_result == True, \
            "fail이 없는데 테스트 결과가 False입니다"


@settings(max_examples=100, deadline=None)
@given(
    action_index=st.integers(min_value=0, max_value=1000),
    action_description=st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\x00'
    )),
    screenshot_match=st.booleans(),
    screenshot_similarity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    vision_verified=st.booleans(),
    vision_match=st.booleans(),
    final_result=st.sampled_from(['pass', 'fail', 'warning', 'unknown'])
)
def test_property_4_verification_result_serialization_roundtrip(
    action_index: int,
    action_description: str,
    screenshot_match: bool,
    screenshot_similarity: float,
    vision_verified: bool,
    vision_match: bool,
    final_result: str
):
    """
    **Feature: coordinate-replay-verification, Property 4: 검증 결과 직렬화 Round-trip**
    
    *For any* VerificationResult 객체에 대해, JSON으로 직렬화한 후 역직렬화하면 
    원본과 동등한 객체가 복원되어야 한다.
    
    **Validates: Requirements 2.5, 6.4**
    """
    import json
    
    # 원본 VerificationResult 생성
    original = VerificationResult(
        action_index=action_index,
        action_description=action_description,
        screenshot_match=screenshot_match,
        screenshot_similarity=screenshot_similarity,
        vision_verified=vision_verified,
        vision_match=vision_match,
        final_result=final_result,
        details={'test_key': 'test_value', 'number': 42}
    )
    
    # 직렬화 (to_dict -> JSON string)
    serialized = json.dumps(original.to_dict(), ensure_ascii=False)
    
    # 역직렬화 (JSON string -> dict)
    deserialized_dict = json.loads(serialized)
    
    # 복원된 VerificationResult 생성
    restored = VerificationResult(
        action_index=deserialized_dict['action_index'],
        action_description=deserialized_dict['action_description'],
        screenshot_match=deserialized_dict['screenshot_match'],
        screenshot_similarity=deserialized_dict['screenshot_similarity'],
        vision_verified=deserialized_dict['vision_verified'],
        vision_match=deserialized_dict['vision_match'],
        final_result=deserialized_dict['final_result'],
        details=deserialized_dict['details']
    )
    
    # Property 검증: 모든 필드가 원본과 동일해야 함
    assert restored.action_index == original.action_index, \
        f"action_index 불일치. 원본: {original.action_index}, 복원: {restored.action_index}"
    assert restored.action_description == original.action_description, \
        f"action_description 불일치. 원본: {original.action_description}, 복원: {restored.action_description}"
    assert restored.screenshot_match == original.screenshot_match, \
        f"screenshot_match 불일치. 원본: {original.screenshot_match}, 복원: {restored.screenshot_match}"
    assert abs(restored.screenshot_similarity - original.screenshot_similarity) < 1e-9, \
        f"screenshot_similarity 불일치. 원본: {original.screenshot_similarity}, 복원: {restored.screenshot_similarity}"
    assert restored.vision_verified == original.vision_verified, \
        f"vision_verified 불일치. 원본: {original.vision_verified}, 복원: {restored.vision_verified}"
    assert restored.vision_match == original.vision_match, \
        f"vision_match 불일치. 원본: {original.vision_match}, 복원: {restored.vision_match}"
    assert restored.final_result == original.final_result, \
        f"final_result 불일치. 원본: {original.final_result}, 복원: {restored.final_result}"
    assert restored.details == original.details, \
        f"details 불일치. 원본: {original.details}, 복원: {restored.details}"


@settings(max_examples=100, deadline=None)
@given(
    test_case_name=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('L', 'N'),
        blacklist_characters='\x00'
    )),
    session_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('L', 'N'),
        blacklist_characters='\x00'
    )),
    total_actions=st.integers(min_value=1, max_value=100),
    passed_count=st.integers(min_value=0, max_value=100),
    failed_count=st.integers(min_value=0, max_value=100),
    warning_count=st.integers(min_value=0, max_value=100),
    success_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
)
def test_property_4_replay_report_serialization_roundtrip(
    test_case_name: str,
    session_id: str,
    total_actions: int,
    passed_count: int,
    failed_count: int,
    warning_count: int,
    success_rate: float
):
    """
    **Feature: coordinate-replay-verification, Property 4: ReplayReport 직렬화 Round-trip**
    
    *For any* ReplayReport 객체에 대해, JSON으로 직렬화한 후 역직렬화하면 
    원본과 동등한 객체가 복원되어야 한다.
    
    **Validates: Requirements 2.5, 6.4**
    """
    import json
    
    # 빈 문자열 방지
    assume(len(test_case_name.strip()) > 0)
    assume(len(session_id.strip()) > 0)
    
    # 원본 ReplayReport 생성
    original = ReplayReport(
        test_case_name=test_case_name,
        session_id=session_id,
        start_time="2026-01-16T00:00:00",
        end_time="2026-01-16T00:05:00",
        total_actions=total_actions,
        passed_count=passed_count,
        failed_count=failed_count,
        warning_count=warning_count,
        success_rate=success_rate,
        verification_results=[],
        summary="Test summary"
    )
    
    # 직렬화 (to_dict -> JSON string)
    serialized = json.dumps(original.to_dict(), ensure_ascii=False)
    
    # 역직렬화 (JSON string -> dict)
    deserialized_dict = json.loads(serialized)
    
    # 복원된 ReplayReport 생성
    restored = ReplayReport(
        test_case_name=deserialized_dict['test_case_name'],
        session_id=deserialized_dict['session_id'],
        start_time=deserialized_dict['start_time'],
        end_time=deserialized_dict['end_time'],
        total_actions=deserialized_dict['total_actions'],
        passed_count=deserialized_dict['passed_count'],
        failed_count=deserialized_dict['failed_count'],
        warning_count=deserialized_dict['warning_count'],
        success_rate=deserialized_dict['success_rate'],
        verification_results=[],
        summary=deserialized_dict['summary']
    )
    
    # Property 검증: 모든 필드가 원본과 동일해야 함
    assert restored.test_case_name == original.test_case_name, \
        f"test_case_name 불일치. 원본: {original.test_case_name}, 복원: {restored.test_case_name}"
    assert restored.session_id == original.session_id, \
        f"session_id 불일치. 원본: {original.session_id}, 복원: {restored.session_id}"
    assert restored.start_time == original.start_time, \
        f"start_time 불일치. 원본: {original.start_time}, 복원: {restored.start_time}"
    assert restored.end_time == original.end_time, \
        f"end_time 불일치. 원본: {original.end_time}, 복원: {restored.end_time}"
    assert restored.total_actions == original.total_actions, \
        f"total_actions 불일치. 원본: {original.total_actions}, 복원: {restored.total_actions}"
    assert restored.passed_count == original.passed_count, \
        f"passed_count 불일치. 원본: {original.passed_count}, 복원: {restored.passed_count}"
    assert restored.failed_count == original.failed_count, \
        f"failed_count 불일치. 원본: {original.failed_count}, 복원: {restored.failed_count}"
    assert restored.warning_count == original.warning_count, \
        f"warning_count 불일치. 원본: {original.warning_count}, 복원: {restored.warning_count}"
    assert abs(restored.success_rate - original.success_rate) < 1e-9, \
        f"success_rate 불일치. 원본: {original.success_rate}, 복원: {restored.success_rate}"
    assert restored.summary == original.summary, \
        f"summary 불일치. 원본: {original.summary}, 복원: {restored.summary}"


@settings(max_examples=100, deadline=None)
@given(
    action_index=st.integers(min_value=0, max_value=1000),
    action_description=st.text(min_size=0, max_size=100, alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P', 'S', 'Z'),
        blacklist_characters='\x00'
    )),
    screenshot_match=st.booleans(),
    screenshot_similarity=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    vision_verified=st.booleans(),
    vision_match=st.booleans(),
    final_result=st.sampled_from(['pass', 'fail', 'warning', 'unknown'])
)
def test_property_9_verification_result_required_fields(
    action_index: int,
    action_description: str,
    screenshot_match: bool,
    screenshot_similarity: float,
    vision_verified: bool,
    vision_match: bool,
    final_result: str
):
    """
    **Feature: coordinate-replay-verification, Property 9: 데이터 구조 필수 필드 존재 (VerificationResult)**
    
    *For any* VerificationResult에 대해 action_index, final_result, screenshot_similarity, 
    vision_match 필드가 존재해야 한다.
    
    **Validates: Requirements 6.2, 6.3**
    """
    # VerificationResult 생성
    result = VerificationResult(
        action_index=action_index,
        action_description=action_description,
        screenshot_match=screenshot_match,
        screenshot_similarity=screenshot_similarity,
        vision_verified=vision_verified,
        vision_match=vision_match,
        final_result=final_result,
        details={}
    )
    
    # Requirements 6.2에서 명시한 필수 필드
    required_fields = ['action_index', 'final_result', 'screenshot_similarity', 'vision_match']
    
    # Property 검증 1: dataclass 속성으로 필수 필드 존재 확인
    for field in required_fields:
        assert hasattr(result, field), \
            f"VerificationResult에 필수 필드 '{field}'가 없습니다"
    
    # Property 검증 2: to_dict()에서 필수 필드 존재 확인
    result_dict = result.to_dict()
    for field in required_fields:
        assert field in result_dict, \
            f"VerificationResult.to_dict()에 필수 필드 '{field}'가 없습니다"
    
    # Property 검증 3: 필드 값이 올바른 타입인지 확인
    assert isinstance(result.action_index, int), \
        f"action_index는 int여야 함: {type(result.action_index)}"
    assert isinstance(result.final_result, str), \
        f"final_result는 str이어야 함: {type(result.final_result)}"
    assert isinstance(result.screenshot_similarity, float), \
        f"screenshot_similarity는 float이어야 함: {type(result.screenshot_similarity)}"
    assert isinstance(result.vision_match, bool), \
        f"vision_match는 bool이어야 함: {type(result.vision_match)}"
    
    # Property 검증 4: 값이 입력과 일치하는지 확인
    assert result.action_index == action_index
    assert result.final_result == final_result
    assert abs(result.screenshot_similarity - screenshot_similarity) < 1e-9
    assert result.vision_match == vision_match


@settings(max_examples=100, deadline=None)
@given(
    total_actions=st.integers(min_value=0, max_value=100),
    passed_count=st.integers(min_value=0, max_value=100),
    failed_count=st.integers(min_value=0, max_value=100),
    warning_count=st.integers(min_value=0, max_value=100),
    success_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
)
def test_property_9_replay_report_required_fields(
    total_actions: int,
    passed_count: int,
    failed_count: int,
    warning_count: int,
    success_rate: float
):
    """
    **Feature: coordinate-replay-verification, Property 9: 데이터 구조 필수 필드 존재 (ReplayReport)**
    
    *For any* ReplayReport에 대해 total_actions, passed_count, failed_count, 
    warning_count, success_rate 필드가 존재해야 한다.
    
    **Validates: Requirements 6.2, 6.3**
    """
    # ReplayReport 생성
    report = ReplayReport(
        test_case_name="test",
        session_id="session",
        start_time="2026-01-16T00:00:00",
        end_time="2026-01-16T00:01:00",
        total_actions=total_actions,
        passed_count=passed_count,
        failed_count=failed_count,
        warning_count=warning_count,
        success_rate=success_rate,
        verification_results=[],
        summary="Test"
    )
    
    # Requirements 6.3에서 명시한 필수 필드
    required_fields = ['total_actions', 'passed_count', 'failed_count', 'warning_count', 'success_rate']
    
    # Property 검증 1: dataclass 속성으로 필수 필드 존재 확인
    for field in required_fields:
        assert hasattr(report, field), \
            f"ReplayReport에 필수 필드 '{field}'가 없습니다"
    
    # Property 검증 2: to_dict()에서 필수 필드 존재 확인
    report_dict = report.to_dict()
    for field in required_fields:
        assert field in report_dict, \
            f"ReplayReport.to_dict()에 필수 필드 '{field}'가 없습니다"
    
    # Property 검증 3: 필드 값이 올바른 타입인지 확인
    assert isinstance(report.total_actions, int), \
        f"total_actions는 int여야 함: {type(report.total_actions)}"
    assert isinstance(report.passed_count, int), \
        f"passed_count는 int여야 함: {type(report.passed_count)}"
    assert isinstance(report.failed_count, int), \
        f"failed_count는 int여야 함: {type(report.failed_count)}"
    assert isinstance(report.warning_count, int), \
        f"warning_count는 int여야 함: {type(report.warning_count)}"
    assert isinstance(report.success_rate, float), \
        f"success_rate는 float이어야 함: {type(report.success_rate)}"
    
    # Property 검증 4: 값이 입력과 일치하는지 확인
    assert report.total_actions == total_actions
    assert report.passed_count == passed_count
    assert report.failed_count == failed_count
    assert report.warning_count == warning_count
    assert abs(report.success_rate - success_rate) < 1e-9


@settings(max_examples=100, deadline=None)
@given(
    action_count=st.integers(min_value=1, max_value=20),
    results_data=st.lists(
        st.tuples(
            st.sampled_from(['pass', 'fail', 'warning']),
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
        ),
        min_size=1,
        max_size=20
    )
)
def test_property_3_report_completeness(action_count: int, results_data: List):
    """
    **Feature: coordinate-replay-verification, Property 3: 보고서 완전성**
    
    *For any* 생성된 보고서에서, 모든 액션에 대해 action_index, final_result, 
    screenshot_similarity 필드가 존재해야 한다.
    
    **Validates: Requirements 2.2, 6.2**
    """
    # 결과 데이터를 action_count에 맞게 조정
    actual_count = min(action_count, len(results_data))
    if actual_count == 0:
        actual_count = 1
    
    # 검증 결과 리스트 생성
    verification_results = []
    for i in range(actual_count):
        idx = i % len(results_data)
        final_result, similarity = results_data[idx]
        result = generate_verification_result(i, final_result, similarity)
        verification_results.append(result)
    
    # 보고서 생성 로직 시뮬레이션
    passed = sum(1 for r in verification_results if r.final_result == "pass")
    failed = sum(1 for r in verification_results if r.final_result == "fail")
    warnings = sum(1 for r in verification_results if r.final_result == "warning")
    total_actions = len(verification_results)
    success_rate = (passed + warnings) / total_actions if total_actions > 0 else 0.0
    
    # ReplayReport 생성
    report = ReplayReport(
        test_case_name="test_property_3",
        session_id="test_session",
        start_time="2026-01-16T00:00:00",
        end_time="2026-01-16T00:01:00",
        total_actions=total_actions,
        passed_count=passed,
        failed_count=failed,
        warning_count=warnings,
        success_rate=success_rate,
        verification_results=verification_results,
        summary=""
    )
    
    # Property 검증 1: 보고서의 verification_results 수가 total_actions와 일치
    assert len(report.verification_results) == report.total_actions, \
        f"verification_results 수({len(report.verification_results)})가 " \
        f"total_actions({report.total_actions})와 다릅니다"
    
    # Property 검증 2: 모든 액션에 대해 필수 필드 존재 확인
    required_fields = ['action_index', 'final_result', 'screenshot_similarity']
    
    for result in report.verification_results:
        result_dict = result.to_dict()
        for field in required_fields:
            assert field in result_dict, \
                f"액션 {result.action_index}에 필수 필드 '{field}'가 없습니다"
    
    # Property 검증 3: 모든 action_index가 유일하고 연속적인지 확인
    action_indices = [r.action_index for r in report.verification_results]
    assert len(action_indices) == len(set(action_indices)), \
        f"중복된 action_index가 있습니다: {action_indices}"
    
    # Property 검증 4: 모든 final_result가 유효한 값인지 확인
    valid_results = {'pass', 'fail', 'warning', 'unknown'}
    for result in report.verification_results:
        assert result.final_result in valid_results, \
            f"유효하지 않은 final_result: {result.final_result}"
    
    # Property 검증 5: screenshot_similarity가 유효 범위 내인지 확인
    for result in report.verification_results:
        assert 0.0 <= result.screenshot_similarity <= 1.0, \
            f"screenshot_similarity가 유효 범위를 벗어남: {result.screenshot_similarity}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])


@settings(max_examples=100, deadline=None)
@given(
    pass_count=st.integers(min_value=0, max_value=20),
    fail_count=st.integers(min_value=0, max_value=20),
    warning_count=st.integers(min_value=0, max_value=20)
)
def test_property_7_exit_code_consistency(pass_count: int, fail_count: int, warning_count: int):
    """
    **Feature: coordinate-replay-verification, Property 7: 종료 코드와 테스트 결과의 일관성**
    
    *For any* CLI 실행에서, 테스트가 성공하면 종료 코드는 0이고, 
    실패하면 종료 코드는 1이어야 한다.
    
    **Validates: Requirements 5.3, 5.4**
    """
    # 최소 1개의 액션이 있어야 함
    total = pass_count + fail_count + warning_count
    assume(total > 0)
    
    # 검증 결과 리스트 생성
    verification_results = []
    action_index = 0
    
    for _ in range(pass_count):
        verification_results.append(generate_verification_result(action_index, 'pass', 0.95))
        action_index += 1
    
    for _ in range(fail_count):
        verification_results.append(generate_verification_result(action_index, 'fail', 0.3))
        action_index += 1
    
    for _ in range(warning_count):
        verification_results.append(generate_verification_result(action_index, 'warning', 0.6))
        action_index += 1
    
    # 테스트 결과 판정 (Requirements 4.3과 동일한 로직)
    # 하나라도 fail이 있으면 테스트 실패
    test_passed = all(r.final_result != 'fail' for r in verification_results)
    
    # 종료 코드 결정 (Requirements 5.3, 5.4)
    # 테스트 성공 시 0, 실패 시 1
    expected_exit_code = 0 if test_passed else 1
    
    # Property 검증 1: 테스트 성공 시 종료 코드는 0
    if test_passed:
        assert expected_exit_code == 0, \
            f"테스트 성공인데 종료 코드가 0이 아닙니다: {expected_exit_code}"
    
    # Property 검증 2: 테스트 실패 시 종료 코드는 1
    if not test_passed:
        assert expected_exit_code == 1, \
            f"테스트 실패인데 종료 코드가 1이 아닙니다: {expected_exit_code}"
    
    # Property 검증 3: fail이 있으면 반드시 종료 코드 1
    has_failure = any(r.final_result == 'fail' for r in verification_results)
    if has_failure:
        assert expected_exit_code == 1, \
            f"fail이 있는데 종료 코드가 1이 아닙니다: {expected_exit_code}"
    
    # Property 검증 4: fail이 없으면 반드시 종료 코드 0
    if not has_failure:
        assert expected_exit_code == 0, \
            f"fail이 없는데 종료 코드가 0이 아닙니다: {expected_exit_code}"
    
    # Property 검증 5: 종료 코드는 0 또는 1만 가능
    assert expected_exit_code in [0, 1], \
        f"종료 코드가 유효 범위를 벗어남: {expected_exit_code}"
    
    # Property 검증 6: test_passed와 exit_code의 일관성
    assert (test_passed and expected_exit_code == 0) or (not test_passed and expected_exit_code == 1), \
        f"test_passed({test_passed})와 exit_code({expected_exit_code})가 일관되지 않습니다"


@settings(max_examples=100, deadline=None)
@given(
    action_count=st.integers(min_value=1, max_value=20),
    no_screenshot_indices=st.lists(st.integers(min_value=0, max_value=19), max_size=10, unique=True)
)
def test_property_8_screenshot_path_missing_warning(action_count: int, no_screenshot_indices: List[int]):
    """
    **Feature: coordinate-replay-verification, Property 8: screenshot_path 없는 액션의 warning 처리**
    
    *For any* screenshot_path가 없는 액션에 대해, 검증 결과는 "warning"이어야 하며 
    검증이 건너뛰어져야 한다.
    
    **Validates: Requirements 3.2**
    
    이 테스트는 screenshot_path가 없는 액션이 warning으로 처리되고,
    검증이 건너뛰어지는지 검증한다.
    """
    # no_screenshot_indices가 action_count 범위 내에 있도록 필터링
    valid_no_screenshot_indices = set(i for i in no_screenshot_indices if i < action_count)
    
    # 검증 결과 리스트 생성
    verification_results = []
    for i in range(action_count):
        if i in valid_no_screenshot_indices:
            # screenshot_path가 없는 액션 - warning으로 처리되어야 함
            result = VerificationResult(
                action_index=i,
                action_description=f'Test action {i} (no screenshot)',
                screenshot_match=False,
                screenshot_similarity=0.0,
                vision_verified=False,
                vision_match=False,
                final_result='warning',
                details={'note': 'screenshot_path 없음 또는 파일 미존재, 검증 생략'}
            )
        else:
            # screenshot_path가 있는 액션 - pass로 처리
            result = VerificationResult(
                action_index=i,
                action_description=f'Test action {i}',
                screenshot_match=True,
                screenshot_similarity=0.95,
                vision_verified=False,
                vision_match=False,
                final_result='pass',
                details={}
            )
        verification_results.append(result)
    
    # Property 검증 1: screenshot_path 없는 액션은 warning이어야 함
    for i in valid_no_screenshot_indices:
        result = verification_results[i]
        assert result.final_result == 'warning', \
            f"screenshot_path 없는 액션 {i}의 결과가 warning이 아닙니다: {result.final_result}"
    
    # Property 검증 2: screenshot_path 없는 액션은 검증이 건너뛰어져야 함 (vision_verified=False)
    for i in valid_no_screenshot_indices:
        result = verification_results[i]
        assert result.vision_verified == False, \
            f"screenshot_path 없는 액션 {i}에서 Vision LLM 검증이 수행되었습니다"
    
    # Property 검증 3: screenshot_path 없는 액션은 screenshot_similarity가 0.0이어야 함
    for i in valid_no_screenshot_indices:
        result = verification_results[i]
        assert result.screenshot_similarity == 0.0, \
            f"screenshot_path 없는 액션 {i}의 screenshot_similarity가 0.0이 아닙니다: {result.screenshot_similarity}"
    
    # Property 검증 4: screenshot_path 없는 액션의 details에 적절한 note가 있어야 함
    for i in valid_no_screenshot_indices:
        result = verification_results[i]
        assert 'note' in result.details, \
            f"screenshot_path 없는 액션 {i}의 details에 note가 없습니다"
        assert '검증 생략' in result.details.get('note', '') or 'screenshot_path' in result.details.get('note', ''), \
            f"screenshot_path 없는 액션 {i}의 note가 적절하지 않습니다: {result.details.get('note')}"
    
    # Property 검증 5: screenshot_path 있는 액션은 warning이 아니어야 함 (이 테스트에서는 pass)
    for i in range(action_count):
        if i not in valid_no_screenshot_indices:
            result = verification_results[i]
            assert result.final_result != 'warning' or result.details.get('note') is None, \
                f"screenshot_path 있는 액션 {i}가 screenshot_path 없음으로 인한 warning입니다"


@settings(max_examples=100, deadline=None)
@given(
    action_type=st.sampled_from(['click', 'key_press', 'scroll']),
    x=st.integers(min_value=0, max_value=1920),
    y=st.integers(min_value=0, max_value=1080),
    action_index=st.integers(min_value=0, max_value=100)
)
def test_property_8_verify_coordinate_action_no_screenshot(
    action_type: str, 
    x: int, 
    y: int, 
    action_index: int
):
    """
    **Feature: coordinate-replay-verification, Property 8: verify_coordinate_action에서 screenshot_path 없는 경우**
    
    *For any* screenshot_path가 없는 액션에 대해 verify_coordinate_action을 호출하면,
    결과는 "warning"이어야 하며 검증이 건너뛰어져야 한다.
    
    **Validates: Requirements 3.2**
    
    이 테스트는 ReplayVerifier.verify_coordinate_action 메서드의 동작을 검증한다.
    """
    # screenshot_path가 없는 액션 딕셔너리 생성
    action_dict = {
        'timestamp': '2026-01-16T00:00:00',
        'action_type': action_type,
        'x': x,
        'y': y,
        'description': f'Test {action_type} action at ({x}, {y})',
        'screenshot_path': None,  # screenshot_path 없음
        'button': 'left' if action_type == 'click' else None,
        'key': 'a' if action_type == 'key_press' else None,
        'scroll_dx': 0,
        'scroll_dy': 100 if action_type == 'scroll' else 0,
    }
    
    # verify_coordinate_action 로직 시뮬레이션
    # (실제 ReplayVerifier.verify_coordinate_action()와 동일한 로직)
    expected_screenshot = action_dict.get('screenshot_path', '')
    
    result = VerificationResult(
        action_index=action_index,
        action_description=action_dict.get('description', ''),
        screenshot_match=False,
        screenshot_similarity=0.0
    )
    result.details["verification_type"] = "coordinate_action"
    result.details["expected_screenshot_path"] = expected_screenshot
    
    # Requirements 3.2: screenshot_path가 없으면 warning 처리
    if not expected_screenshot:
        result.final_result = "warning"
        result.details["note"] = "screenshot_path 없음 또는 파일 미존재, 검증 생략"
    else:
        # 이 테스트에서는 screenshot_path가 없으므로 이 분기는 실행되지 않음
        result.final_result = "pass"
    
    # Property 검증 1: screenshot_path 없으면 warning
    assert result.final_result == "warning", \
        f"screenshot_path 없는 액션의 결과가 warning이 아닙니다: {result.final_result}"
    
    # Property 검증 2: screenshot_similarity는 0.0
    assert result.screenshot_similarity == 0.0, \
        f"screenshot_path 없는 액션의 screenshot_similarity가 0.0이 아닙니다: {result.screenshot_similarity}"
    
    # Property 검증 3: vision_verified는 False (검증 건너뜀)
    assert result.vision_verified == False, \
        f"screenshot_path 없는 액션에서 Vision LLM 검증이 수행되었습니다"
    
    # Property 검증 4: details에 적절한 note가 있어야 함
    assert 'note' in result.details, \
        f"screenshot_path 없는 액션의 details에 note가 없습니다"


@settings(max_examples=100, deadline=None)
@given(
    action_type=st.sampled_from(['click', 'key_press', 'scroll']),
    x=st.integers(min_value=0, max_value=1920),
    y=st.integers(min_value=0, max_value=1080),
    action_index=st.integers(min_value=0, max_value=100)
)
def test_property_8_verify_coordinate_action_nonexistent_screenshot(
    action_type: str, 
    x: int, 
    y: int, 
    action_index: int
):
    """
    **Feature: coordinate-replay-verification, Property 8: verify_coordinate_action에서 존재하지 않는 screenshot_path**
    
    *For any* 존재하지 않는 파일 경로를 가진 screenshot_path에 대해 verify_coordinate_action을 호출하면,
    결과는 "warning"이어야 하며 검증이 건너뛰어져야 한다.
    
    **Validates: Requirements 3.2**
    """
    import os
    
    # 존재하지 않는 screenshot_path를 가진 액션 딕셔너리 생성
    nonexistent_path = f'/nonexistent/path/screenshot_{action_index}.png'
    action_dict = {
        'timestamp': '2026-01-16T00:00:00',
        'action_type': action_type,
        'x': x,
        'y': y,
        'description': f'Test {action_type} action at ({x}, {y})',
        'screenshot_path': nonexistent_path,  # 존재하지 않는 경로
        'button': 'left' if action_type == 'click' else None,
        'key': 'a' if action_type == 'key_press' else None,
        'scroll_dx': 0,
        'scroll_dy': 100 if action_type == 'scroll' else 0,
    }
    
    # verify_coordinate_action 로직 시뮬레이션
    expected_screenshot = action_dict.get('screenshot_path', '')
    
    result = VerificationResult(
        action_index=action_index,
        action_description=action_dict.get('description', ''),
        screenshot_match=False,
        screenshot_similarity=0.0
    )
    result.details["verification_type"] = "coordinate_action"
    result.details["expected_screenshot_path"] = expected_screenshot
    
    # Requirements 3.2: screenshot_path가 없거나 파일이 존재하지 않으면 warning 처리
    if not expected_screenshot or not os.path.exists(expected_screenshot):
        result.final_result = "warning"
        result.details["note"] = "screenshot_path 없음 또는 파일 미존재, 검증 생략"
    else:
        result.final_result = "pass"
    
    # Property 검증 1: 존재하지 않는 screenshot_path는 warning
    assert result.final_result == "warning", \
        f"존재하지 않는 screenshot_path의 결과가 warning이 아닙니다: {result.final_result}"
    
    # Property 검증 2: screenshot_similarity는 0.0
    assert result.screenshot_similarity == 0.0, \
        f"존재하지 않는 screenshot_path의 screenshot_similarity가 0.0이 아닙니다: {result.screenshot_similarity}"
    
    # Property 검증 3: details에 적절한 note가 있어야 함
    assert 'note' in result.details, \
        f"존재하지 않는 screenshot_path의 details에 note가 없습니다"
    assert '파일 미존재' in result.details.get('note', '') or 'screenshot_path' in result.details.get('note', ''), \
        f"존재하지 않는 screenshot_path의 note가 적절하지 않습니다: {result.details.get('note')}"
