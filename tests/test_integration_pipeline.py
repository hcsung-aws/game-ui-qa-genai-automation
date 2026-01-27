"""
IntegrationPipeline 단위 테스트

Requirements: 7.2, 7.3, 7.4
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

from src.bvt_integration.pipeline import IntegrationPipeline, PipelineStage
from src.bvt_integration.models import (
    BVTTestCase,
    SemanticTestCase,
    SemanticAction,
    SemanticSummary,
    ActionSummary,
    MatchResult,
    ActionRange,
    PlayTestCase,
    PlayTestResult,
    BVTReference,
    MatchingReport,
    PipelineResult,
    TestStatus
)
from src.bvt_integration.bvt_parser import BVTParser, BVTParseError
from src.bvt_integration.tc_loader import SemanticTestCaseLoader
from src.bvt_integration.summary_generator import SemanticSummaryGenerator
from src.bvt_integration.matching_analyzer import MatchingAnalyzer
from src.bvt_integration.auto_play_generator import AutoPlayGenerator
from src.bvt_integration.bvt_updater import BVTUpdater
from src.bvt_integration.report_generator import ReportGenerator


class TestIntegrationPipelineDryRun:
    """Dry-run 모드 동작 테스트
    
    Requirements: 7.3
    """
    
    def test_dry_run_skips_test_execution(self, tmp_path):
        """dry_run=True일 때 테스트 실행을 건너뛰는지 확인"""
        # Given: 모의 컴포넌트 설정
        mock_parser = Mock(spec=BVTParser)
        mock_loader = Mock(spec=SemanticTestCaseLoader)
        mock_summary_gen = Mock(spec=SemanticSummaryGenerator)
        mock_analyzer = Mock(spec=MatchingAnalyzer)
        mock_play_gen = Mock(spec=AutoPlayGenerator)
        mock_updater = Mock(spec=BVTUpdater)
        mock_report_gen = Mock(spec=ReportGenerator)
        
        # BVT 케이스 설정
        bvt_case = BVTTestCase(
            no=1, category1="메인", category2="UI", category3="",
            check="버튼 클릭", test_result="Not Tested",
            bts_id="", comment=""
        )
        mock_parser.parse.return_value = [bvt_case]
        
        # 테스트 케이스 설정
        test_case = SemanticTestCase(
            name="test-001",
            created_at="2026-01-25T00:00:00",
            actions=[
                SemanticAction(
                    timestamp="2026-01-25T00:00:01",
                    action_type="click",
                    x=100, y=200,
                    description="버튼 클릭"
                )
            ],
            json_path="/test/test-001.json"
        )
        mock_loader.load_directory.return_value = [test_case]
        
        # 요약 설정
        summary = SemanticSummary(
            generated_at="2026-01-25T00:00:00",
            test_case_summaries=[
                ActionSummary(
                    test_case_name="test-001",
                    intents=["click"],
                    target_elements=["button"],
                    screen_states=[],
                    action_descriptions=["버튼 클릭"],
                    action_count=1
                )
            ],
            total_test_cases=1,
            total_actions=1
        )
        mock_summary_gen.generate.return_value = summary
        
        # 매칭 결과 설정 (고신뢰도)
        match_result = MatchResult(
            bvt_case=bvt_case,
            matched_test_case="test-001",
            action_range=ActionRange(start_index=0, end_index=0),
            confidence_score=0.85,
            is_high_confidence=True,
            match_details={}
        )
        mock_analyzer.analyze.return_value = [match_result]
        
        # 플레이 테스트 설정
        play_test = PlayTestCase(
            name="bvt_0001_play",
            bvt_reference=BVTReference(
                no=1, category1="메인", category2="UI",
                category3="", check="버튼 클릭"
            ),
            source_test_case="test-001",
            actions=[test_case.actions[0]],
            created_at="2026-01-25T00:00:00"
        )
        mock_play_gen.generate_from_test_case.return_value = play_test
        mock_play_gen.cache_test_case = Mock()
        mock_play_gen.save_play_test = Mock()
        
        # 리포트 설정
        report = MatchingReport(
            generated_at="2026-01-25T00:00:00",
            total_bvt_items=1,
            matched_items=1,
            unmatched_items=0,
            high_confidence_matches=[match_result],
            low_confidence_matches=[],
            unmatched_bvt_cases=[],
            coverage_percentage=100.0
        )
        mock_report_gen.generate.return_value = report
        mock_report_gen.to_json.return_value = "{}"
        mock_report_gen.to_markdown.return_value = "# Report"
        
        # 파이프라인 생성
        pipeline = IntegrationPipeline(
            bvt_parser=mock_parser,
            tc_loader=mock_loader,
            summary_generator=mock_summary_gen,
            matching_analyzer=mock_analyzer,
            play_generator=mock_play_gen,
            bvt_updater=mock_updater,
            report_generator=mock_report_gen
        )
        
        # BVT 파일 생성
        bvt_file = tmp_path / "test_bvt.csv"
        bvt_file.write_text("dummy")
        
        # When: dry_run 모드로 실행
        result = pipeline.run(
            bvt_path=str(bvt_file),
            test_cases_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            dry_run=True
        )
        
        # Then: 테스트 실행이 호출되지 않아야 함
        mock_play_gen.execute.assert_not_called()
        
        # BVT 업데이트도 호출되지 않아야 함 (결과가 없으므로)
        mock_updater.update.assert_not_called()
        
        # 성공해야 함
        assert result.success is True
    
    def test_dry_run_still_generates_report(self, tmp_path):
        """dry_run 모드에서도 리포트는 생성되는지 확인"""
        # Given: 간단한 모의 설정
        mock_parser = Mock(spec=BVTParser)
        mock_loader = Mock(spec=SemanticTestCaseLoader)
        mock_summary_gen = Mock(spec=SemanticSummaryGenerator)
        mock_analyzer = Mock(spec=MatchingAnalyzer)
        mock_play_gen = Mock(spec=AutoPlayGenerator)
        mock_updater = Mock(spec=BVTUpdater)
        mock_report_gen = Mock(spec=ReportGenerator)
        
        mock_parser.parse.return_value = []
        mock_loader.load_directory.return_value = []
        mock_summary_gen.generate.return_value = SemanticSummary(
            generated_at="", test_case_summaries=[], 
            total_test_cases=0, total_actions=0
        )
        mock_analyzer.analyze.return_value = []
        mock_play_gen.cache_test_case = Mock()
        
        report = MatchingReport(
            generated_at="2026-01-25T00:00:00",
            total_bvt_items=0, matched_items=0, unmatched_items=0,
            high_confidence_matches=[], low_confidence_matches=[],
            unmatched_bvt_cases=[], coverage_percentage=0.0
        )
        mock_report_gen.generate.return_value = report
        mock_report_gen.to_json.return_value = "{}"
        mock_report_gen.to_markdown.return_value = "# Report"
        
        pipeline = IntegrationPipeline(
            bvt_parser=mock_parser,
            tc_loader=mock_loader,
            summary_generator=mock_summary_gen,
            matching_analyzer=mock_analyzer,
            play_generator=mock_play_gen,
            bvt_updater=mock_updater,
            report_generator=mock_report_gen
        )
        
        bvt_file = tmp_path / "test_bvt.csv"
        bvt_file.write_text("dummy")
        
        # When
        result = pipeline.run(
            bvt_path=str(bvt_file),
            test_cases_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            dry_run=True
        )
        
        # Then: 리포트 생성이 호출되어야 함
        mock_report_gen.generate.assert_called_once()
        assert result.matching_report is not None


class TestIntegrationPipelineProgressCallback:
    """진행 콜백 호출 테스트
    
    Requirements: 7.2
    """
    
    def test_progress_callback_called_for_each_stage(self, tmp_path):
        """각 단계에서 진행 콜백이 호출되는지 확인"""
        # Given: 모의 컴포넌트 설정
        mock_parser = Mock(spec=BVTParser)
        mock_loader = Mock(spec=SemanticTestCaseLoader)
        mock_summary_gen = Mock(spec=SemanticSummaryGenerator)
        mock_analyzer = Mock(spec=MatchingAnalyzer)
        mock_play_gen = Mock(spec=AutoPlayGenerator)
        mock_updater = Mock(spec=BVTUpdater)
        mock_report_gen = Mock(spec=ReportGenerator)
        
        mock_parser.parse.return_value = []
        mock_loader.load_directory.return_value = []
        mock_summary_gen.generate.return_value = SemanticSummary(
            generated_at="", test_case_summaries=[],
            total_test_cases=0, total_actions=0
        )
        mock_analyzer.analyze.return_value = []
        mock_play_gen.cache_test_case = Mock()
        
        report = MatchingReport(
            generated_at="", total_bvt_items=0, matched_items=0,
            unmatched_items=0, high_confidence_matches=[],
            low_confidence_matches=[], unmatched_bvt_cases=[],
            coverage_percentage=0.0
        )
        mock_report_gen.generate.return_value = report
        mock_report_gen.to_json.return_value = "{}"
        mock_report_gen.to_markdown.return_value = ""
        
        pipeline = IntegrationPipeline(
            bvt_parser=mock_parser,
            tc_loader=mock_loader,
            summary_generator=mock_summary_gen,
            matching_analyzer=mock_analyzer,
            play_generator=mock_play_gen,
            bvt_updater=mock_updater,
            report_generator=mock_report_gen
        )
        
        bvt_file = tmp_path / "test_bvt.csv"
        bvt_file.write_text("dummy")
        
        # 콜백 모의 객체
        progress_callback = Mock()
        
        # When
        pipeline.run(
            bvt_path=str(bvt_file),
            test_cases_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            dry_run=True,
            progress_callback=progress_callback
        )
        
        # Then: 콜백이 여러 번 호출되어야 함
        assert progress_callback.call_count >= 5
        
        # 호출된 단계들 확인
        called_stages = [call[0][0] for call in progress_callback.call_args_list]
        assert PipelineStage.PARSING in called_stages
        assert PipelineStage.LOADING in called_stages
        assert PipelineStage.SUMMARIZING in called_stages
        assert PipelineStage.MATCHING in called_stages
        assert PipelineStage.GENERATING in called_stages
    
    def test_progress_callback_receives_correct_arguments(self, tmp_path):
        """콜백이 올바른 인자를 받는지 확인"""
        # Given
        mock_parser = Mock(spec=BVTParser)
        mock_loader = Mock(spec=SemanticTestCaseLoader)
        mock_summary_gen = Mock(spec=SemanticSummaryGenerator)
        mock_analyzer = Mock(spec=MatchingAnalyzer)
        mock_play_gen = Mock(spec=AutoPlayGenerator)
        mock_updater = Mock(spec=BVTUpdater)
        mock_report_gen = Mock(spec=ReportGenerator)
        
        mock_parser.parse.return_value = []
        mock_loader.load_directory.return_value = []
        mock_summary_gen.generate.return_value = SemanticSummary(
            generated_at="", test_case_summaries=[],
            total_test_cases=0, total_actions=0
        )
        mock_analyzer.analyze.return_value = []
        mock_play_gen.cache_test_case = Mock()
        
        report = MatchingReport(
            generated_at="", total_bvt_items=0, matched_items=0,
            unmatched_items=0, high_confidence_matches=[],
            low_confidence_matches=[], unmatched_bvt_cases=[],
            coverage_percentage=0.0
        )
        mock_report_gen.generate.return_value = report
        mock_report_gen.to_json.return_value = "{}"
        mock_report_gen.to_markdown.return_value = ""
        
        pipeline = IntegrationPipeline(
            bvt_parser=mock_parser,
            tc_loader=mock_loader,
            summary_generator=mock_summary_gen,
            matching_analyzer=mock_analyzer,
            play_generator=mock_play_gen,
            bvt_updater=mock_updater,
            report_generator=mock_report_gen
        )
        
        bvt_file = tmp_path / "test_bvt.csv"
        bvt_file.write_text("dummy")
        
        received_calls = []
        
        def track_callback(stage, message, progress):
            received_calls.append((stage, message, progress))
        
        # When
        pipeline.run(
            bvt_path=str(bvt_file),
            test_cases_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            dry_run=True,
            progress_callback=track_callback
        )
        
        # Then: 각 호출이 (stage, message, progress) 형식이어야 함
        for stage, message, progress in received_calls:
            assert isinstance(stage, str)
            assert isinstance(message, str)
            assert isinstance(progress, float)
            assert 0.0 <= progress <= 1.0
    
    def test_progress_callback_exception_does_not_stop_pipeline(self, tmp_path):
        """콜백에서 예외가 발생해도 파이프라인이 계속 실행되는지 확인"""
        # Given
        mock_parser = Mock(spec=BVTParser)
        mock_loader = Mock(spec=SemanticTestCaseLoader)
        mock_summary_gen = Mock(spec=SemanticSummaryGenerator)
        mock_analyzer = Mock(spec=MatchingAnalyzer)
        mock_play_gen = Mock(spec=AutoPlayGenerator)
        mock_updater = Mock(spec=BVTUpdater)
        mock_report_gen = Mock(spec=ReportGenerator)
        
        mock_parser.parse.return_value = []
        mock_loader.load_directory.return_value = []
        mock_summary_gen.generate.return_value = SemanticSummary(
            generated_at="", test_case_summaries=[],
            total_test_cases=0, total_actions=0
        )
        mock_analyzer.analyze.return_value = []
        mock_play_gen.cache_test_case = Mock()
        
        report = MatchingReport(
            generated_at="", total_bvt_items=0, matched_items=0,
            unmatched_items=0, high_confidence_matches=[],
            low_confidence_matches=[], unmatched_bvt_cases=[],
            coverage_percentage=0.0
        )
        mock_report_gen.generate.return_value = report
        mock_report_gen.to_json.return_value = "{}"
        mock_report_gen.to_markdown.return_value = ""
        
        pipeline = IntegrationPipeline(
            bvt_parser=mock_parser,
            tc_loader=mock_loader,
            summary_generator=mock_summary_gen,
            matching_analyzer=mock_analyzer,
            play_generator=mock_play_gen,
            bvt_updater=mock_updater,
            report_generator=mock_report_gen
        )
        
        bvt_file = tmp_path / "test_bvt.csv"
        bvt_file.write_text("dummy")
        
        def failing_callback(stage, message, progress):
            raise RuntimeError("Callback error")
        
        # When
        result = pipeline.run(
            bvt_path=str(bvt_file),
            test_cases_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            dry_run=True,
            progress_callback=failing_callback
        )
        
        # Then: 파이프라인은 성공해야 함
        assert result.success is True


class TestIntegrationPipelineFailureHandling:
    """단계별 실패 처리 테스트
    
    Requirements: 7.4
    """
    
    def test_parsing_failure_returns_partial_result(self, tmp_path):
        """파싱 실패 시 부분 결과를 반환하는지 확인"""
        # Given
        mock_parser = Mock(spec=BVTParser)
        mock_parser.parse.side_effect = BVTParseError("파싱 오류")
        
        pipeline = IntegrationPipeline(bvt_parser=mock_parser)
        
        bvt_file = tmp_path / "test_bvt.csv"
        bvt_file.write_text("invalid")
        
        # When
        result = pipeline.run(
            bvt_path=str(bvt_file),
            test_cases_dir=str(tmp_path),
            output_dir=str(tmp_path / "output")
        )
        
        # Then
        assert result.success is False
        assert result.error_message is not None
        assert "파싱 오류" in result.error_message
    
    def test_matching_failure_returns_partial_result(self, tmp_path):
        """매칭 실패 시 부분 결과를 반환하는지 확인"""
        # Given
        mock_parser = Mock(spec=BVTParser)
        mock_loader = Mock(spec=SemanticTestCaseLoader)
        mock_summary_gen = Mock(spec=SemanticSummaryGenerator)
        mock_analyzer = Mock(spec=MatchingAnalyzer)
        
        mock_parser.parse.return_value = [
            BVTTestCase(
                no=1, category1="", category2="", category3="",
                check="test", test_result="", bts_id="", comment=""
            )
        ]
        mock_loader.load_directory.return_value = []
        mock_summary_gen.generate.return_value = SemanticSummary(
            generated_at="", test_case_summaries=[],
            total_test_cases=0, total_actions=0
        )
        mock_analyzer.analyze.side_effect = RuntimeError("매칭 오류")
        
        pipeline = IntegrationPipeline(
            bvt_parser=mock_parser,
            tc_loader=mock_loader,
            summary_generator=mock_summary_gen,
            matching_analyzer=mock_analyzer
        )
        
        bvt_file = tmp_path / "test_bvt.csv"
        bvt_file.write_text("dummy")
        
        # When
        result = pipeline.run(
            bvt_path=str(bvt_file),
            test_cases_dir=str(tmp_path),
            output_dir=str(tmp_path / "output")
        )
        
        # Then
        assert result.success is False
        assert result.error_message is not None
        assert "매칭 오류" in result.error_message
    
    def test_execution_failure_continues_with_other_tests(self, tmp_path):
        """실행 실패 시 다른 테스트는 계속 진행하는지 확인"""
        # Given
        mock_parser = Mock(spec=BVTParser)
        mock_loader = Mock(spec=SemanticTestCaseLoader)
        mock_summary_gen = Mock(spec=SemanticSummaryGenerator)
        mock_analyzer = Mock(spec=MatchingAnalyzer)
        mock_play_gen = Mock(spec=AutoPlayGenerator)
        mock_updater = Mock(spec=BVTUpdater)
        mock_report_gen = Mock(spec=ReportGenerator)
        
        # 두 개의 BVT 케이스
        bvt_cases = [
            BVTTestCase(
                no=1, category1="", category2="", category3="",
                check="test1", test_result="", bts_id="", comment=""
            ),
            BVTTestCase(
                no=2, category1="", category2="", category3="",
                check="test2", test_result="", bts_id="", comment=""
            )
        ]
        mock_parser.parse.return_value = bvt_cases
        
        # 테스트 케이스
        test_cases = [
            SemanticTestCase(
                name="tc1", created_at="",
                actions=[SemanticAction(timestamp="", action_type="click")],
                json_path=""
            ),
            SemanticTestCase(
                name="tc2", created_at="",
                actions=[SemanticAction(timestamp="", action_type="click")],
                json_path=""
            )
        ]
        mock_loader.load_directory.return_value = test_cases
        
        # 요약
        mock_summary_gen.generate.return_value = SemanticSummary(
            generated_at="",
            test_case_summaries=[
                ActionSummary(test_case_name="tc1", action_count=1),
                ActionSummary(test_case_name="tc2", action_count=1)
            ],
            total_test_cases=2,
            total_actions=2
        )
        
        # 매칭 결과
        match_results = [
            MatchResult(
                bvt_case=bvt_cases[0],
                matched_test_case="tc1",
                action_range=ActionRange(0, 0),
                confidence_score=0.9,
                is_high_confidence=True
            ),
            MatchResult(
                bvt_case=bvt_cases[1],
                matched_test_case="tc2",
                action_range=ActionRange(0, 0),
                confidence_score=0.9,
                is_high_confidence=True
            )
        ]
        mock_analyzer.analyze.return_value = match_results
        
        # 플레이 테스트
        play_tests = [
            PlayTestCase(
                name="play1",
                bvt_reference=BVTReference(1, "", "", "", ""),
                source_test_case="tc1",
                actions=[test_cases[0].actions[0]]
            ),
            PlayTestCase(
                name="play2",
                bvt_reference=BVTReference(2, "", "", "", ""),
                source_test_case="tc2",
                actions=[test_cases[1].actions[0]]
            )
        ]
        mock_play_gen.generate_from_test_case.side_effect = play_tests
        mock_play_gen.cache_test_case = Mock()
        mock_play_gen.save_play_test = Mock()
        
        # 첫 번째 실행은 실패, 두 번째는 성공
        mock_play_gen.execute.side_effect = [
            Exception("실행 오류"),
            PlayTestResult(
                play_test_name="play2",
                bvt_no=2,
                status=TestStatus.PASS,
                executed_actions=1,
                failed_actions=0
            )
        ]
        
        # 업데이터
        mock_updater.update.return_value = bvt_cases
        mock_updater.save.return_value = str(tmp_path / "output" / "bvt.csv")
        
        # 리포트
        report = MatchingReport(
            generated_at="", total_bvt_items=2, matched_items=2,
            unmatched_items=0, high_confidence_matches=match_results,
            low_confidence_matches=[], unmatched_bvt_cases=[],
            coverage_percentage=100.0
        )
        mock_report_gen.generate.return_value = report
        mock_report_gen.to_json.return_value = "{}"
        mock_report_gen.to_markdown.return_value = ""
        
        pipeline = IntegrationPipeline(
            bvt_parser=mock_parser,
            tc_loader=mock_loader,
            summary_generator=mock_summary_gen,
            matching_analyzer=mock_analyzer,
            play_generator=mock_play_gen,
            bvt_updater=mock_updater,
            report_generator=mock_report_gen
        )
        
        bvt_file = tmp_path / "test_bvt.csv"
        bvt_file.write_text("dummy")
        
        # When
        result = pipeline.run(
            bvt_path=str(bvt_file),
            test_cases_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            dry_run=False
        )
        
        # Then: 두 번째 테스트는 실행되어야 함
        assert mock_play_gen.execute.call_count == 2
        # 파이프라인은 성공해야 함 (개별 실패는 로깅만)
        assert result.success is True
    
    def test_file_not_found_returns_error(self, tmp_path):
        """파일이 없을 때 오류를 반환하는지 확인"""
        # Given
        pipeline = IntegrationPipeline()
        
        # When
        result = pipeline.run(
            bvt_path=str(tmp_path / "nonexistent.csv"),
            test_cases_dir=str(tmp_path),
            output_dir=str(tmp_path / "output")
        )
        
        # Then
        assert result.success is False
        assert result.error_message is not None


class TestIntegrationPipelineEndToEnd:
    """통합 테스트 (실제 컴포넌트 사용)"""
    
    def test_full_pipeline_with_sample_data(self, tmp_path):
        """샘플 데이터로 전체 파이프라인 실행"""
        # Given: BVT CSV 파일 생성
        bvt_content = """,No.,Category 1,Category 2,Category 3,Check,,,Test Result (PC),BTS ID,Comment
,1,메인화면,공통 UI,버튼,시작 버튼 클릭 시 게임 시작,,,Not Tested,,
,2,메인화면,공통 UI,텍스트,타이틀 텍스트 표시,,,Not Tested,,
"""
        bvt_file = tmp_path / "test_bvt.csv"
        bvt_file.write_text(bvt_content, encoding='utf-8-sig')
        
        # 테스트 케이스 JSON 파일 생성
        tc_dir = tmp_path / "test_cases"
        tc_dir.mkdir()
        
        tc_data = {
            "name": "main-screen-test",
            "created_at": "2026-01-25T00:00:00",
            "actions": [
                {
                    "timestamp": "2026-01-25T00:00:01",
                    "action_type": "click",
                    "x": 100,
                    "y": 200,
                    "description": "시작 버튼 클릭",
                    "semantic_info": {
                        "intent": "게임 시작",
                        "target_element": "시작 버튼"
                    }
                }
            ]
        }
        tc_file = tc_dir / "main-screen-test.json"
        tc_file.write_text(json.dumps(tc_data, ensure_ascii=False), encoding='utf-8')
        
        output_dir = tmp_path / "output"
        
        # When
        pipeline = IntegrationPipeline()
        result = pipeline.run(
            bvt_path=str(bvt_file),
            test_cases_dir=str(tc_dir),
            output_dir=str(output_dir),
            dry_run=True
        )
        
        # Then
        assert result.success is True
        assert result.matching_report is not None
        assert result.report_json_path is not None
        assert result.report_md_path is not None
        
        # 리포트 파일이 생성되었는지 확인
        assert Path(result.report_json_path).exists()
        assert Path(result.report_md_path).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
