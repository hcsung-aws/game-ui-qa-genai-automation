"""
BVT-Semantic Test Integration 모듈

BVT 테스트 데이터와 의미론적 테스트 케이스를 연결하여
자동화된 QA 파이프라인을 구축하는 시스템이다.

주요 기능:
1. BVT 파싱: CSV 형식의 BVT 문서를 구조화된 객체로 변환
2. 의미론적 요약 생성: 녹화된 테스트 케이스들의 의미론적 정보를 종합
3. 매칭 분석: BVT 항목과 테스트 케이스 간의 연관관계 분석
4. 자동 플레이 테스트 생성: 매칭된 데이터를 바탕으로 재생 가능한 테스트 케이스 생성
5. BVT 업데이트: 테스트 결과를 반영한 새로운 BVT 문서 생성

사용 예시:
    from src.bvt_integration import IntegrationPipeline
    
    pipeline = IntegrationPipeline()
    result = pipeline.run(
        bvt_path="bvt_samples/BVT_example.csv",
        test_cases_dir="test_cases",
        output_dir="reports",
        dry_run=True
    )
"""

__version__ = "1.0.0"
__author__ = "QA Automation Team"

# Data Models
from .models import (
    # Core Models
    BVTTestCase,
    TestStatus,
    SemanticAction,
    SemanticTestCase,
    # Summary Models
    ActionSummary,
    SemanticSummary,
    # Matching Models
    ActionRange,
    BVTReference,
    MatchResult,
    # Play Test Models
    PlayTestCase,
    PlayTestResult,
    # Report Models
    MatchingReport,
    PipelineResult,
)

# BVT Parser
from .bvt_parser import BVTParser, BVTParseError

# Test Case Loader
from .tc_loader import SemanticTestCaseLoader

# Summary Generator
from .summary_generator import SemanticSummaryGenerator

# Text Similarity
from .text_similarity import TextSimilarityCalculator

# Matching Analyzer
from .matching_analyzer import MatchingAnalyzer, HIGH_CONFIDENCE_THRESHOLD

# Auto Play Generator
from .auto_play_generator import AutoPlayGenerator

# BVT Updater
from .bvt_updater import BVTUpdater

# Report Generator
from .report_generator import ReportGenerator

# Integration Pipeline
from .pipeline import IntegrationPipeline, PipelineStage

# CLI
from .cli import main as cli_main, create_parser as cli_create_parser

__all__ = [
    # Version Info
    "__version__",
    "__author__",
    
    # Data Models - Core
    "BVTTestCase",
    "TestStatus",
    "SemanticAction",
    "SemanticTestCase",
    
    # Data Models - Summary
    "ActionSummary",
    "SemanticSummary",
    
    # Data Models - Matching
    "ActionRange",
    "BVTReference",
    "MatchResult",
    
    # Data Models - Play Test
    "PlayTestCase",
    "PlayTestResult",
    
    # Data Models - Report
    "MatchingReport",
    "PipelineResult",
    
    # BVT Parser
    "BVTParser",
    "BVTParseError",
    
    # Test Case Loader
    "SemanticTestCaseLoader",
    
    # Summary Generator
    "SemanticSummaryGenerator",
    
    # Text Similarity
    "TextSimilarityCalculator",
    
    # Matching Analyzer
    "MatchingAnalyzer",
    "HIGH_CONFIDENCE_THRESHOLD",
    
    # Auto Play Generator
    "AutoPlayGenerator",
    
    # BVT Updater
    "BVTUpdater",
    
    # Report Generator
    "ReportGenerator",
    
    # Integration Pipeline
    "IntegrationPipeline",
    "PipelineStage",
    
    # CLI
    "cli_main",
    "cli_create_parser",
]
