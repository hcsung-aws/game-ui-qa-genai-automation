"""
AccuracyTracker - 테스트 재실행 정확도 추적기

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ActionExecutionResult:
    """액션 실행 결과 데이터 클래스
    
    Requirements: 13.2, 13.3, 13.4
    
    Attributes:
        action_id: 액션 고유 식별자
        timestamp: 실행 시간
        success: 성공 여부
        method: 매칭 방법 ('direct', 'semantic', 'manual', 'failed')
        original_coords: 원래 좌표
        actual_coords: 실제 실행 좌표
        coordinate_change: 좌표 변경량 (dx, dy)
        execution_time: 실행 소요 시간 (초)
        failure_reason: 실패 원인 (실패 시)
        screen_transition_matched: 화면 전환 일치 여부
    """
    action_id: str
    timestamp: str
    success: bool
    method: str  # 'direct', 'semantic', 'manual', 'failed'
    original_coords: Tuple[int, int] = (0, 0)
    actual_coords: Optional[Tuple[int, int]] = None
    coordinate_change: Optional[Tuple[int, int]] = None
    execution_time: float = 0.0
    failure_reason: str = ""
    screen_transition_matched: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "action_id": self.action_id,
            "timestamp": self.timestamp,
            "success": self.success,
            "method": self.method,
            "original_coords": list(self.original_coords) if self.original_coords else None,
            "actual_coords": list(self.actual_coords) if self.actual_coords else None,
            "coordinate_change": list(self.coordinate_change) if self.coordinate_change else None,
            "execution_time": self.execution_time,
            "failure_reason": self.failure_reason,
            "screen_transition_matched": self.screen_transition_matched
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionExecutionResult':
        """딕셔너리에서 생성"""
        return cls(
            action_id=data.get("action_id", ""),
            timestamp=data.get("timestamp", ""),
            success=data.get("success", False),
            method=data.get("method", "failed"),
            original_coords=tuple(data["original_coords"]) if data.get("original_coords") else (0, 0),
            actual_coords=tuple(data["actual_coords"]) if data.get("actual_coords") else None,
            coordinate_change=tuple(data["coordinate_change"]) if data.get("coordinate_change") else None,
            execution_time=data.get("execution_time", 0.0),
            failure_reason=data.get("failure_reason", ""),
            screen_transition_matched=data.get("screen_transition_matched", True)
        )


@dataclass
class AccuracyStatistics:
    """정확도 통계 데이터 클래스
    
    Requirements: 13.5, 13.6
    
    Attributes:
        total_actions: 전체 액션 수
        success_count: 성공 횟수
        failure_count: 실패 횟수
        success_rate: 성공률 (0.0 ~ 1.0)
        direct_match_count: 직접 매칭 횟수
        semantic_match_count: 의미론적 매칭 횟수
        manual_match_count: 수동 매칭 횟수
        direct_match_rate: 직접 매칭률
        semantic_match_rate: 의미론적 매칭률
        avg_coordinate_change: 평균 좌표 변경 거리
        avg_execution_time: 평균 실행 시간
        failure_reasons: 실패 원인 분포
        transition_match_count: 화면 전환 일치 횟수
        transition_mismatch_count: 화면 전환 불일치 횟수
    """
    total_actions: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    direct_match_count: int = 0
    semantic_match_count: int = 0
    manual_match_count: int = 0
    direct_match_rate: float = 0.0
    semantic_match_rate: float = 0.0
    avg_coordinate_change: float = 0.0
    avg_execution_time: float = 0.0
    failure_reasons: Dict[str, int] = field(default_factory=dict)
    transition_match_count: int = 0
    transition_mismatch_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "total_actions": self.total_actions,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "direct_match_count": self.direct_match_count,
            "semantic_match_count": self.semantic_match_count,
            "manual_match_count": self.manual_match_count,
            "direct_match_rate": self.direct_match_rate,
            "semantic_match_rate": self.semantic_match_rate,
            "avg_coordinate_change": self.avg_coordinate_change,
            "avg_execution_time": self.avg_execution_time,
            "failure_reasons": self.failure_reasons,
            "transition_match_count": self.transition_match_count,
            "transition_mismatch_count": self.transition_mismatch_count
        }


class AccuracyTracker:
    """정확도 추적기
    
    테스트 재실행 중 각 액션의 성공/실패를 추적하고 통계를 계산한다.
    
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
    """
    
    def __init__(self, test_case_name: str, data_dir: str = "accuracy_data"):
        """
        Args:
            test_case_name: 테스트 케이스 이름
            data_dir: 정확도 데이터 저장 디렉토리
        """
        self.test_case_name = test_case_name
        self.data_dir = data_dir
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.results: List[ActionExecutionResult] = []
        self._action_counter = 0
        
        # 데이터 디렉토리 생성
        self._ensure_data_dir()
        
        logger.info(f"AccuracyTracker 초기화: test_case={test_case_name}, session={self.session_id}")
    
    def _ensure_data_dir(self):
        """데이터 디렉토리 생성"""
        test_case_dir = os.path.join(self.data_dir, self.test_case_name)
        os.makedirs(test_case_dir, exist_ok=True)
    
    def start_session(self) -> str:
        """새 실행 세션 시작
        
        Requirements: 13.1
        
        Returns:
            세션 ID
        """
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.results = []
        self._action_counter = 0
        logger.info(f"새 세션 시작: {self.session_id}")
        return self.session_id
    
    def record_success(self, action_id: str, method: str,
                      original_coords: Tuple[int, int],
                      actual_coords: Optional[Tuple[int, int]] = None,
                      execution_time: float = 0.0,
                      screen_transition_matched: bool = True) -> ActionExecutionResult:
        """성공 기록
        
        Requirements: 13.2, 13.3
        
        Args:
            action_id: 액션 ID
            method: 매칭 방법 ('direct', 'semantic', 'manual')
            original_coords: 원래 좌표
            actual_coords: 실제 실행 좌표
            execution_time: 실행 소요 시간
            screen_transition_matched: 화면 전환 일치 여부
            
        Returns:
            ActionExecutionResult 객체
        """
        self._action_counter += 1
        
        # 좌표 변경 계산
        coordinate_change = None
        if actual_coords and original_coords:
            coordinate_change = (
                actual_coords[0] - original_coords[0],
                actual_coords[1] - original_coords[1]
            )
        
        result = ActionExecutionResult(
            action_id=action_id or f"action_{self._action_counter:04d}",
            timestamp=datetime.now().isoformat(),
            success=True,
            method=method,
            original_coords=original_coords,
            actual_coords=actual_coords or original_coords,
            coordinate_change=coordinate_change,
            execution_time=execution_time,
            failure_reason="",
            screen_transition_matched=screen_transition_matched
        )
        
        self.results.append(result)
        logger.debug(f"성공 기록: {result.action_id}, method={method}")
        
        return result
    
    def record_failure(self, action_id: str, reason: str,
                      original_coords: Tuple[int, int],
                      execution_time: float = 0.0) -> ActionExecutionResult:
        """실패 기록
        
        Requirements: 13.2
        
        Args:
            action_id: 액션 ID
            reason: 실패 원인
            original_coords: 원래 좌표
            execution_time: 실행 소요 시간
            
        Returns:
            ActionExecutionResult 객체
        """
        self._action_counter += 1
        
        result = ActionExecutionResult(
            action_id=action_id or f"action_{self._action_counter:04d}",
            timestamp=datetime.now().isoformat(),
            success=False,
            method='failed',
            original_coords=original_coords,
            actual_coords=None,
            coordinate_change=None,
            execution_time=execution_time,
            failure_reason=reason,
            screen_transition_matched=False
        )
        
        self.results.append(result)
        logger.debug(f"실패 기록: {result.action_id}, reason={reason}")
        
        return result

    
    def calculate_statistics(self) -> AccuracyStatistics:
        """통계 계산
        
        Requirements: 13.5, 13.6
        
        Returns:
            AccuracyStatistics 객체 (성공률, 매칭 방법 비율, 평균 좌표 변경 거리 등)
        """
        stats = AccuracyStatistics()
        
        if not self.results:
            return stats
        
        total = len(self.results)
        stats.total_actions = total
        
        # 성공/실패 카운트
        stats.success_count = sum(1 for r in self.results if r.success)
        stats.failure_count = total - stats.success_count
        stats.success_rate = stats.success_count / total if total > 0 else 0.0
        
        # 매칭 방법별 카운트
        stats.direct_match_count = sum(1 for r in self.results if r.method == 'direct')
        stats.semantic_match_count = sum(1 for r in self.results if r.method == 'semantic')
        stats.manual_match_count = sum(1 for r in self.results if r.method == 'manual')
        
        # 매칭 방법 비율 (성공한 것 중에서)
        if stats.success_count > 0:
            stats.direct_match_rate = stats.direct_match_count / stats.success_count
            stats.semantic_match_rate = stats.semantic_match_count / stats.success_count
        
        # 평균 좌표 변경 거리 (의미론적 매칭에서만)
        coord_changes = []
        for r in self.results:
            if r.coordinate_change is not None:
                dx, dy = r.coordinate_change
                distance = (dx**2 + dy**2) ** 0.5
                coord_changes.append(distance)
        
        stats.avg_coordinate_change = sum(coord_changes) / len(coord_changes) if coord_changes else 0.0
        
        # 평균 실행 시간
        execution_times = [r.execution_time for r in self.results if r.execution_time > 0]
        stats.avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        # 실패 원인 분포
        failure_reasons: Dict[str, int] = {}
        for r in self.results:
            if not r.success and r.failure_reason:
                reason = r.failure_reason
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        stats.failure_reasons = failure_reasons
        
        # 화면 전환 일치/불일치 카운트
        stats.transition_match_count = sum(1 for r in self.results if r.screen_transition_matched)
        stats.transition_mismatch_count = total - stats.transition_match_count
        
        return stats
    
    def get_results(self) -> List[ActionExecutionResult]:
        """실행 결과 목록 반환
        
        Returns:
            ActionExecutionResult 리스트
        """
        return self.results
    
    def get_session_id(self) -> str:
        """현재 세션 ID 반환
        
        Returns:
            세션 ID 문자열
        """
        return self.session_id
    
    def save_session(self) -> str:
        """세션 데이터 저장
        
        Requirements: 13.1
        
        Returns:
            저장된 파일 경로
        """
        test_case_dir = os.path.join(self.data_dir, self.test_case_name)
        os.makedirs(test_case_dir, exist_ok=True)
        
        # 결과 파일 저장
        results_path = os.path.join(test_case_dir, f"{self.session_id}_results.json")
        results_data = {
            "test_case_name": self.test_case_name,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.results]
        }
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        # 통계 파일 저장
        stats_path = os.path.join(test_case_dir, f"{self.session_id}_stats.json")
        stats = self.calculate_statistics()
        stats_data = {
            "test_case_name": self.test_case_name,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "statistics": stats.to_dict()
        }
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"세션 데이터 저장: {results_path}")
        
        return results_path
    
    def load_session(self, session_id: str) -> bool:
        """세션 데이터 로드
        
        Args:
            session_id: 로드할 세션 ID
            
        Returns:
            성공 여부
        """
        test_case_dir = os.path.join(self.data_dir, self.test_case_name)
        results_path = os.path.join(test_case_dir, f"{session_id}_results.json")
        
        if not os.path.exists(results_path):
            logger.warning(f"세션 파일을 찾을 수 없음: {results_path}")
            return False
        
        try:
            with open(results_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.session_id = data.get("session_id", session_id)
            self.results = [
                ActionExecutionResult.from_dict(r) 
                for r in data.get("results", [])
            ]
            
            logger.info(f"세션 로드 완료: {session_id}, {len(self.results)}개 결과")
            return True
            
        except Exception as e:
            logger.error(f"세션 로드 실패: {e}")
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """저장된 세션 목록 반환
        
        Returns:
            세션 정보 리스트 [{session_id, timestamp, total_actions, success_rate}, ...]
        """
        test_case_dir = os.path.join(self.data_dir, self.test_case_name)
        
        if not os.path.exists(test_case_dir):
            return []
        
        sessions = []
        
        for filename in os.listdir(test_case_dir):
            if filename.endswith("_stats.json"):
                stats_path = os.path.join(test_case_dir, filename)
                try:
                    with open(stats_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    stats = data.get("statistics", {})
                    sessions.append({
                        "session_id": data.get("session_id", ""),
                        "timestamp": data.get("timestamp", ""),
                        "total_actions": stats.get("total_actions", 0),
                        "success_rate": stats.get("success_rate", 0.0),
                        "success_count": stats.get("success_count", 0),
                        "failure_count": stats.get("failure_count", 0),
                        "semantic_match_rate": stats.get("semantic_match_rate", 0.0)
                    })
                except Exception as e:
                    logger.warning(f"세션 정보 로드 실패: {filename}, {e}")
        
        # 타임스탬프 기준 정렬 (최신순)
        sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return sessions
    
    def get_action_history(self, action_id: str) -> List[ActionExecutionResult]:
        """특정 액션의 실행 이력 조회
        
        Args:
            action_id: 액션 ID
            
        Returns:
            해당 액션의 실행 결과 리스트
        """
        test_case_dir = os.path.join(self.data_dir, self.test_case_name)
        
        if not os.path.exists(test_case_dir):
            return []
        
        history = []
        
        for filename in os.listdir(test_case_dir):
            if filename.endswith("_results.json"):
                results_path = os.path.join(test_case_dir, filename)
                try:
                    with open(results_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    for r in data.get("results", []):
                        if r.get("action_id") == action_id:
                            history.append(ActionExecutionResult.from_dict(r))
                            
                except Exception as e:
                    logger.warning(f"결과 파일 로드 실패: {filename}, {e}")
        
        return history
    
    def get_failure_rate_by_action(self) -> Dict[str, float]:
        """액션별 실패율 계산
        
        Returns:
            {action_id: failure_rate} 딕셔너리
        """
        test_case_dir = os.path.join(self.data_dir, self.test_case_name)
        
        if not os.path.exists(test_case_dir):
            return {}
        
        # 액션별 성공/실패 카운트
        action_stats: Dict[str, Dict[str, int]] = {}
        
        for filename in os.listdir(test_case_dir):
            if filename.endswith("_results.json"):
                results_path = os.path.join(test_case_dir, filename)
                try:
                    with open(results_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    for r in data.get("results", []):
                        action_id = r.get("action_id", "")
                        if action_id not in action_stats:
                            action_stats[action_id] = {"success": 0, "failure": 0}
                        
                        if r.get("success", False):
                            action_stats[action_id]["success"] += 1
                        else:
                            action_stats[action_id]["failure"] += 1
                            
                except Exception as e:
                    logger.warning(f"결과 파일 로드 실패: {filename}, {e}")
        
        # 실패율 계산
        failure_rates = {}
        for action_id, counts in action_stats.items():
            total = counts["success"] + counts["failure"]
            if total > 0:
                failure_rates[action_id] = counts["failure"] / total
        
        return failure_rates
    
    def clear_results(self):
        """현재 세션 결과 초기화"""
        self.results = []
        self._action_counter = 0
        logger.debug("결과 초기화됨")
