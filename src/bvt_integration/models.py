"""
BVT-Semantic Integration 데이터 모델

Requirements: 1.1, 1.2, 2.4, 3.1, 4.1, 5.1, 6.1
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List


class TestStatus(Enum):
    """테스트 상태 열거형
    
    Requirements: 5.1
    """
    PASS = "PASS"
    FAIL = "Fail"
    BLOCKED = "Block"
    NOT_TESTED = "Not Tested"
    NA = "N/A"


@dataclass
class BVTTestCase:
    """BVT 테스트 케이스
    
    Requirements: 1.1, 1.2
    """
    no: int
    category1: str
    category2: str
    category3: str
    check: str
    test_result: str
    bts_id: str
    comment: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "no": self.no,
            "category1": self.category1,
            "category2": self.category2,
            "category3": self.category3,
            "check": self.check,
            "test_result": self.test_result,
            "bts_id": self.bts_id,
            "comment": self.comment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BVTTestCase':
        """딕셔너리에서 생성"""
        return cls(
            no=data.get("no", 0),
            category1=data.get("category1", ""),
            category2=data.get("category2", ""),
            category3=data.get("category3", ""),
            check=data.get("check", ""),
            test_result=data.get("test_result", "Not Tested"),
            bts_id=data.get("bts_id", ""),
            comment=data.get("comment", "")
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BVTTestCase):
            return False
        return (
            self.no == other.no and
            self.category1 == other.category1 and
            self.category2 == other.category2 and
            self.category3 == other.category3 and
            self.check == other.check and
            self.test_result == other.test_result and
            self.bts_id == other.bts_id and
            self.comment == other.comment
        )


@dataclass
class ActionSummary:
    """단일 테스트 케이스의 액션 요약
    
    Requirements: 2.4
    """
    test_case_name: str
    intents: List[str] = field(default_factory=list)
    target_elements: List[str] = field(default_factory=list)
    screen_states: List[str] = field(default_factory=list)
    action_descriptions: List[str] = field(default_factory=list)
    action_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "test_case_name": self.test_case_name,
            "intents": list(self.intents),
            "target_elements": list(self.target_elements),
            "screen_states": list(self.screen_states),
            "action_descriptions": list(self.action_descriptions),
            "action_count": self.action_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionSummary':
        """딕셔너리에서 생성"""
        return cls(
            test_case_name=data.get("test_case_name", ""),
            intents=list(data.get("intents", [])),
            target_elements=list(data.get("target_elements", [])),
            screen_states=list(data.get("screen_states", [])),
            action_descriptions=list(data.get("action_descriptions", [])),
            action_count=data.get("action_count", 0)
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ActionSummary):
            return False
        return (
            self.test_case_name == other.test_case_name and
            self.intents == other.intents and
            self.target_elements == other.target_elements and
            self.screen_states == other.screen_states and
            self.action_descriptions == other.action_descriptions and
            self.action_count == other.action_count
        )


@dataclass
class SemanticSummary:
    """의미론적 요약 문서
    
    Requirements: 2.4
    """
    generated_at: str
    test_case_summaries: List[ActionSummary] = field(default_factory=list)
    total_test_cases: int = 0
    total_actions: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "generated_at": self.generated_at,
            "test_case_summaries": [s.to_dict() for s in self.test_case_summaries],
            "total_test_cases": self.total_test_cases,
            "total_actions": self.total_actions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticSummary':
        """딕셔너리에서 생성"""
        summaries = [
            ActionSummary.from_dict(s) 
            for s in data.get("test_case_summaries", [])
        ]
        return cls(
            generated_at=data.get("generated_at", ""),
            test_case_summaries=summaries,
            total_test_cases=data.get("total_test_cases", 0),
            total_actions=data.get("total_actions", 0)
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticSummary):
            return False
        return (
            self.generated_at == other.generated_at and
            self.test_case_summaries == other.test_case_summaries and
            self.total_test_cases == other.total_test_cases and
            self.total_actions == other.total_actions
        )


@dataclass
class ActionRange:
    """액션 인덱스 범위
    
    Requirements: 3.1
    """
    start_index: int
    end_index: int
    
    @property
    def length(self) -> int:
        """범위 내 액션 수"""
        return self.end_index - self.start_index + 1
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "start_index": self.start_index,
            "end_index": self.end_index
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionRange':
        """딕셔너리에서 생성"""
        return cls(
            start_index=data.get("start_index", 0),
            end_index=data.get("end_index", 0)
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ActionRange):
            return False
        return (
            self.start_index == other.start_index and
            self.end_index == other.end_index
        )


@dataclass
class BVTReference:
    """BVT 참조 정보
    
    Requirements: 4.1
    """
    no: int
    category1: str
    category2: str
    category3: str
    check: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "no": self.no,
            "category1": self.category1,
            "category2": self.category2,
            "category3": self.category3,
            "check": self.check
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BVTReference':
        """딕셔너리에서 생성"""
        return cls(
            no=data.get("no", 0),
            category1=data.get("category1", ""),
            category2=data.get("category2", ""),
            category3=data.get("category3", ""),
            check=data.get("check", "")
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BVTReference):
            return False
        return (
            self.no == other.no and
            self.category1 == other.category1 and
            self.category2 == other.category2 and
            self.category3 == other.category3 and
            self.check == other.check
        )


@dataclass
class MatchResult:
    """매칭 결과
    
    Requirements: 3.1
    """
    bvt_case: BVTTestCase
    matched_test_case: Optional[str] = None
    action_range: Optional[ActionRange] = None
    confidence_score: float = 0.0
    is_high_confidence: bool = False
    match_details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_matched(self) -> bool:
        """매칭 여부"""
        return self.matched_test_case is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "bvt_case": self.bvt_case.to_dict(),
            "matched_test_case": self.matched_test_case,
            "action_range": self.action_range.to_dict() if self.action_range else None,
            "confidence_score": self.confidence_score,
            "is_high_confidence": self.is_high_confidence,
            "match_details": dict(self.match_details)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchResult':
        """딕셔너리에서 생성"""
        bvt_case = BVTTestCase.from_dict(data.get("bvt_case", {}))
        action_range_data = data.get("action_range")
        action_range = ActionRange.from_dict(action_range_data) if action_range_data else None
        
        return cls(
            bvt_case=bvt_case,
            matched_test_case=data.get("matched_test_case"),
            action_range=action_range,
            confidence_score=data.get("confidence_score", 0.0),
            is_high_confidence=data.get("is_high_confidence", False),
            match_details=dict(data.get("match_details", {}))
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MatchResult):
            return False
        return (
            self.bvt_case == other.bvt_case and
            self.matched_test_case == other.matched_test_case and
            self.action_range == other.action_range and
            self.confidence_score == other.confidence_score and
            self.is_high_confidence == other.is_high_confidence and
            self.match_details == other.match_details
        )


@dataclass
class SemanticAction:
    """의미론적 액션 (간소화된 버전)
    
    기존 SemanticAction과 호환되는 구조로, 
    PlayTestCase에서 사용하기 위한 최소 필드만 포함.
    
    Requirements: 4.1
    """
    timestamp: str
    action_type: str
    x: int = 0
    y: int = 0
    description: str = ""
    screenshot_path: Optional[str] = None
    button: Optional[str] = None
    key: Optional[str] = None
    scroll_dx: Optional[int] = None
    scroll_dy: Optional[int] = None
    screenshot_before_path: Optional[str] = None
    screenshot_after_path: Optional[str] = None
    click_region_crop_path: Optional[str] = None
    ui_state_hash_before: Optional[str] = None
    ui_state_hash_after: Optional[str] = None
    semantic_info: Dict[str, Any] = field(default_factory=dict)
    screen_transition: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "x": self.x,
            "y": self.y,
            "description": self.description,
            "screenshot_path": self.screenshot_path,
            "button": self.button,
            "key": self.key,
            "scroll_dx": self.scroll_dx,
            "scroll_dy": self.scroll_dy,
            "screenshot_before_path": self.screenshot_before_path,
            "screenshot_after_path": self.screenshot_after_path,
            "click_region_crop_path": self.click_region_crop_path,
            "ui_state_hash_before": self.ui_state_hash_before,
            "ui_state_hash_after": self.ui_state_hash_after,
            "semantic_info": dict(self.semantic_info),
            "screen_transition": dict(self.screen_transition)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticAction':
        """딕셔너리에서 생성"""
        return cls(
            timestamp=data.get("timestamp", ""),
            action_type=data.get("action_type", ""),
            x=data.get("x", 0),
            y=data.get("y", 0),
            description=data.get("description", ""),
            screenshot_path=data.get("screenshot_path"),
            button=data.get("button"),
            key=data.get("key"),
            scroll_dx=data.get("scroll_dx"),
            scroll_dy=data.get("scroll_dy"),
            screenshot_before_path=data.get("screenshot_before_path"),
            screenshot_after_path=data.get("screenshot_after_path"),
            click_region_crop_path=data.get("click_region_crop_path"),
            ui_state_hash_before=data.get("ui_state_hash_before"),
            ui_state_hash_after=data.get("ui_state_hash_after"),
            semantic_info=dict(data.get("semantic_info", {})),
            screen_transition=dict(data.get("screen_transition", {}))
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticAction):
            return False
        return (
            self.timestamp == other.timestamp and
            self.action_type == other.action_type and
            self.x == other.x and
            self.y == other.y and
            self.description == other.description and
            self.screenshot_path == other.screenshot_path and
            self.button == other.button and
            self.key == other.key and
            self.scroll_dx == other.scroll_dx and
            self.scroll_dy == other.scroll_dy and
            self.screenshot_before_path == other.screenshot_before_path and
            self.screenshot_after_path == other.screenshot_after_path and
            self.click_region_crop_path == other.click_region_crop_path and
            self.ui_state_hash_before == other.ui_state_hash_before and
            self.ui_state_hash_after == other.ui_state_hash_after and
            self.semantic_info == other.semantic_info and
            self.screen_transition == other.screen_transition
        )


@dataclass
class SemanticTestCase:
    """의미론적 테스트 케이스
    
    Requirements: 2.4
    """
    name: str
    created_at: str
    actions: List[SemanticAction] = field(default_factory=list)
    json_path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "actions": [a.to_dict() for a in self.actions],
            "json_path": self.json_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticTestCase':
        """딕셔너리에서 생성"""
        actions = [
            SemanticAction.from_dict(a) 
            for a in data.get("actions", [])
        ]
        return cls(
            name=data.get("name", ""),
            created_at=data.get("created_at", ""),
            actions=actions,
            json_path=data.get("json_path", "")
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticTestCase):
            return False
        return (
            self.name == other.name and
            self.created_at == other.created_at and
            self.actions == other.actions and
            self.json_path == other.json_path
        )


@dataclass
class PlayTestCase:
    """플레이 테스트 케이스
    
    Requirements: 4.1
    """
    name: str
    bvt_reference: BVTReference
    source_test_case: str
    actions: List[SemanticAction] = field(default_factory=list)
    created_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "bvt_reference": self.bvt_reference.to_dict(),
            "source_test_case": self.source_test_case,
            "actions": [a.to_dict() for a in self.actions],
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayTestCase':
        """딕셔너리에서 생성"""
        bvt_ref = BVTReference.from_dict(data.get("bvt_reference", {}))
        actions = [
            SemanticAction.from_dict(a) 
            for a in data.get("actions", [])
        ]
        return cls(
            name=data.get("name", ""),
            bvt_reference=bvt_ref,
            source_test_case=data.get("source_test_case", ""),
            actions=actions,
            created_at=data.get("created_at", "")
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlayTestCase):
            return False
        return (
            self.name == other.name and
            self.bvt_reference == other.bvt_reference and
            self.source_test_case == other.source_test_case and
            self.actions == other.actions and
            self.created_at == other.created_at
        )


@dataclass
class PlayTestResult:
    """플레이 테스트 결과
    
    Requirements: 5.1
    """
    play_test_name: str
    bvt_no: int
    status: TestStatus
    executed_actions: int = 0
    failed_actions: int = 0
    screenshots: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "play_test_name": self.play_test_name,
            "bvt_no": self.bvt_no,
            "status": self.status.value,
            "executed_actions": self.executed_actions,
            "failed_actions": self.failed_actions,
            "screenshots": list(self.screenshots),
            "error_message": self.error_message,
            "execution_time": self.execution_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayTestResult':
        """딕셔너리에서 생성"""
        status_str = data.get("status", "Not Tested")
        try:
            status = TestStatus(status_str)
        except ValueError:
            status = TestStatus.NOT_TESTED
        
        return cls(
            play_test_name=data.get("play_test_name", ""),
            bvt_no=data.get("bvt_no", 0),
            status=status,
            executed_actions=data.get("executed_actions", 0),
            failed_actions=data.get("failed_actions", 0),
            screenshots=list(data.get("screenshots", [])),
            error_message=data.get("error_message"),
            execution_time=data.get("execution_time", 0.0)
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlayTestResult):
            return False
        return (
            self.play_test_name == other.play_test_name and
            self.bvt_no == other.bvt_no and
            self.status == other.status and
            self.executed_actions == other.executed_actions and
            self.failed_actions == other.failed_actions and
            self.screenshots == other.screenshots and
            self.error_message == other.error_message and
            self.execution_time == other.execution_time
        )


@dataclass
class MatchingReport:
    """매칭 리포트
    
    Requirements: 6.1
    """
    generated_at: str
    total_bvt_items: int = 0
    matched_items: int = 0
    unmatched_items: int = 0
    high_confidence_matches: List[MatchResult] = field(default_factory=list)
    low_confidence_matches: List[MatchResult] = field(default_factory=list)
    unmatched_bvt_cases: List[BVTTestCase] = field(default_factory=list)
    coverage_percentage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "generated_at": self.generated_at,
            "total_bvt_items": self.total_bvt_items,
            "matched_items": self.matched_items,
            "unmatched_items": self.unmatched_items,
            "high_confidence_matches": [m.to_dict() for m in self.high_confidence_matches],
            "low_confidence_matches": [m.to_dict() for m in self.low_confidence_matches],
            "unmatched_bvt_cases": [c.to_dict() for c in self.unmatched_bvt_cases],
            "coverage_percentage": self.coverage_percentage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchingReport':
        """딕셔너리에서 생성"""
        high_matches = [
            MatchResult.from_dict(m) 
            for m in data.get("high_confidence_matches", [])
        ]
        low_matches = [
            MatchResult.from_dict(m) 
            for m in data.get("low_confidence_matches", [])
        ]
        unmatched = [
            BVTTestCase.from_dict(c) 
            for c in data.get("unmatched_bvt_cases", [])
        ]
        
        return cls(
            generated_at=data.get("generated_at", ""),
            total_bvt_items=data.get("total_bvt_items", 0),
            matched_items=data.get("matched_items", 0),
            unmatched_items=data.get("unmatched_items", 0),
            high_confidence_matches=high_matches,
            low_confidence_matches=low_matches,
            unmatched_bvt_cases=unmatched,
            coverage_percentage=data.get("coverage_percentage", 0.0)
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MatchingReport):
            return False
        return (
            self.generated_at == other.generated_at and
            self.total_bvt_items == other.total_bvt_items and
            self.matched_items == other.matched_items and
            self.unmatched_items == other.unmatched_items and
            self.high_confidence_matches == other.high_confidence_matches and
            self.low_confidence_matches == other.low_confidence_matches and
            self.unmatched_bvt_cases == other.unmatched_bvt_cases and
            self.coverage_percentage == other.coverage_percentage
        )


@dataclass
class PipelineResult:
    """파이프라인 결과
    
    Requirements: 7.1
    """
    success: bool
    bvt_output_path: Optional[str] = None
    report_json_path: Optional[str] = None
    report_md_path: Optional[str] = None
    play_tests_dir: Optional[str] = None
    matching_report: Optional[MatchingReport] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "success": self.success,
            "bvt_output_path": self.bvt_output_path,
            "report_json_path": self.report_json_path,
            "report_md_path": self.report_md_path,
            "play_tests_dir": self.play_tests_dir,
            "matching_report": self.matching_report.to_dict() if self.matching_report else None,
            "error_message": self.error_message,
            "execution_time": self.execution_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineResult':
        """딕셔너리에서 생성"""
        report_data = data.get("matching_report")
        matching_report = MatchingReport.from_dict(report_data) if report_data else None
        
        return cls(
            success=data.get("success", False),
            bvt_output_path=data.get("bvt_output_path"),
            report_json_path=data.get("report_json_path"),
            report_md_path=data.get("report_md_path"),
            play_tests_dir=data.get("play_tests_dir"),
            matching_report=matching_report,
            error_message=data.get("error_message"),
            execution_time=data.get("execution_time", 0.0)
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PipelineResult):
            return False
        return (
            self.success == other.success and
            self.bvt_output_path == other.bvt_output_path and
            self.report_json_path == other.report_json_path and
            self.report_md_path == other.report_md_path and
            self.play_tests_dir == other.play_tests_dir and
            self.matching_report == other.matching_report and
            self.error_message == other.error_message and
            self.execution_time == other.execution_time
        )
