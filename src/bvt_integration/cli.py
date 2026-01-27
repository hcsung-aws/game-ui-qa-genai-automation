"""
BVT-Semantic Integration CLI

명령줄 인터페이스를 통해 BVT-의미론적 통합 파이프라인을 실행한다.

Requirements: 7.1, 7.3

사용 예시:
    # 기본 실행
    python -m src.bvt_integration.cli --bvt-path bvt.csv --test-cases-dir test_cases
    
    # Dry-run 모드 (분석만 수행)
    python -m src.bvt_integration.cli --bvt-path bvt.csv --test-cases-dir test_cases --dry-run
    
    # 출력 디렉토리 지정
    python -m src.bvt_integration.cli --bvt-path bvt.csv --test-cases-dir test_cases --output-dir reports
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .pipeline import IntegrationPipeline, PipelineStage
from . import __version__


def setup_logging(verbose: bool = False) -> None:
    """로깅 설정
    
    Args:
        verbose: True이면 DEBUG 레벨, False이면 INFO 레벨
    """
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def create_progress_callback(quiet: bool = False):
    """진행 상황 콜백 생성
    
    Args:
        quiet: True이면 진행 상황 출력 안 함
        
    Returns:
        콜백 함수 또는 None
    """
    if quiet:
        return None
    
    stage_names = {
        PipelineStage.PARSING: "BVT 파싱",
        PipelineStage.LOADING: "테스트 케이스 로드",
        PipelineStage.SUMMARIZING: "요약 생성",
        PipelineStage.MATCHING: "매칭 분석",
        PipelineStage.GENERATING: "플레이 테스트 생성",
        PipelineStage.EXECUTING: "테스트 실행",
        PipelineStage.UPDATING: "BVT 업데이트",
        PipelineStage.REPORTING: "리포트 생성",
        "complete": "완료"
    }
    
    def callback(stage: str, message: str, progress: float) -> None:
        stage_name = stage_names.get(stage, stage)
        progress_pct = int(progress * 100)
        print(f"[{progress_pct:3d}%] {stage_name}: {message}")
    
    return callback


def validate_paths(bvt_path: str, test_cases_dir: str) -> bool:
    """경로 유효성 검증
    
    Args:
        bvt_path: BVT 파일 경로
        test_cases_dir: 테스트 케이스 디렉토리 경로
        
    Returns:
        유효하면 True, 아니면 False
    """
    bvt_file = Path(bvt_path)
    if not bvt_file.exists():
        print(f"오류: BVT 파일을 찾을 수 없습니다: {bvt_path}", file=sys.stderr)
        return False
    
    if not bvt_file.is_file():
        print(f"오류: BVT 경로가 파일이 아닙니다: {bvt_path}", file=sys.stderr)
        return False
    
    tc_dir = Path(test_cases_dir)
    if not tc_dir.exists():
        print(f"오류: 테스트 케이스 디렉토리를 찾을 수 없습니다: {test_cases_dir}", file=sys.stderr)
        return False
    
    if not tc_dir.is_dir():
        print(f"오류: 테스트 케이스 경로가 디렉토리가 아닙니다: {test_cases_dir}", file=sys.stderr)
        return False
    
    return True


def print_result_summary(result) -> None:
    """결과 요약 출력
    
    Args:
        result: PipelineResult 객체
    """
    print("\n" + "=" * 60)
    print("파이프라인 실행 결과")
    print("=" * 60)
    
    if result.success:
        print("상태: 성공")
    else:
        print(f"상태: 실패 - {result.error_message}")
    
    print(f"실행 시간: {result.execution_time:.2f}초")
    
    if result.matching_report:
        report = result.matching_report
        print(f"\n매칭 결과:")
        print(f"  - 총 BVT 항목: {report.total_bvt_items}")
        print(f"  - 매칭된 항목: {report.matched_items}")
        print(f"  - 미매칭 항목: {report.unmatched_items}")
        print(f"  - 커버리지: {report.coverage_percentage:.1f}%")
    
    print(f"\n출력 파일:")
    if result.bvt_output_path:
        print(f"  - BVT 파일: {result.bvt_output_path}")
    if result.report_json_path:
        print(f"  - JSON 리포트: {result.report_json_path}")
    if result.report_md_path:
        print(f"  - Markdown 리포트: {result.report_md_path}")
    if result.play_tests_dir:
        print(f"  - 플레이 테스트: {result.play_tests_dir}")
    
    print("=" * 60)


def create_parser() -> argparse.ArgumentParser:
    """ArgumentParser 생성
    
    Returns:
        설정된 ArgumentParser 객체
    """
    parser = argparse.ArgumentParser(
        prog="bvt-integration",
        description="BVT-Semantic Test Integration Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 실행 (분석 + 테스트 실행)
  python -m src.bvt_integration.cli --bvt-path bvt.csv --test-cases-dir test_cases

  # Dry-run 모드 (분석만 수행, 테스트 실행 안 함)
  python -m src.bvt_integration.cli --bvt-path bvt.csv --test-cases-dir test_cases --dry-run

  # 출력 디렉토리 지정
  python -m src.bvt_integration.cli --bvt-path bvt.csv --test-cases-dir test_cases -o reports

  # 상세 로그 출력
  python -m src.bvt_integration.cli --bvt-path bvt.csv --test-cases-dir test_cases -v
        """
    )
    
    # 필수 인자
    parser.add_argument(
        "--bvt-path",
        required=True,
        help="BVT CSV 파일 경로"
    )
    
    parser.add_argument(
        "--test-cases-dir",
        required=True,
        help="테스트 케이스 디렉토리 경로"
    )
    
    # 선택 인자
    parser.add_argument(
        "-o", "--output-dir",
        default="reports",
        help="출력 디렉토리 경로 (기본값: reports)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="분석만 수행하고 테스트는 실행하지 않음"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="상세 로그 출력"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="진행 상황 출력 안 함"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    return parser


def main(args: Optional[list] = None) -> int:
    """CLI 메인 함수
    
    Args:
        args: 명령줄 인자 리스트 (None이면 sys.argv 사용)
        
    Returns:
        종료 코드 (0: 성공, 1: 실패)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    # 로깅 설정
    setup_logging(parsed_args.verbose)
    logger = logging.getLogger(__name__)
    
    # 경로 검증
    if not validate_paths(parsed_args.bvt_path, parsed_args.test_cases_dir):
        return 1
    
    # 진행 콜백 생성
    progress_callback = create_progress_callback(parsed_args.quiet)
    
    # 파이프라인 실행
    logger.info("BVT-Semantic Integration Pipeline 시작")
    logger.info(f"BVT 파일: {parsed_args.bvt_path}")
    logger.info(f"테스트 케이스 디렉토리: {parsed_args.test_cases_dir}")
    logger.info(f"출력 디렉토리: {parsed_args.output_dir}")
    logger.info(f"Dry-run 모드: {parsed_args.dry_run}")
    
    try:
        pipeline = IntegrationPipeline()
        result = pipeline.run(
            bvt_path=parsed_args.bvt_path,
            test_cases_dir=parsed_args.test_cases_dir,
            output_dir=parsed_args.output_dir,
            dry_run=parsed_args.dry_run,
            progress_callback=progress_callback
        )
        
        # 결과 출력
        if not parsed_args.quiet:
            print_result_summary(result)
        
        if result.success:
            logger.info("파이프라인 실행 완료")
            return 0
        else:
            logger.error(f"파이프라인 실패: {result.error_message}")
            return 1
            
    except Exception as e:
        logger.exception(f"예기치 않은 오류: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
