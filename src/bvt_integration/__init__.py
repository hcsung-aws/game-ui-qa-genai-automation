"""
BVT-Semantic Test Integration 모듈

BVT 테스트 데이터와 의미론적 테스트 케이스를 연결하여
자동화된 QA 파이프라인을 구축하는 시스템이다.
"""

__version__ = "0.1.0"

from .models import (
    BVTTestCase,
    TestStatus,
    ActionSummary,
    SemanticSummary,
    ActionRange,
    BVTReference,
    MatchResult,
    SemanticAction,
    SemanticTestCase,
    PlayTestCase,
    PlayTestResult,
    MatchingReport,
    PipelineResult,
)

from .bvt_parser import BVTParser, BVTParseError
from .tc_loader import SemanticTestCaseLoader
from .summary_generator import SemanticSummaryGenerator

__all__ = [
    # Models
    "BVTTestCase",
    "TestStatus",
    "ActionSummary",
    "SemanticSummary",
    "ActionRange",
    "BVTReference",
    "MatchResult",
    "SemanticAction",
    "SemanticTestCase",
    "PlayTestCase",
    "PlayTestResult",
    "MatchingReport",
    "PipelineResult",
    # Parser
    "BVTParser",
    "BVTParseError",
    # Loader
    "SemanticTestCaseLoader",
    # Summary Generator
    "SemanticSummaryGenerator",
]
