"""
BVT-의미론적 통합 파이프라인

전체 파이프라인을 조율하여 BVT 파싱부터 업데이트까지 실행한다.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List

from .models import (
    PipelineResult,
    MatchingReport,
    BVTTestCase,
    SemanticTestCase,
    SemanticSummary,
    MatchResult,
    PlayTestCase,
    PlayTestResult
)
from .bvt_parser import BVTParser, BVTParseError
from .tc_loader import SemanticTestCaseLoader
from .summary_generator import SemanticSummaryGenerator
from .matching_analyzer import MatchingAnalyzer
from .text_similarity import TextSimilarityCalculator
from .auto_play_generator import AutoPlayGenerator
from .bvt_updater import BVTUpdater
from .report_generator import ReportGenerator


logger = logging.getLogger(__name__)


class PipelineStage:
    """파이프라인 단계 상수"""
    PARSING = "parsing"
    LOADING = "loading"
    SUMMARIZING = "summarizing"
    MATCHING = "matching"
    GENERATING = "generating"
    EXECUTING = "executing"
    UPDATING = "updating"
    REPORTING = "reporting"


class IntegrationPipeline:
    """BVT-의미론적 통합 파이프라인
    
    전체 파이프라인을 조율하여 다음 단계를 순서대로 실행한다:
    1. BVT 파싱
    2. 테스트 케이스 로드
    3. 의미론적 요약 생성
    4. 매칭 분석
    5. 플레이 테스트 생성
    6. 플레이 테스트 실행 (dry_run이 아닌 경우)
    7. BVT 업데이트
    8. 리포트 생성
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    
    def __init__(
        self,
        bvt_parser: Optional[BVTParser] = None,
        tc_loader: Optional[SemanticTestCaseLoader] = None,
        summary_generator: Optional[SemanticSummaryGenerator] = None,
        matching_analyzer: Optional[MatchingAnalyzer] = None,
        play_generator: Optional[AutoPlayGenerator] = None,
        bvt_updater: Optional[BVTUpdater] = None,
        report_generator: Optional[ReportGenerator] = None
    ):
        """파이프라인 초기화
        
        Args:
            bvt_parser: BVT 파서 (None이면 새로 생성)
            tc_loader: 테스트 케이스 로더 (None이면 새로 생성)
            summary_generator: 요약 생성기 (None이면 새로 생성)
            matching_analyzer: 매칭 분석기 (None이면 새로 생성)
            play_generator: 플레이 테스트 생성기 (None이면 새로 생성)
            bvt_updater: BVT 업데이터 (None이면 새로 생성)
            report_generator: 리포트 생성기 (None이면 새로 생성)
        """
        self.bvt_parser = bvt_parser or BVTParser()
        self.tc_loader = tc_loader or SemanticTestCaseLoader()
        self.summary_generator = summary_generator or SemanticSummaryGenerator()
        self.matching_analyzer = matching_analyzer or MatchingAnalyzer(
            TextSimilarityCalculator()
        )
        self.play_generator = play_generator or AutoPlayGenerator(
            tc_loader=self.tc_loader
        )
        self.bvt_updater = bvt_updater or BVTUpdater(self.bvt_parser)
        self.report_generator = report_generator or ReportGenerator()
    
    def run(
        self,
        bvt_path: str,
        test_cases_dir: str,
        output_dir: str = "reports",
        dry_run: bool = False,
        progress_callback: Optional[Callable[[str, str, float], None]] = None
    ) -> PipelineResult:
        """파이프라인 실행
        
        Args:
            bvt_path: BVT CSV 파일 경로
            test_cases_dir: 테스트 케이스 디렉토리 경로
            output_dir: 출력 디렉토리 경로
            dry_run: True이면 분석만 수행 (테스트 실행 안 함)
            progress_callback: 진행 상황 콜백 (stage, message, progress)
                - stage: 현재 단계 이름
                - message: 진행 메시지
                - progress: 진행률 (0.0 ~ 1.0)
            
        Returns:
            PipelineResult 객체
            
        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        start_time = time.time()
        
        # 결과 초기화
        bvt_cases: List[BVTTestCase] = []
        test_cases: List[SemanticTestCase] = []
        summary: Optional[SemanticSummary] = None
        match_results: List[MatchResult] = []
        play_tests: List[PlayTestCase] = []
        play_results: List[PlayTestResult] = []
        matching_report: Optional[MatchingReport] = None
        
        # 출력 경로
        bvt_output_path: Optional[str] = None
        report_json_path: Optional[str] = None
        report_md_path: Optional[str] = None
        play_tests_dir: Optional[str] = None
        
        try:
            # 1. BVT 파싱 (Requirements 7.1)
            self._notify_progress(
                progress_callback, 
                PipelineStage.PARSING, 
                "BVT 파일 파싱 중...", 
                0.0
            )
            bvt_cases = self._parse_bvt(bvt_path)
            logger.info(f"BVT 파싱 완료: {len(bvt_cases)}개 케이스")
            
            # 2. 테스트 케이스 로드 (Requirements 7.1)
            self._notify_progress(
                progress_callback, 
                PipelineStage.LOADING, 
                "테스트 케이스 로드 중...", 
                0.15
            )
            test_cases = self._load_test_cases(test_cases_dir)
            logger.info(f"테스트 케이스 로드 완료: {len(test_cases)}개")
            
            # 3. 의미론적 요약 생성 (Requirements 7.1)
            self._notify_progress(
                progress_callback, 
                PipelineStage.SUMMARIZING, 
                "의미론적 요약 생성 중...", 
                0.25
            )
            summary = self._generate_summary(test_cases)
            logger.info(f"요약 생성 완료: {summary.total_actions}개 액션")
            
            # 4. 매칭 분석 (Requirements 7.1)
            self._notify_progress(
                progress_callback, 
                PipelineStage.MATCHING, 
                "매칭 분석 중...", 
                0.35
            )
            match_results = self._analyze_matching(bvt_cases, summary)
            logger.info(f"매칭 분석 완료: {len(match_results)}개 결과")
            
            # 5. 플레이 테스트 생성 (Requirements 7.1)
            self._notify_progress(
                progress_callback, 
                PipelineStage.GENERATING, 
                "플레이 테스트 생성 중...", 
                0.45
            )
            play_tests = self._generate_play_tests(match_results, test_cases)
            logger.info(f"플레이 테스트 생성 완료: {len(play_tests)}개")
            
            # 플레이 테스트 저장
            if play_tests:
                play_tests_dir = str(Path(output_dir) / "play_tests")
                self._save_play_tests(play_tests, play_tests_dir)
            
            # 6. 플레이 테스트 실행 (dry_run이 아닌 경우) (Requirements 7.3)
            if not dry_run and play_tests:
                self._notify_progress(
                    progress_callback, 
                    PipelineStage.EXECUTING, 
                    "플레이 테스트 실행 중...", 
                    0.55
                )
                play_results = self._execute_play_tests(
                    play_tests, 
                    progress_callback
                )
                logger.info(f"플레이 테스트 실행 완료: {len(play_results)}개 결과")
            else:
                if dry_run:
                    logger.info("Dry-run 모드: 테스트 실행 건너뜀")
            
            # 7. BVT 업데이트 (Requirements 7.1, 7.5)
            self._notify_progress(
                progress_callback, 
                PipelineStage.UPDATING, 
                "BVT 업데이트 중...", 
                0.75
            )
            if play_results:
                updated_bvt_cases = self._update_bvt(bvt_cases, play_results)
                bvt_output_path = self._save_bvt(updated_bvt_cases, output_dir)
                logger.info(f"BVT 업데이트 완료: {bvt_output_path}")
            
            # 8. 리포트 생성 (Requirements 7.1, 7.5)
            self._notify_progress(
                progress_callback, 
                PipelineStage.REPORTING, 
                "리포트 생성 중...", 
                0.85
            )
            matching_report = self._generate_report(match_results)
            report_json_path, report_md_path = self._save_reports(
                matching_report, 
                output_dir
            )
            logger.info(f"리포트 생성 완료: {report_json_path}")
            
            # 완료
            self._notify_progress(
                progress_callback, 
                "complete", 
                "파이프라인 완료", 
                1.0
            )
            
            execution_time = time.time() - start_time
            
            return PipelineResult(
                success=True,
                bvt_output_path=bvt_output_path,
                report_json_path=report_json_path,
                report_md_path=report_md_path,
                play_tests_dir=play_tests_dir,
                matching_report=matching_report,
                error_message=None,
                execution_time=execution_time
            )
            
        except Exception as e:
            # 단계별 실패 처리 (Requirements 7.4)
            execution_time = time.time() - start_time
            error_message = str(e)
            logger.error(f"파이프라인 실패: {error_message}")
            
            # 부분 결과 반환
            if match_results:
                matching_report = self._generate_report(match_results)
                try:
                    report_json_path, report_md_path = self._save_reports(
                        matching_report, 
                        output_dir
                    )
                except Exception:
                    pass
            
            return PipelineResult(
                success=False,
                bvt_output_path=bvt_output_path,
                report_json_path=report_json_path,
                report_md_path=report_md_path,
                play_tests_dir=play_tests_dir,
                matching_report=matching_report,
                error_message=error_message,
                execution_time=execution_time
            )
    
    def _notify_progress(
        self,
        callback: Optional[Callable[[str, str, float], None]],
        stage: str,
        message: str,
        progress: float
    ) -> None:
        """진행 상황 알림
        
        Args:
            callback: 콜백 함수
            stage: 현재 단계
            message: 메시지
            progress: 진행률
        """
        if callback:
            try:
                callback(stage, message, progress)
            except Exception as e:
                logger.warning(f"진행 콜백 오류: {e}")
    
    def _parse_bvt(self, bvt_path: str) -> List[BVTTestCase]:
        """BVT 파일 파싱
        
        Args:
            bvt_path: BVT CSV 파일 경로
            
        Returns:
            BVTTestCase 리스트
            
        Raises:
            BVTParseError: 파싱 실패 시
        """
        return self.bvt_parser.parse(bvt_path)
    
    def _load_test_cases(self, test_cases_dir: str) -> List[SemanticTestCase]:
        """테스트 케이스 로드
        
        Args:
            test_cases_dir: 테스트 케이스 디렉토리 경로
            
        Returns:
            SemanticTestCase 리스트
        """
        return self.tc_loader.load_directory(test_cases_dir)
    
    def _generate_summary(
        self, 
        test_cases: List[SemanticTestCase]
    ) -> SemanticSummary:
        """의미론적 요약 생성
        
        Args:
            test_cases: 테스트 케이스 리스트
            
        Returns:
            SemanticSummary 객체
        """
        return self.summary_generator.generate(test_cases)
    
    def _analyze_matching(
        self,
        bvt_cases: List[BVTTestCase],
        summary: SemanticSummary
    ) -> List[MatchResult]:
        """매칭 분석
        
        Args:
            bvt_cases: BVT 케이스 리스트
            summary: 의미론적 요약
            
        Returns:
            MatchResult 리스트
        """
        return self.matching_analyzer.analyze(bvt_cases, summary)
    
    def _generate_play_tests(
        self,
        match_results: List[MatchResult],
        test_cases: List[SemanticTestCase]
    ) -> List[PlayTestCase]:
        """플레이 테스트 생성
        
        Args:
            match_results: 매칭 결과 리스트
            test_cases: 테스트 케이스 리스트
            
        Returns:
            PlayTestCase 리스트
        """
        # 테스트 케이스를 이름으로 인덱싱
        tc_by_name = {tc.name: tc for tc in test_cases}
        
        # 테스트 케이스 캐시에 추가
        for tc in test_cases:
            self.play_generator.cache_test_case(tc)
        
        play_tests: List[PlayTestCase] = []
        
        for match_result in match_results:
            if not match_result.is_high_confidence:
                continue
            
            if not match_result.matched_test_case:
                continue
            
            # 원본 테스트 케이스 찾기
            source_tc = tc_by_name.get(match_result.matched_test_case)
            if not source_tc:
                logger.warning(
                    f"테스트 케이스를 찾을 수 없음: "
                    f"{match_result.matched_test_case}"
                )
                continue
            
            # 플레이 테스트 생성
            play_test = self.play_generator.generate_from_test_case(
                match_result, 
                source_tc
            )
            if play_test:
                play_tests.append(play_test)
        
        return play_tests
    
    def _save_play_tests(
        self, 
        play_tests: List[PlayTestCase], 
        output_dir: str
    ) -> None:
        """플레이 테스트 저장
        
        Args:
            play_tests: 플레이 테스트 리스트
            output_dir: 출력 디렉토리
        """
        for play_test in play_tests:
            try:
                self.play_generator.save_play_test(play_test, output_dir)
            except Exception as e:
                logger.warning(f"플레이 테스트 저장 실패: {e}")
    
    def _execute_play_tests(
        self,
        play_tests: List[PlayTestCase],
        progress_callback: Optional[Callable[[str, str, float], None]] = None
    ) -> List[PlayTestResult]:
        """플레이 테스트 실행
        
        Args:
            play_tests: 플레이 테스트 리스트
            progress_callback: 진행 콜백
            
        Returns:
            PlayTestResult 리스트
        """
        results: List[PlayTestResult] = []
        total = len(play_tests)
        
        for i, play_test in enumerate(play_tests):
            try:
                # 진행 상황 업데이트
                progress = 0.55 + (0.2 * (i / total))
                self._notify_progress(
                    progress_callback,
                    PipelineStage.EXECUTING,
                    f"테스트 실행 중: {play_test.name} ({i + 1}/{total})",
                    progress
                )
                
                result = self.play_generator.execute(play_test)
                results.append(result)
                
            except Exception as e:
                logger.warning(f"플레이 테스트 실행 실패: {e}")
                continue
        
        return results
    
    def _update_bvt(
        self,
        bvt_cases: List[BVTTestCase],
        play_results: List[PlayTestResult]
    ) -> List[BVTTestCase]:
        """BVT 업데이트
        
        Args:
            bvt_cases: 원본 BVT 케이스 리스트
            play_results: 플레이 테스트 결과 리스트
            
        Returns:
            업데이트된 BVT 케이스 리스트
        """
        return self.bvt_updater.update(bvt_cases, play_results)
    
    def _save_bvt(
        self, 
        bvt_cases: List[BVTTestCase], 
        output_dir: str
    ) -> str:
        """BVT 저장
        
        Args:
            bvt_cases: BVT 케이스 리스트
            output_dir: 출력 디렉토리
            
        Returns:
            저장된 파일 경로
        """
        return self.bvt_updater.save(bvt_cases, output_dir)
    
    def _generate_report(
        self, 
        match_results: List[MatchResult]
    ) -> MatchingReport:
        """리포트 생성
        
        Args:
            match_results: 매칭 결과 리스트
            
        Returns:
            MatchingReport 객체
        """
        return self.report_generator.generate(match_results)
    
    def _save_reports(
        self, 
        report: MatchingReport, 
        output_dir: str
    ) -> tuple:
        """리포트 저장
        
        Args:
            report: 매칭 리포트
            output_dir: 출력 디렉토리
            
        Returns:
            (JSON 파일 경로, Markdown 파일 경로) 튜플
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 리포트 저장
        json_filename = f"matching_report_{timestamp}.json"
        json_path = output_path / json_filename
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(self.report_generator.to_json(report))
        
        # Markdown 리포트 저장
        md_filename = f"matching_report_{timestamp}.md"
        md_path = output_path / md_filename
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self.report_generator.to_markdown(report))
        
        return str(json_path), str(md_path)
