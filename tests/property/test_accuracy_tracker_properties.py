# -*- coding: utf-8 -*-
"""
Property-based tests for AccuracyTracker

**Feature: game-qa-automation, Property 32: 정확도 통계 완전성**
**Feature: game-qa-automation, Property 33: 액션 실행 결과 기록**

Validates: Requirements 13.2, 13.6
"""

import os
import sys
import tempfile
import shutil
import random
from hypothesis import given, settings, strategies as st, assume

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.accuracy_tracker import (
    AccuracyTracker, 
    ActionExecutionResult, 
    AccuracyStatistics
)


# Strategies
coordinate_strategy = st.tuples(
    st.integers(min_value=0, max_value=1920),
    st.integers(min_value=0, max_value=1080)
)

method_strategy = st.sampled_from(['direct', 'semantic', 'manual'])

failure_reason_strategy = st.sampled_from([
    'element_not_found',
    'timeout',
    'coordinate_out_of_bounds',
    'screen_transition_failed',
    'unknown_error'
])

execution_time_strategy = st.floats(min_value=0.01, max_value=10.0)

action_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N')),
    min_size=1,
    max_size=20
).filter(lambda x: len(x.strip()) > 0)

test_case_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N')),
    min_size=1,
    max_size=30
).filter(lambda x: len(x.strip()) > 0 and x.isalnum())


def create_temp_data_dir():
    return tempfile.mkdtemp()


def cleanup_temp_dir(temp_dir):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


class TestStatisticsCompleteness:
    """Property 32: 정확도 통계 완전성 테스트"""
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_success=st.integers(min_value=0, max_value=50),
        num_failure=st.integers(min_value=0, max_value=50),
        num_direct=st.integers(min_value=0, max_value=25),
        num_semantic=st.integers(min_value=0, max_value=25)
    )
    def test_statistics_has_all_required_fields(self, num_success, num_failure, 
                                                 num_direct, num_semantic):
        total = num_success + num_failure
        assume(total > 0)
        
        num_direct = min(num_direct, num_success)
        num_semantic = min(num_semantic, num_success - num_direct)
        num_manual = num_success - num_direct - num_semantic
        
        temp_dir = create_temp_data_dir()
        
        try:
            tracker = AccuracyTracker("test_case", data_dir=temp_dir)
            
            for i in range(num_direct):
                tracker.record_success(
                    action_id=f"action_direct_{i}",
                    method='direct',
                    original_coords=(100 + i, 200 + i),
                    actual_coords=(100 + i, 200 + i),
                    execution_time=0.5
                )
            
            for i in range(num_semantic):
                tracker.record_success(
                    action_id=f"action_semantic_{i}",
                    method='semantic',
                    original_coords=(100 + i, 200 + i),
                    actual_coords=(150 + i, 250 + i),
                    execution_time=1.0
                )
            
            for i in range(num_manual):
                tracker.record_success(
                    action_id=f"action_manual_{i}",
                    method='manual',
                    original_coords=(100 + i, 200 + i),
                    actual_coords=(120 + i, 220 + i),
                    execution_time=2.0
                )
            
            for i in range(num_failure):
                tracker.record_failure(
                    action_id=f"action_fail_{i}",
                    reason='element_not_found',
                    original_coords=(100 + i, 200 + i),
                    execution_time=0.3
                )
            
            stats = tracker.calculate_statistics()
            
            assert hasattr(stats, 'total_actions')
            assert hasattr(stats, 'success_count')
            assert hasattr(stats, 'failure_count')
            assert hasattr(stats, 'success_rate')
            assert hasattr(stats, 'direct_match_count')
            assert hasattr(stats, 'semantic_match_count')
            assert hasattr(stats, 'avg_coordinate_change')
            assert hasattr(stats, 'failure_reasons')
            
            assert stats.total_actions == total
            assert stats.success_count == num_success
            assert stats.failure_count == num_failure
            
            expected_success_rate = num_success / total if total > 0 else 0.0
            assert abs(stats.success_rate - expected_success_rate) < 0.001
            
            assert stats.direct_match_count == num_direct
            assert stats.semantic_match_count == num_semantic
            
        finally:
            cleanup_temp_dir(temp_dir)
    
    @settings(max_examples=50, deadline=None)
    @given(num_actions=st.integers(min_value=1, max_value=30))
    def test_statistics_rates_bounded(self, num_actions):
        temp_dir = create_temp_data_dir()
        
        try:
            tracker = AccuracyTracker("test_case", data_dir=temp_dir)
            
            for i in range(num_actions):
                if random.random() > 0.3:
                    method = random.choice(['direct', 'semantic', 'manual'])
                    tracker.record_success(
                        action_id=f"action_{i}",
                        method=method,
                        original_coords=(100, 200),
                        actual_coords=(110, 210),
                        execution_time=0.5
                    )
                else:
                    tracker.record_failure(
                        action_id=f"action_{i}",
                        reason='element_not_found',
                        original_coords=(100, 200),
                        execution_time=0.3
                    )
            
            stats = tracker.calculate_statistics()
            
            assert 0.0 <= stats.success_rate <= 1.0
            assert 0.0 <= stats.direct_match_rate <= 1.0
            assert 0.0 <= stats.semantic_match_rate <= 1.0
            assert stats.avg_coordinate_change >= 0.0
            assert stats.avg_execution_time >= 0.0
            
        finally:
            cleanup_temp_dir(temp_dir)
    
    def test_empty_tracker_statistics(self):
        temp_dir = create_temp_data_dir()
        
        try:
            tracker = AccuracyTracker("test_case", data_dir=temp_dir)
            stats = tracker.calculate_statistics()
            
            assert stats.total_actions == 0
            assert stats.success_count == 0
            assert stats.failure_count == 0
            assert stats.success_rate == 0.0
            
        finally:
            cleanup_temp_dir(temp_dir)


class TestActionResultRecording:
    """Property 33: 액션 실행 결과 기록 테스트"""
    
    @settings(max_examples=100, deadline=None)
    @given(
        action_id=action_id_strategy,
        method=method_strategy,
        original_coords=coordinate_strategy,
        actual_coords=coordinate_strategy,
        execution_time=execution_time_strategy
    )
    def test_success_recording_completeness(self, action_id, method, original_coords, 
                                            actual_coords, execution_time):
        temp_dir = create_temp_data_dir()
        
        try:
            tracker = AccuracyTracker("test_case", data_dir=temp_dir)
            
            result = tracker.record_success(
                action_id=action_id,
                method=method,
                original_coords=original_coords,
                actual_coords=actual_coords,
                execution_time=execution_time
            )
            
            assert result.action_id is not None
            assert result.timestamp is not None
            assert result.success == True
            assert result.method == method
            assert result.original_coords == original_coords
            assert result.actual_coords == actual_coords
            assert abs(result.execution_time - execution_time) < 0.001
            
            expected_change = (
                actual_coords[0] - original_coords[0],
                actual_coords[1] - original_coords[1]
            )
            assert result.coordinate_change == expected_change
            
            results = tracker.get_results()
            assert len(results) == 1
            assert results[0] == result
            
        finally:
            cleanup_temp_dir(temp_dir)
    
    @settings(max_examples=100, deadline=None)
    @given(
        action_id=action_id_strategy,
        reason=failure_reason_strategy,
        original_coords=coordinate_strategy,
        execution_time=execution_time_strategy
    )
    def test_failure_recording_completeness(self, action_id, reason, 
                                            original_coords, execution_time):
        temp_dir = create_temp_data_dir()
        
        try:
            tracker = AccuracyTracker("test_case", data_dir=temp_dir)
            
            result = tracker.record_failure(
                action_id=action_id,
                reason=reason,
                original_coords=original_coords,
                execution_time=execution_time
            )
            
            assert result.success == False
            assert result.method == 'failed'
            assert result.failure_reason == reason
            assert result.original_coords == original_coords
            assert result.actual_coords is None
            assert result.coordinate_change is None
            
        finally:
            cleanup_temp_dir(temp_dir)
    
    @settings(max_examples=50, deadline=None)
    @given(num_results=st.integers(min_value=1, max_value=20))
    def test_multiple_results_ordering(self, num_results):
        temp_dir = create_temp_data_dir()
        
        try:
            tracker = AccuracyTracker("test_case", data_dir=temp_dir)
            
            for i in range(num_results):
                tracker.record_success(
                    action_id=f"action_{i:04d}",
                    method='direct',
                    original_coords=(100 + i, 200 + i),
                    actual_coords=(100 + i, 200 + i),
                    execution_time=0.5
                )
            
            results = tracker.get_results()
            assert len(results) == num_results
            
            for i, result in enumerate(results):
                assert result.action_id == f"action_{i:04d}"
            
        finally:
            cleanup_temp_dir(temp_dir)


class TestSessionRoundTrip:
    """세션 저장/로드 라운드트립 테스트"""
    
    @settings(max_examples=30, deadline=None)
    @given(
        test_case_name=test_case_name_strategy,
        num_results=st.integers(min_value=1, max_value=20)
    )
    def test_session_save_load_roundtrip(self, test_case_name, num_results):
        temp_dir = create_temp_data_dir()
        
        try:
            tracker1 = AccuracyTracker(test_case_name, data_dir=temp_dir)
            session_id = tracker1.get_session_id()
            
            for i in range(num_results):
                if i % 3 == 0:
                    tracker1.record_failure(
                        action_id=f"action_{i}",
                        reason='element_not_found',
                        original_coords=(100 + i, 200 + i),
                        execution_time=0.3
                    )
                else:
                    tracker1.record_success(
                        action_id=f"action_{i}",
                        method='direct' if i % 2 == 0 else 'semantic',
                        original_coords=(100 + i, 200 + i),
                        actual_coords=(110 + i, 210 + i),
                        execution_time=0.5
                    )
            
            saved_path = tracker1.save_session()
            assert os.path.exists(saved_path)
            
            tracker2 = AccuracyTracker(test_case_name, data_dir=temp_dir)
            load_success = tracker2.load_session(session_id)
            assert load_success
            
            results1 = tracker1.get_results()
            results2 = tracker2.get_results()
            
            assert len(results1) == len(results2)
            
            for r1, r2 in zip(results1, results2):
                assert r1.action_id == r2.action_id
                assert r1.success == r2.success
                assert r1.method == r2.method
                assert r1.original_coords == r2.original_coords
                assert r1.failure_reason == r2.failure_reason
            
        finally:
            cleanup_temp_dir(temp_dir)
    
    @settings(max_examples=20, deadline=None)
    @given(num_sessions=st.integers(min_value=1, max_value=5))
    def test_list_sessions(self, num_sessions):
        temp_dir = create_temp_data_dir()
        
        try:
            test_case_name = "test_case_list"
            
            import time
            for s in range(num_sessions):
                tracker = AccuracyTracker(test_case_name, data_dir=temp_dir)
                tracker.start_session()
                
                for i in range(3):
                    tracker.record_success(
                        action_id=f"action_{i}",
                        method='direct',
                        original_coords=(100, 200),
                        actual_coords=(100, 200),
                        execution_time=0.5
                    )
                
                tracker.save_session()
                # 세션 ID가 마이크로초 단위이므로 짧은 대기로 충분
                time.sleep(0.01)
            
            tracker = AccuracyTracker(test_case_name, data_dir=temp_dir)
            sessions = tracker.list_sessions()
            
            assert len(sessions) == num_sessions
            
            for session in sessions:
                assert 'session_id' in session
                assert 'timestamp' in session
                assert 'total_actions' in session
                assert 'success_rate' in session
            
        finally:
            cleanup_temp_dir(temp_dir)


class TestActionExecutionResult:
    """ActionExecutionResult 데이터 클래스 테스트"""
    
    @settings(max_examples=50, deadline=None)
    @given(
        action_id=action_id_strategy,
        method=method_strategy,
        original_coords=coordinate_strategy,
        actual_coords=coordinate_strategy,
        execution_time=execution_time_strategy
    )
    def test_to_dict_from_dict_roundtrip(self, action_id, method, original_coords,
                                          actual_coords, execution_time):
        from datetime import datetime
        
        result = ActionExecutionResult(
            action_id=action_id,
            timestamp=datetime.now().isoformat(),
            success=True,
            method=method,
            original_coords=original_coords,
            actual_coords=actual_coords,
            coordinate_change=(
                actual_coords[0] - original_coords[0],
                actual_coords[1] - original_coords[1]
            ),
            execution_time=execution_time,
            failure_reason="",
            screen_transition_matched=True
        )
        
        data = result.to_dict()
        restored = ActionExecutionResult.from_dict(data)
        
        assert restored.action_id == result.action_id
        assert restored.success == result.success
        assert restored.method == result.method
        assert restored.original_coords == result.original_coords
        assert restored.actual_coords == result.actual_coords
        assert restored.coordinate_change == result.coordinate_change
        assert abs(restored.execution_time - result.execution_time) < 0.001


class TestAccuracyStatistics:
    """AccuracyStatistics 데이터 클래스 테스트"""
    
    def test_to_dict_contains_all_fields(self):
        stats = AccuracyStatistics(
            total_actions=10,
            success_count=8,
            failure_count=2,
            success_rate=0.8,
            direct_match_count=5,
            semantic_match_count=3,
            manual_match_count=0,
            direct_match_rate=0.625,
            semantic_match_rate=0.375,
            avg_coordinate_change=25.5,
            avg_execution_time=0.5,
            failure_reasons={'element_not_found': 2},
            transition_match_count=8,
            transition_mismatch_count=2
        )
        
        data = stats.to_dict()
        
        assert data['total_actions'] == 10
        assert data['success_count'] == 8
        assert data['failure_count'] == 2
        assert abs(data['success_rate'] - 0.8) < 0.001
        assert data['direct_match_count'] == 5
        assert data['semantic_match_count'] == 3
        assert 'failure_reasons' in data
        assert data['failure_reasons']['element_not_found'] == 2
