"""
ReplayVerifier 단위 테스트

보고서 생성 및 카운트 계산 로직을 검증한다.
"""

import os
import sys
import json
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config_manager import ConfigManager
from src.replay_verifier import (
    ReplayVerifier, 
    VerificationResult, 
    ReplayReport,
    MatchingStatistics
)


class TestReportCountCalculation:
    """보고서 카운트 계산 로직 테스트
    
    Requirements: 2.1, 2.3
    """
    
    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager 생성"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'automation.hash_threshold': 5,
            'game.window_title': '',
            'automation.screenshot_dir': 'screenshots',
            'automation.capture_delay': 0.5,
        }.get(key, default)
        return config
    
    @pytest.fixture
    def verifier(self, mock_config):
        """ReplayVerifier 인스턴스 생성"""
        with patch('src.replay_verifier.ScreenshotVerifier'):
            with patch('src.replay_verifier.UIAnalyzer'):
                return ReplayVerifier(mock_config)
    
    def _create_verification_result(self, index: int, final_result: str, 
                                     similarity: float = 0.9) -> VerificationResult:
        """테스트용 VerificationResult 생성"""
        return VerificationResult(
            action_index=index,
            action_description=f'Test action {index}',
            screenshot_match=(final_result == 'pass'),
            screenshot_similarity=similarity,
            vision_verified=(final_result != 'pass'),
            vision_match=(final_result == 'warning'),
            final_result=final_result,
            details={}
        )
    
    def test_count_calculation_all_pass(self, verifier):
        """모든 액션이 pass인 경우 카운트 검증
        
        Requirements: 2.1, 2.3
        """
        # Given: 5개의 pass 결과
        verifier.test_case_name = "test_all_pass"
        verifier.start_time = datetime.now().isoformat()
        verifier.verification_results = [
            self._create_verification_result(i, 'pass') for i in range(5)
        ]
        
        # When: 보고서 생성
        report = verifier.generate_report()
        
        # Then: 카운트 검증
        assert report.total_actions == 5
        assert report.passed_count == 5
        assert report.failed_count == 0
        assert report.warning_count == 0
        assert report.passed_count + report.failed_count + report.warning_count == report.total_actions
        assert report.success_rate == 1.0
    
    def test_count_calculation_all_fail(self, verifier):
        """모든 액션이 fail인 경우 카운트 검증
        
        Requirements: 2.1, 2.3
        """
        # Given: 3개의 fail 결과
        verifier.test_case_name = "test_all_fail"
        verifier.start_time = datetime.now().isoformat()
        verifier.verification_results = [
            self._create_verification_result(i, 'fail', 0.3) for i in range(3)
        ]
        
        # When: 보고서 생성
        report = verifier.generate_report()
        
        # Then: 카운트 검증
        assert report.total_actions == 3
        assert report.passed_count == 0
        assert report.failed_count == 3
        assert report.warning_count == 0
        assert report.passed_count + report.failed_count + report.warning_count == report.total_actions
        assert report.success_rate == 0.0
    
    def test_count_calculation_mixed_results(self, verifier):
        """혼합된 결과의 카운트 검증
        
        Requirements: 2.1, 2.3
        """
        # Given: pass 2개, fail 1개, warning 2개
        verifier.test_case_name = "test_mixed"
        verifier.start_time = datetime.now().isoformat()
        verifier.verification_results = [
            self._create_verification_result(0, 'pass'),
            self._create_verification_result(1, 'fail', 0.3),
            self._create_verification_result(2, 'warning', 0.6),
            self._create_verification_result(3, 'pass'),
            self._create_verification_result(4, 'warning', 0.7),
        ]
        
        # When: 보고서 생성
        report = verifier.generate_report()
        
        # Then: 카운트 검증
        assert report.total_actions == 5
        assert report.passed_count == 2
        assert report.failed_count == 1
        assert report.warning_count == 2
        assert report.passed_count + report.failed_count + report.warning_count == report.total_actions
        # success_rate = (passed + warning) / total = (2 + 2) / 5 = 0.8
        assert report.success_rate == pytest.approx(0.8, rel=1e-6)
    
    def test_count_calculation_empty_results(self, verifier):
        """결과가 없는 경우 카운트 검증
        
        Requirements: 2.1, 2.3
        """
        # Given: 빈 결과
        verifier.test_case_name = "test_empty"
        verifier.start_time = datetime.now().isoformat()
        verifier.verification_results = []
        
        # When: 보고서 생성
        report = verifier.generate_report()
        
        # Then: 카운트 검증
        assert report.total_actions == 0
        assert report.passed_count == 0
        assert report.failed_count == 0
        assert report.warning_count == 0
        assert report.passed_count + report.failed_count + report.warning_count == report.total_actions
        assert report.success_rate == 0.0
    
    def test_success_rate_calculation(self, verifier):
        """성공률 계산 정확성 검증
        
        Requirements: 2.3
        success_rate = (passed_count + warning_count) / total_actions
        """
        # Given: pass 3개, warning 2개, fail 5개 = 총 10개
        verifier.test_case_name = "test_success_rate"
        verifier.start_time = datetime.now().isoformat()
        verifier.verification_results = [
            self._create_verification_result(0, 'pass'),
            self._create_verification_result(1, 'pass'),
            self._create_verification_result(2, 'pass'),
            self._create_verification_result(3, 'warning', 0.6),
            self._create_verification_result(4, 'warning', 0.7),
            self._create_verification_result(5, 'fail', 0.3),
            self._create_verification_result(6, 'fail', 0.2),
            self._create_verification_result(7, 'fail', 0.4),
            self._create_verification_result(8, 'fail', 0.1),
            self._create_verification_result(9, 'fail', 0.25),
        ]
        
        # When: 보고서 생성
        report = verifier.generate_report()
        
        # Then: 성공률 검증
        # success_rate = (3 + 2) / 10 = 0.5
        expected_success_rate = (3 + 2) / 10
        assert report.success_rate == pytest.approx(expected_success_rate, rel=1e-6)


class TestReportSaveFormats:
    """보고서 저장 형식 테스트
    
    Requirements: 2.5
    """
    
    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager 생성"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'automation.hash_threshold': 5,
            'game.window_title': '',
            'automation.screenshot_dir': 'screenshots',
            'automation.capture_delay': 0.5,
        }.get(key, default)
        return config
    
    @pytest.fixture
    def verifier(self, mock_config):
        """ReplayVerifier 인스턴스 생성"""
        with patch('src.replay_verifier.ScreenshotVerifier'):
            with patch('src.replay_verifier.UIAnalyzer'):
                return ReplayVerifier(mock_config)
    
    def _create_verification_result(self, index: int, final_result: str, 
                                     similarity: float = 0.9) -> VerificationResult:
        """테스트용 VerificationResult 생성"""
        return VerificationResult(
            action_index=index,
            action_description=f'Test action {index}',
            screenshot_match=(final_result == 'pass'),
            screenshot_similarity=similarity,
            vision_verified=(final_result != 'pass'),
            vision_match=(final_result == 'warning'),
            final_result=final_result,
            details={}
        )
    
    def test_save_report_creates_json_and_txt(self, verifier):
        """JSON과 TXT 형식 모두 저장되는지 확인
        
        Requirements: 2.5
        """
        # Given: 검증 결과가 있는 verifier
        verifier.test_case_name = "test_save"
        verifier.session_id = "20260116_120000"
        verifier.start_time = datetime.now().isoformat()
        verifier.verification_results = [
            self._create_verification_result(0, 'pass'),
            self._create_verification_result(1, 'fail', 0.3),
        ]
        report = verifier.generate_report()
        
        # When: 임시 디렉토리에 보고서 저장
        with tempfile.TemporaryDirectory() as tmpdir:
            saved_path = verifier.save_report(report, tmpdir)
            
            # Then: JSON 파일 존재 확인
            json_path = os.path.join(tmpdir, "test_save_20260116_120000_report.json")
            assert os.path.exists(json_path), f"JSON 파일이 생성되지 않음: {json_path}"
            
            # Then: TXT 파일 존재 확인
            txt_path = os.path.join(tmpdir, "test_save_20260116_120000_report.txt")
            assert os.path.exists(txt_path), f"TXT 파일이 생성되지 않음: {txt_path}"
            
            # Then: JSON 파일 내용 검증
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            assert json_data['test_case_name'] == 'test_save'
            assert json_data['total_actions'] == 2
            assert json_data['passed_count'] == 1
            assert json_data['failed_count'] == 1
            
            # Then: TXT 파일 내용 검증
            with open(txt_path, 'r', encoding='utf-8') as f:
                txt_content = f.read()
            assert 'test_save' in txt_content
            assert '✓' in txt_content  # pass 표시
            assert '✗' in txt_content  # fail 표시
    
    def test_save_report_to_specified_directory(self, verifier):
        """지정된 디렉토리에 보고서가 저장되는지 확인
        
        Requirements: 2.5
        """
        # Given: 검증 결과가 있는 verifier
        verifier.test_case_name = "test_dir"
        verifier.session_id = "20260116_130000"
        verifier.start_time = datetime.now().isoformat()
        verifier.verification_results = [
            self._create_verification_result(0, 'pass'),
        ]
        report = verifier.generate_report()
        
        # When: 특정 디렉토리에 저장
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = os.path.join(tmpdir, "custom_reports")
            saved_path = verifier.save_report(report, custom_dir)
            
            # Then: 디렉토리가 생성되었는지 확인
            assert os.path.exists(custom_dir), f"디렉토리가 생성되지 않음: {custom_dir}"
            
            # Then: 파일이 해당 디렉토리에 저장되었는지 확인
            assert saved_path.startswith(custom_dir), \
                f"파일이 지정된 디렉토리에 저장되지 않음: {saved_path}"


class TestVerificationResultToDict:
    """VerificationResult.to_dict() 테스트
    
    Requirements: 6.2
    """
    
    def test_to_dict_contains_all_required_fields(self):
        """to_dict()가 모든 필수 필드를 포함하는지 확인
        
        Requirements: 6.2
        """
        # Given: VerificationResult 인스턴스
        result = VerificationResult(
            action_index=5,
            action_description='Click button',
            screenshot_match=True,
            screenshot_similarity=0.95,
            vision_verified=False,
            vision_match=False,
            final_result='pass',
            details={'key': 'value'}
        )
        
        # When: to_dict() 호출
        result_dict = result.to_dict()
        
        # Then: 필수 필드 존재 확인
        assert 'action_index' in result_dict
        assert 'action_description' in result_dict
        assert 'screenshot_match' in result_dict
        assert 'screenshot_similarity' in result_dict
        assert 'vision_verified' in result_dict
        assert 'vision_match' in result_dict
        assert 'final_result' in result_dict
        assert 'details' in result_dict
        
        # Then: 값 검증
        assert result_dict['action_index'] == 5
        assert result_dict['final_result'] == 'pass'
        assert result_dict['screenshot_similarity'] == 0.95
    
    def test_required_fields_per_requirements_6_2(self):
        """Requirements 6.2에서 명시한 필수 필드 존재 확인
        
        Requirements: 6.2
        - action_index, final_result, screenshot_similarity, vision_match 필드 존재 확인
        """
        # Given: 다양한 상태의 VerificationResult 인스턴스들
        test_cases = [
            # pass 상태
            VerificationResult(
                action_index=0,
                action_description='Pass action',
                screenshot_match=True,
                screenshot_similarity=0.95,
                vision_verified=False,
                vision_match=False,
                final_result='pass',
                details={}
            ),
            # fail 상태
            VerificationResult(
                action_index=1,
                action_description='Fail action',
                screenshot_match=False,
                screenshot_similarity=0.3,
                vision_verified=True,
                vision_match=False,
                final_result='fail',
                details={'error': 'mismatch'}
            ),
            # warning 상태
            VerificationResult(
                action_index=2,
                action_description='Warning action',
                screenshot_match=False,
                screenshot_similarity=0.6,
                vision_verified=True,
                vision_match=True,
                final_result='warning',
                details={'note': 'semantic match'}
            ),
        ]
        
        # Requirements 6.2에서 명시한 필수 필드
        required_fields = ['action_index', 'final_result', 'screenshot_similarity', 'vision_match']
        
        for result in test_cases:
            # When: to_dict() 호출
            result_dict = result.to_dict()
            
            # Then: 필수 필드 존재 확인
            for field in required_fields:
                assert field in result_dict, \
                    f"필수 필드 '{field}'가 누락됨 (final_result={result.final_result})"
            
            # Then: 필드 타입 검증
            assert isinstance(result_dict['action_index'], int), \
                f"action_index는 int여야 함: {type(result_dict['action_index'])}"
            assert isinstance(result_dict['final_result'], str), \
                f"final_result는 str이어야 함: {type(result_dict['final_result'])}"
            assert isinstance(result_dict['screenshot_similarity'], float), \
                f"screenshot_similarity는 float이어야 함: {type(result_dict['screenshot_similarity'])}"
            assert isinstance(result_dict['vision_match'], bool), \
                f"vision_match는 bool이어야 함: {type(result_dict['vision_match'])}"
    
    def test_verification_result_dataclass_has_required_attributes(self):
        """VerificationResult dataclass가 필수 속성을 가지는지 확인
        
        Requirements: 6.2
        """
        # Given: VerificationResult 인스턴스
        result = VerificationResult(
            action_index=10,
            action_description='Test',
            screenshot_match=True,
            screenshot_similarity=0.9,
            vision_verified=False,
            vision_match=False,
            final_result='pass',
            details={}
        )
        
        # Then: 필수 속성 존재 확인 (dataclass 속성으로 직접 접근)
        assert hasattr(result, 'action_index')
        assert hasattr(result, 'final_result')
        assert hasattr(result, 'screenshot_similarity')
        assert hasattr(result, 'vision_match')
        
        # Then: 값 접근 가능 확인
        assert result.action_index == 10
        assert result.final_result == 'pass'
        assert result.screenshot_similarity == 0.9
        assert result.vision_match == False


class TestReplayReportToDict:
    """ReplayReport.to_dict() 테스트
    
    Requirements: 6.3
    """
    
    def test_to_dict_contains_all_required_fields(self):
        """to_dict()가 모든 필수 필드를 포함하는지 확인
        
        Requirements: 6.3
        """
        # Given: ReplayReport 인스턴스
        report = ReplayReport(
            test_case_name='test_case',
            session_id='20260116_140000',
            start_time='2026-01-16T14:00:00',
            end_time='2026-01-16T14:05:00',
            total_actions=10,
            passed_count=7,
            failed_count=2,
            warning_count=1,
            success_rate=0.8,
            verification_results=[],
            summary='Test summary'
        )
        
        # When: to_dict() 호출
        report_dict = report.to_dict()
        
        # Then: 필수 필드 존재 확인
        assert 'test_case_name' in report_dict
        assert 'session_id' in report_dict
        assert 'start_time' in report_dict
        assert 'end_time' in report_dict
        assert 'total_actions' in report_dict
        assert 'passed_count' in report_dict
        assert 'failed_count' in report_dict
        assert 'warning_count' in report_dict
        assert 'success_rate' in report_dict
        assert 'verification_results' in report_dict
        assert 'summary' in report_dict
        
        # Then: 값 검증
        assert report_dict['total_actions'] == 10
        assert report_dict['passed_count'] == 7
        assert report_dict['failed_count'] == 2
        assert report_dict['warning_count'] == 1
        assert report_dict['success_rate'] == 0.8
    
    def test_required_fields_per_requirements_6_3(self):
        """Requirements 6.3에서 명시한 필수 필드 존재 확인
        
        Requirements: 6.3
        - total_actions, passed_count, failed_count, warning_count, success_rate 필드 존재 확인
        """
        # Given: 다양한 상태의 ReplayReport 인스턴스들
        test_cases = [
            # 모두 pass
            ReplayReport(
                test_case_name='all_pass',
                session_id='session_1',
                start_time='2026-01-16T00:00:00',
                end_time='2026-01-16T00:01:00',
                total_actions=5,
                passed_count=5,
                failed_count=0,
                warning_count=0,
                success_rate=1.0,
                verification_results=[],
                summary='All passed'
            ),
            # 모두 fail
            ReplayReport(
                test_case_name='all_fail',
                session_id='session_2',
                start_time='2026-01-16T00:00:00',
                end_time='2026-01-16T00:01:00',
                total_actions=3,
                passed_count=0,
                failed_count=3,
                warning_count=0,
                success_rate=0.0,
                verification_results=[],
                summary='All failed'
            ),
            # 혼합
            ReplayReport(
                test_case_name='mixed',
                session_id='session_3',
                start_time='2026-01-16T00:00:00',
                end_time='2026-01-16T00:01:00',
                total_actions=10,
                passed_count=4,
                failed_count=3,
                warning_count=3,
                success_rate=0.7,
                verification_results=[],
                summary='Mixed results'
            ),
            # 빈 결과
            ReplayReport(
                test_case_name='empty',
                session_id='session_4',
                start_time='2026-01-16T00:00:00',
                end_time='2026-01-16T00:01:00',
                total_actions=0,
                passed_count=0,
                failed_count=0,
                warning_count=0,
                success_rate=0.0,
                verification_results=[],
                summary='Empty'
            ),
        ]
        
        # Requirements 6.3에서 명시한 필수 필드
        required_fields = ['total_actions', 'passed_count', 'failed_count', 'warning_count', 'success_rate']
        
        for report in test_cases:
            # When: to_dict() 호출
            report_dict = report.to_dict()
            
            # Then: 필수 필드 존재 확인
            for field in required_fields:
                assert field in report_dict, \
                    f"필수 필드 '{field}'가 누락됨 (test_case_name={report.test_case_name})"
            
            # Then: 필드 타입 검증
            assert isinstance(report_dict['total_actions'], int), \
                f"total_actions는 int여야 함: {type(report_dict['total_actions'])}"
            assert isinstance(report_dict['passed_count'], int), \
                f"passed_count는 int여야 함: {type(report_dict['passed_count'])}"
            assert isinstance(report_dict['failed_count'], int), \
                f"failed_count는 int여야 함: {type(report_dict['failed_count'])}"
            assert isinstance(report_dict['warning_count'], int), \
                f"warning_count는 int여야 함: {type(report_dict['warning_count'])}"
            assert isinstance(report_dict['success_rate'], float), \
                f"success_rate는 float이어야 함: {type(report_dict['success_rate'])}"
    
    def test_replay_report_dataclass_has_required_attributes(self):
        """ReplayReport dataclass가 필수 속성을 가지는지 확인
        
        Requirements: 6.3
        """
        # Given: ReplayReport 인스턴스
        report = ReplayReport(
            test_case_name='test',
            session_id='session',
            start_time='2026-01-16T00:00:00',
            end_time='2026-01-16T00:01:00',
            total_actions=10,
            passed_count=6,
            failed_count=2,
            warning_count=2,
            success_rate=0.8,
            verification_results=[],
            summary='Test'
        )
        
        # Then: 필수 속성 존재 확인 (dataclass 속성으로 직접 접근)
        assert hasattr(report, 'total_actions')
        assert hasattr(report, 'passed_count')
        assert hasattr(report, 'failed_count')
        assert hasattr(report, 'warning_count')
        assert hasattr(report, 'success_rate')
        
        # Then: 값 접근 가능 확인
        assert report.total_actions == 10
        assert report.passed_count == 6
        assert report.failed_count == 2
        assert report.warning_count == 2
        assert report.success_rate == 0.8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


class TestScreenshotPathMissingWarning:
    """screenshot_path 없는 액션의 warning 처리 테스트
    
    Requirements: 3.2
    """
    
    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager 생성"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'automation.hash_threshold': 5,
            'game.window_title': '',
            'automation.screenshot_dir': 'screenshots',
            'automation.capture_delay': 0.0,  # 테스트에서는 대기 시간 없음
        }.get(key, default)
        return config
    
    @pytest.fixture
    def verifier(self, mock_config):
        """ReplayVerifier 인스턴스 생성"""
        with patch('src.replay_verifier.ScreenshotVerifier'):
            with patch('src.replay_verifier.UIAnalyzer'):
                verifier = ReplayVerifier(mock_config)
                verifier.start_verification_session("test_missing_screenshot")
                return verifier
    
    def test_verify_coordinate_action_no_screenshot_path(self, verifier):
        """screenshot_path가 None인 경우 warning 처리
        
        Requirements: 3.2
        """
        from PIL import Image
        
        # Given: screenshot_path가 없는 액션
        action = {
            'action_type': 'click',
            'x': 100,
            'y': 200,
            'description': 'Test click without screenshot',
            'screenshot_path': None,
        }
        current_screenshot = Image.new('RGB', (100, 100), color='red')
        
        # When: verify_coordinate_action 호출
        result = verifier.verify_coordinate_action(0, action, current_screenshot)
        
        # Then: warning으로 처리되어야 함
        assert result.final_result == 'warning', \
            f"screenshot_path 없는 액션이 warning이 아님: {result.final_result}"
        assert result.screenshot_similarity == 0.0, \
            f"screenshot_similarity가 0.0이 아님: {result.screenshot_similarity}"
        assert result.vision_verified == False, \
            "Vision LLM 검증이 수행되지 않아야 함"
        assert 'note' in result.details, \
            "details에 note가 있어야 함"
        assert '검증 생략' in result.details.get('note', '') or 'screenshot_path' in result.details.get('note', ''), \
            f"note가 적절하지 않음: {result.details.get('note')}"
    
    def test_verify_coordinate_action_empty_screenshot_path(self, verifier):
        """screenshot_path가 빈 문자열인 경우 warning 처리
        
        Requirements: 3.2
        """
        from PIL import Image
        
        # Given: screenshot_path가 빈 문자열인 액션
        action = {
            'action_type': 'click',
            'x': 100,
            'y': 200,
            'description': 'Test click with empty screenshot path',
            'screenshot_path': '',
        }
        current_screenshot = Image.new('RGB', (100, 100), color='blue')
        
        # When: verify_coordinate_action 호출
        result = verifier.verify_coordinate_action(1, action, current_screenshot)
        
        # Then: warning으로 처리되어야 함
        assert result.final_result == 'warning', \
            f"빈 screenshot_path 액션이 warning이 아님: {result.final_result}"
        assert result.screenshot_similarity == 0.0
        assert result.vision_verified == False
    
    def test_verify_coordinate_action_nonexistent_screenshot_path(self, verifier):
        """screenshot_path가 존재하지 않는 파일인 경우 warning 처리
        
        Requirements: 3.2
        """
        from PIL import Image
        
        # Given: 존재하지 않는 파일 경로를 가진 액션
        action = {
            'action_type': 'click',
            'x': 100,
            'y': 200,
            'description': 'Test click with nonexistent screenshot',
            'screenshot_path': '/nonexistent/path/screenshot.png',
        }
        current_screenshot = Image.new('RGB', (100, 100), color='green')
        
        # When: verify_coordinate_action 호출
        result = verifier.verify_coordinate_action(2, action, current_screenshot)
        
        # Then: warning으로 처리되어야 함
        assert result.final_result == 'warning', \
            f"존재하지 않는 screenshot_path 액션이 warning이 아님: {result.final_result}"
        assert result.screenshot_similarity == 0.0
        assert result.vision_verified == False
        assert '파일 미존재' in result.details.get('note', '') or 'screenshot_path' in result.details.get('note', '')


class TestDetermineTestResult:
    """전체 테스트 결과 판정 테스트
    
    Requirements: 4.3
    """
    
    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager 생성"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'automation.hash_threshold': 5,
            'game.window_title': '',
            'automation.screenshot_dir': 'screenshots',
            'automation.capture_delay': 0.5,
        }.get(key, default)
        return config
    
    @pytest.fixture
    def verifier(self, mock_config):
        """ReplayVerifier 인스턴스 생성"""
        with patch('src.replay_verifier.ScreenshotVerifier'):
            with patch('src.replay_verifier.UIAnalyzer'):
                return ReplayVerifier(mock_config)
    
    def _create_verification_result(self, index: int, final_result: str) -> VerificationResult:
        """테스트용 VerificationResult 생성"""
        return VerificationResult(
            action_index=index,
            action_description=f'Test action {index}',
            screenshot_match=(final_result == 'pass'),
            screenshot_similarity=0.9 if final_result == 'pass' else 0.3,
            vision_verified=(final_result != 'pass'),
            vision_match=(final_result == 'warning'),
            final_result=final_result,
            details={}
        )
    
    def test_determine_test_result_all_pass(self, verifier):
        """모든 액션이 pass인 경우 True 반환
        
        Requirements: 4.3
        """
        # Given: 모든 결과가 pass
        verifier.verification_results = [
            self._create_verification_result(i, 'pass') for i in range(5)
        ]
        
        # When: determine_test_result 호출
        result = verifier.determine_test_result()
        
        # Then: True 반환
        assert result == True, "모든 액션이 pass인데 결과가 False"
    
    def test_determine_test_result_all_warning(self, verifier):
        """모든 액션이 warning인 경우 True 반환
        
        Requirements: 4.3
        """
        # Given: 모든 결과가 warning
        verifier.verification_results = [
            self._create_verification_result(i, 'warning') for i in range(3)
        ]
        
        # When: determine_test_result 호출
        result = verifier.determine_test_result()
        
        # Then: True 반환
        assert result == True, "모든 액션이 warning인데 결과가 False"
    
    def test_determine_test_result_mixed_pass_warning(self, verifier):
        """pass와 warning이 혼합된 경우 True 반환
        
        Requirements: 4.3
        """
        # Given: pass와 warning 혼합
        verifier.verification_results = [
            self._create_verification_result(0, 'pass'),
            self._create_verification_result(1, 'warning'),
            self._create_verification_result(2, 'pass'),
            self._create_verification_result(3, 'warning'),
        ]
        
        # When: determine_test_result 호출
        result = verifier.determine_test_result()
        
        # Then: True 반환
        assert result == True, "pass와 warning만 있는데 결과가 False"
    
    def test_determine_test_result_one_fail(self, verifier):
        """하나라도 fail이 있으면 False 반환
        
        Requirements: 4.3
        """
        # Given: 하나의 fail 포함
        verifier.verification_results = [
            self._create_verification_result(0, 'pass'),
            self._create_verification_result(1, 'pass'),
            self._create_verification_result(2, 'fail'),  # 하나의 fail
            self._create_verification_result(3, 'pass'),
        ]
        
        # When: determine_test_result 호출
        result = verifier.determine_test_result()
        
        # Then: False 반환
        assert result == False, "fail이 있는데 결과가 True"
    
    def test_determine_test_result_all_fail(self, verifier):
        """모든 액션이 fail인 경우 False 반환
        
        Requirements: 4.3
        """
        # Given: 모든 결과가 fail
        verifier.verification_results = [
            self._create_verification_result(i, 'fail') for i in range(3)
        ]
        
        # When: determine_test_result 호출
        result = verifier.determine_test_result()
        
        # Then: False 반환
        assert result == False, "모든 액션이 fail인데 결과가 True"
    
    def test_determine_test_result_empty(self, verifier):
        """결과가 없는 경우 True 반환
        
        Requirements: 4.3
        """
        # Given: 빈 결과
        verifier.verification_results = []
        
        # When: determine_test_result 호출
        result = verifier.determine_test_result()
        
        # Then: True 반환 (검증 결과가 없으면 성공으로 간주)
        assert result == True, "결과가 없는데 False 반환"


class TestMixedTestCaseHandling:
    """혼합 테스트 케이스 처리 테스트
    
    semantic_info가 있는 액션과 없는 액션이 혼재된 경우를 테스트한다.
    
    Requirements: 3.3
    """
    
    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager 생성"""
        config = Mock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: {
            'automation.hash_threshold': 5,
            'game.window_title': '',
            'automation.screenshot_dir': 'screenshots',
            'automation.capture_delay': 0.0,
        }.get(key, default)
        return config
    
    @pytest.fixture
    def verifier(self, mock_config):
        """ReplayVerifier 인스턴스 생성"""
        with patch('src.replay_verifier.ScreenshotVerifier') as mock_sv:
            # 스크린샷 비교 결과 mock
            mock_sv_instance = Mock()
            mock_sv_instance.verify_screenshot.return_value = {
                'match': True,
                'similarity': 0.95,
                'method': 'ssim'
            }
            mock_sv.return_value = mock_sv_instance
            
            with patch('src.replay_verifier.UIAnalyzer'):
                verifier = ReplayVerifier(mock_config)
                verifier.start_verification_session("test_mixed_cases")
                verifier.screenshot_verifier = mock_sv_instance
                return verifier
    
    def test_mixed_actions_with_and_without_semantic_info(self, verifier):
        """semantic_info가 있는 액션과 없는 액션이 혼재된 경우
        
        Requirements: 3.3
        """
        from PIL import Image
        import tempfile
        import os
        
        # Given: 임시 스크린샷 파일 생성
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = os.path.join(tmpdir, "test_screenshot.png")
            test_image = Image.new('RGB', (100, 100), color='red')
            test_image.save(screenshot_path)
            
            # 혼합된 액션들
            actions = [
                # semantic_info가 없는 좌표 기반 액션
                {
                    'action_type': 'click',
                    'x': 100,
                    'y': 200,
                    'description': 'Coordinate-based click',
                    'screenshot_path': screenshot_path,
                    # semantic_info 없음
                },
                # semantic_info가 있는 의미론적 액션
                {
                    'action_type': 'click',
                    'x': 300,
                    'y': 400,
                    'description': 'Semantic click on button',
                    'screenshot_path': screenshot_path,
                    'semantic_info': {
                        'element_type': 'button',
                        'element_text': 'Start',
                        'confidence': 0.95
                    }
                },
                # screenshot_path가 없는 액션
                {
                    'action_type': 'click',
                    'x': 500,
                    'y': 600,
                    'description': 'Click without screenshot',
                    'screenshot_path': None,
                },
            ]
            
            current_screenshot = Image.new('RGB', (100, 100), color='blue')
            
            # When: 각 액션에 대해 검증 수행
            results = []
            for i, action in enumerate(actions):
                result = verifier.verify_coordinate_action(i, action, current_screenshot)
                results.append(result)
            
            # Then: 각 액션 타입에 맞는 검증 결과 확인
            # 첫 번째 액션: screenshot_path 있음 -> pass (mock이 True 반환)
            assert results[0].final_result == 'pass', \
                f"좌표 기반 액션이 pass가 아님: {results[0].final_result}"
            
            # 두 번째 액션: semantic_info 있지만 screenshot_path로 검증 -> pass
            assert results[1].final_result == 'pass', \
                f"의미론적 액션이 pass가 아님: {results[1].final_result}"
            
            # 세 번째 액션: screenshot_path 없음 -> warning
            assert results[2].final_result == 'warning', \
                f"screenshot_path 없는 액션이 warning이 아님: {results[2].final_result}"
    
    def test_capture_and_verify_handles_semantic_info_action(self, verifier):
        """capture_and_verify가 semantic_info가 있는 액션도 처리하는지 확인
        
        Requirements: 3.3
        """
        from PIL import Image
        import tempfile
        import os
        
        # Given: semantic_info가 있는 액션
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = os.path.join(tmpdir, "semantic_screenshot.png")
            test_image = Image.new('RGB', (100, 100), color='green')
            test_image.save(screenshot_path)
            
            action = {
                'action_type': 'click',
                'x': 200,
                'y': 300,
                'description': 'Click on Start button',
                'screenshot_path': screenshot_path,
                'semantic_info': {
                    'element_type': 'button',
                    'element_text': 'Start',
                    'bounding_box': {'x': 180, 'y': 280, 'width': 40, 'height': 40},
                    'confidence': 0.92
                },
                'screen_transition': {
                    'from_screen': 'main_menu',
                    'to_screen': 'game_screen'
                }
            }
            
            # When: capture_and_verify 호출 (내부적으로 screenshot_path로 검증)
            # capture_and_verify는 스크린샷을 캡처하므로 verify_coordinate_action 사용
            current_screenshot = Image.new('RGB', (100, 100), color='yellow')
            result = verifier.verify_coordinate_action(0, action, current_screenshot)
            
            # Then: semantic_info가 있어도 screenshot_path로 검증 수행
            assert result.final_result == 'pass', \
                f"semantic_info가 있는 액션 검증 실패: {result.final_result}"
            assert result.screenshot_similarity > 0, \
                "스크린샷 유사도가 계산되어야 함"
    
    def test_capture_and_verify_handles_coordinate_only_action(self, verifier):
        """capture_and_verify가 좌표만 있는 액션도 처리하는지 확인
        
        Requirements: 3.1, 3.3
        """
        from PIL import Image
        import tempfile
        import os
        
        # Given: semantic_info가 없는 좌표 기반 액션
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = os.path.join(tmpdir, "coord_screenshot.png")
            test_image = Image.new('RGB', (100, 100), color='purple')
            test_image.save(screenshot_path)
            
            action = {
                'action_type': 'click',
                'x': 150,
                'y': 250,
                'description': 'Simple coordinate click',
                'screenshot_path': screenshot_path,
                'button': 'left',
                # semantic_info 없음
            }
            
            current_screenshot = Image.new('RGB', (100, 100), color='orange')
            
            # When: verify_coordinate_action 호출
            result = verifier.verify_coordinate_action(0, action, current_screenshot)
            
            # Then: 좌표 기반 액션도 정상 검증
            assert result.final_result == 'pass', \
                f"좌표 기반 액션 검증 실패: {result.final_result}"
            assert result.details.get('verification_type') == 'coordinate_action', \
                "verification_type이 coordinate_action이어야 함"
