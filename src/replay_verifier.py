"""
ReplayVerifier - 통합 검증기

스크린샷 비교와 Vision LLM을 조합하여 replay 결과를 검증한다.
스크린샷 비교 실패 시 Vision LLM으로 재검증한다.

수정 사항:
- 클릭 후 대기 시간 추가하여 화면 전환 후 캡처
- 특정 게임 윈도우만 캡처하도록 개선
- Vision LLM 검증 오류 처리 강화
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from PIL import Image
import pyautogui

from src.config_manager import ConfigManager
from src.screenshot_verifier import ScreenshotVerifier
from src.ui_analyzer import UIAnalyzer
from src.accuracy_tracker import AccuracyTracker, ActionExecutionResult
from src.window_capture import WindowCapture, capture_game_window
from src.semantic_action_replayer import ReplayResult

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """검증 결과 데이터 클래스"""
    action_index: int
    action_description: str
    screenshot_match: bool
    screenshot_similarity: float
    vision_verified: bool = False
    vision_match: bool = False
    final_result: str = "unknown"  # "pass", "fail", "warning"
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_index": self.action_index,
            "action_description": self.action_description,
            "screenshot_match": self.screenshot_match,
            "screenshot_similarity": self.screenshot_similarity,
            "vision_verified": self.vision_verified,
            "vision_match": self.vision_match,
            "final_result": self.final_result,
            "details": self.details
        }


@dataclass
class MatchingStatistics:
    """매칭 방법별 통계 데이터 클래스
    
    Requirements: 4.1, 4.3, 4.4
    """
    total_actions: int = 0
    semantic_match_count: int = 0
    coordinate_match_count: int = 0
    failed_count: int = 0
    avg_coordinate_change: float = 0.0
    max_coordinate_change: float = 0.0
    avg_match_confidence: float = 0.0
    min_match_confidence: float = 0.0
    max_match_confidence: float = 0.0
    confidence_scores: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_actions": self.total_actions,
            "semantic_match_count": self.semantic_match_count,
            "coordinate_match_count": self.coordinate_match_count,
            "failed_count": self.failed_count,
            "avg_coordinate_change": self.avg_coordinate_change,
            "max_coordinate_change": self.max_coordinate_change,
            "avg_match_confidence": self.avg_match_confidence,
            "min_match_confidence": self.min_match_confidence,
            "max_match_confidence": self.max_match_confidence
        }


@dataclass 
class ReplayReport:
    """Replay 검증 보고서"""
    test_case_name: str
    session_id: str
    start_time: str
    end_time: str
    total_actions: int
    passed_count: int
    failed_count: int
    warning_count: int
    success_rate: float
    verification_results: List[VerificationResult] = field(default_factory=list)
    matching_statistics: Optional[MatchingStatistics] = None
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "test_case_name": self.test_case_name,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_actions": self.total_actions,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "warning_count": self.warning_count,
            "success_rate": self.success_rate,
            "verification_results": [r.to_dict() for r in self.verification_results],
            "summary": self.summary
        }
        if self.matching_statistics:
            result["matching_statistics"] = self.matching_statistics.to_dict()
        return result


class ReplayVerifier:
    """통합 검증기"""
    
    def __init__(self, config: ConfigManager):
        """
        Args:
            config: 설정 관리자
        """
        self.config = config
        hash_threshold = config.get('automation.hash_threshold', 5)
        self.screenshot_verifier = ScreenshotVerifier(hash_threshold)
        self.ui_analyzer = UIAnalyzer(config)
        self.verification_results: List[VerificationResult] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_case_name = ""
        self.start_time = ""
        self._replay_screenshots_dir = ""
        
        # 게임 윈도우 캡처 설정
        self._window_title = config.get('game.window_title', '')
        self._window_capture = WindowCapture(self._window_title) if self._window_title else None
        self._capture_delay = config.get('automation.capture_delay', 0.5)  # 캡처 전 대기 시간
    
    def start_verification_session(self, test_case_name: str) -> str:
        """검증 세션 시작
        
        Args:
            test_case_name: 테스트 케이스 이름
            
        Returns:
            세션 ID
        """
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_case_name = test_case_name
        self.start_time = datetime.now().isoformat()
        self.verification_results = []
        
        # replay 스크린샷 저장 디렉토리 생성
        screenshot_dir = self.config.get('automation.screenshot_dir', 'screenshots')
        self._replay_screenshots_dir = os.path.join(screenshot_dir, f"replay_{self.session_id}")
        os.makedirs(self._replay_screenshots_dir, exist_ok=True)
        
        # 게임 윈도우 찾기
        if self._window_capture:
            hwnd = self._window_capture.find_window()
            if hwnd:
                logger.info(f"게임 윈도우 찾음: {self._window_title}")
            else:
                logger.warning(f"게임 윈도우를 찾을 수 없음: {self._window_title}, 전체 화면 캡처 사용")
        
        logger.info(f"검증 세션 시작: {test_case_name}, session={self.session_id}")
        return self.session_id
    
    def _capture_screenshot(self) -> Image.Image:
        """게임 윈도우 스크린샷 캡처
        
        Returns:
            PIL Image 객체
        """
        # 캡처 전 대기 (화면 전환 시간 확보)
        if self._capture_delay > 0:
            time.sleep(self._capture_delay)
        
        # 게임 윈도우만 캡처 시도
        if self._window_capture and self._window_capture._hwnd:
            image = self._window_capture.capture_window_region()
            if image:
                return image
        
        # 실패 시 전체 화면 캡처
        return pyautogui.screenshot()
    
    def capture_and_verify(self, action_index: int, action: Dict[str, Any], 
                          next_action: Dict[str, Any] = None) -> VerificationResult:
        """액션 실행 후 스크린샷 캡처 및 검증
        
        녹화 시와 동일한 타이밍으로 캡처하여 비교한다.
        (액션 실행 후 capture_delay 대기 후 게임 윈도우만 캡처)
        
        Args:
            action_index: 액션 인덱스
            action: 현재 액션 데이터 딕셔너리
            next_action: 다음 액션 데이터 (현재 사용하지 않음)
            
        Returns:
            VerificationResult 객체
        """
        description = action.get('description', f'액션 {action_index}')
        
        # 현재 액션의 스크린샷과 비교 (녹화 시 액션 후 대기 후 캡처했으므로)
        expected_screenshot = action.get('screenshot_path', '')
        
        # 상대 경로를 절대 경로로 변환 (프로젝트 루트 기준)
        if expected_screenshot and not os.path.isabs(expected_screenshot):
            # 프로젝트 루트 찾기 (src 폴더의 상위)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # 경로 구분자 정규화 (Windows 호환)
            expected_screenshot = expected_screenshot.replace('/', os.sep).replace('\\', os.sep)
            expected_screenshot = os.path.join(project_root, expected_screenshot)
            expected_screenshot = os.path.normpath(expected_screenshot)
        
        result = VerificationResult(
            action_index=action_index,
            action_description=description,
            screenshot_match=False,
            screenshot_similarity=0.0
        )
        result.details["comparison_method"] = "현재 액션 스크린샷과 비교 (동일 타이밍)"
        result.details["expected_screenshot_path"] = expected_screenshot
        
        # 디버그: 경로 존재 여부 출력
        if expected_screenshot:
            exists = os.path.exists(expected_screenshot)
            logger.info(f"[{action_index}] 예상 스크린샷 경로: {expected_screenshot}, 존재: {exists}")
            if not exists:
                print(f"  ⚠ 예상 스크린샷 경로: {expected_screenshot}")
                print(f"  ⚠ 파일 존재 여부: {exists}")
        
        # 현재 화면 캡처 (게임 윈도우만)
        try:
            current_screenshot = self._capture_screenshot()
            
            # replay 스크린샷 저장
            replay_screenshot_path = os.path.join(
                self._replay_screenshots_dir, 
                f"action_{action_index:04d}.png"
            )
            current_screenshot.save(replay_screenshot_path)
            result.details["replay_screenshot"] = replay_screenshot_path
            
        except Exception as e:
            logger.error(f"스크린샷 캡처 실패: {e}")
            result.final_result = "fail"
            result.details["error"] = str(e)
            self.verification_results.append(result)
            return result
        
        # 1단계: 스크린샷 비교
        if expected_screenshot and os.path.exists(expected_screenshot):
            verify_result = self.screenshot_verifier.verify_screenshot(
                expected_screenshot, current_screenshot
            )
            result.screenshot_match = verify_result["match"]
            result.screenshot_similarity = verify_result["similarity"]
            result.details["screenshot_verification"] = verify_result
            
            if result.screenshot_match:
                # 스크린샷 일치 - PASS
                result.final_result = "pass"
                logger.info(f"[{action_index}] 스크린샷 검증 통과 (similarity={result.screenshot_similarity:.3f})")
            else:
                # 2단계: Vision LLM으로 재검증
                logger.info(f"[{action_index}] 스크린샷 불일치 (similarity={result.screenshot_similarity:.3f}), Vision LLM 검증 시도...")
                result.vision_verified = True
                
                try:
                    vision_match, vision_details = self._verify_with_vision_llm(
                        expected_screenshot, current_screenshot, action
                    )
                    result.vision_match = vision_match
                    result.details["vision_details"] = vision_details
                    
                    if vision_match:
                        result.final_result = "warning"  # 스크린샷은 다르지만 의미적으로 일치
                        logger.info(f"[{action_index}] Vision LLM 검증 통과 (의미적 일치)")
                    else:
                        result.final_result = "fail"
                        logger.warning(f"[{action_index}] Vision LLM 검증 실패")
                        
                except Exception as e:
                    logger.error(f"Vision LLM 검증 오류: {e}")
                    # Vision LLM 실패해도 스크린샷 유사도가 높으면 warning으로 처리
                    if result.screenshot_similarity >= 0.7:
                        result.final_result = "warning"
                        result.details["note"] = f"Vision LLM 오류, 유사도 {result.screenshot_similarity:.1%}로 warning 처리"
                    else:
                        result.final_result = "fail"
                    result.details["vision_error"] = str(e)
        else:
            # 예상 스크린샷 없음 - 검증 불가, warning 처리
            result.final_result = "warning"
            result.details["note"] = "예상 스크린샷 없음, 검증 생략"
            logger.warning(f"[{action_index}] 예상 스크린샷 없음: {expected_screenshot}")
        
        self.verification_results.append(result)
        return result
    
    def _verify_with_vision_llm(self, expected_path: str, actual_image: Image.Image, 
                                action: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Vision LLM으로 의미적 검증
        
        Args:
            expected_path: 예상 스크린샷 경로
            actual_image: 실제 캡처 이미지
            action: 액션 데이터
            
        Returns:
            (의미적 일치 여부, 상세 정보)
        """
        details = {}
        
        try:
            # 예상 이미지 로드
            expected_image = Image.open(expected_path)
            
            # 예상 이미지 분석
            logger.info("예상 이미지 Vision LLM 분석 중...")
            expected_ui = self.ui_analyzer.analyze_with_retry(expected_image, retry_count=2)
            details["expected_ui_source"] = expected_ui.get("source", "unknown")
            
            # 예상 이미지 분석 결과 상세 기록
            expected_buttons = [b.get('text', '') for b in expected_ui.get('buttons', []) if b.get('text')]
            expected_texts = [t.get('content', '') for t in expected_ui.get('text_fields', []) if t.get('content')]
            details["expected_ui_elements"] = {
                "buttons": expected_buttons,
                "text_fields": expected_texts,
                "button_count": len(expected_buttons),
                "text_count": len(expected_texts)
            }
            logger.info(f"예상 이미지 UI 요소: 버튼 {len(expected_buttons)}개 {expected_buttons}, 텍스트 {len(expected_texts)}개")
            
            if expected_ui.get("source") == "failed":
                logger.warning("예상 이미지 분석 실패")
                details["expected_error"] = expected_ui.get("error", "분석 실패")
            
            # 실제 이미지 분석
            logger.info("실제 이미지 Vision LLM 분석 중...")
            actual_ui = self.ui_analyzer.analyze_with_retry(actual_image, retry_count=2)
            details["actual_ui_source"] = actual_ui.get("source", "unknown")
            
            # 실제 이미지 분석 결과 상세 기록
            actual_buttons = [b.get('text', '') for b in actual_ui.get('buttons', []) if b.get('text')]
            actual_texts = [t.get('content', '') for t in actual_ui.get('text_fields', []) if t.get('content')]
            details["actual_ui_elements"] = {
                "buttons": actual_buttons,
                "text_fields": actual_texts,
                "button_count": len(actual_buttons),
                "text_count": len(actual_texts)
            }
            logger.info(f"실제 이미지 UI 요소: 버튼 {len(actual_buttons)}개 {actual_buttons}, 텍스트 {len(actual_texts)}개")
            
            if actual_ui.get("source") == "failed":
                logger.warning("실제 이미지 분석 실패")
                details["actual_error"] = actual_ui.get("error", "분석 실패")
            
            # 둘 다 실패하면 비교 불가
            if expected_ui.get("source") == "failed" and actual_ui.get("source") == "failed":
                details["comparison_result"] = "both_failed"
                return False, details
            
            # UI 요소 비교
            match_result, similarity, comparison_details = self._compare_ui_elements(expected_ui, actual_ui, action)
            details["ui_similarity"] = similarity
            details["comparison_result"] = "match" if match_result else "mismatch"
            details["comparison_details"] = comparison_details
            
            logger.info(f"Vision LLM 비교 결과: {'일치' if match_result else '불일치'} (유사도: {similarity:.2%})")
            
            return match_result, details
            
        except Exception as e:
            logger.error(f"Vision LLM 분석 실패: {e}")
            details["error"] = str(e)
            raise
    
    def _compare_ui_elements(self, expected_ui: Dict, actual_ui: Dict, 
                            action: Dict[str, Any]) -> Tuple[bool, float, Dict[str, Any]]:
        """UI 요소 비교
        
        Args:
            expected_ui: 예상 UI 분석 결과
            actual_ui: 실제 UI 분석 결과
            action: 액션 데이터
            
        Returns:
            (의미적 일치 여부, 유사도, 비교 상세 정보)
        """
        # 버튼 텍스트 비교
        expected_buttons = {b.get('text', '').lower().strip() for b in expected_ui.get('buttons', []) if b.get('text')}
        actual_buttons = {b.get('text', '').lower().strip() for b in actual_ui.get('buttons', []) if b.get('text')}
        
        # 텍스트 필드 비교
        expected_texts = {t.get('content', '').lower().strip() for t in expected_ui.get('text_fields', []) if t.get('content')}
        actual_texts = {t.get('content', '').lower().strip() for t in actual_ui.get('text_fields', []) if t.get('content')}
        
        # 빈 문자열 제거
        expected_buttons.discard('')
        actual_buttons.discard('')
        expected_texts.discard('')
        actual_texts.discard('')
        
        # 주요 UI 요소가 유사하면 일치로 판단
        button_overlap = len(expected_buttons & actual_buttons)
        text_overlap = len(expected_texts & actual_texts)
        
        total_expected = len(expected_buttons) + len(expected_texts)
        total_overlap = button_overlap + text_overlap
        
        # 비교 상세 정보 생성
        comparison_details = {
            "expected_buttons": list(expected_buttons),
            "actual_buttons": list(actual_buttons),
            "expected_texts": list(expected_texts),
            "actual_texts": list(actual_texts),
            "matched_buttons": list(expected_buttons & actual_buttons),
            "matched_texts": list(expected_texts & actual_texts),
            "button_overlap": button_overlap,
            "text_overlap": text_overlap,
            "total_expected": total_expected,
            "total_overlap": total_overlap
        }
        
        if total_expected == 0:
            # 비교할 요소가 없으면 일치로 간주
            logger.debug("비교할 UI 요소 없음, 일치로 간주")
            comparison_details["note"] = "비교할 UI 요소 없음, 일치로 간주"
            return True, 1.0, comparison_details
        
        similarity = total_overlap / total_expected
        
        logger.debug(f"UI 요소 유사도: {similarity:.2f} "
                    f"(buttons: {button_overlap}/{len(expected_buttons)}, "
                    f"texts: {text_overlap}/{len(expected_texts)})")
        
        # 50% 이상 일치하면 의미적으로 같은 화면으로 판단
        return similarity >= 0.5, similarity, comparison_details
    
    def generate_report(self) -> ReplayReport:
        """검증 보고서 생성
        
        Returns:
            ReplayReport 객체
        """
        end_time = datetime.now().isoformat()
        
        passed = sum(1 for r in self.verification_results if r.final_result == "pass")
        failed = sum(1 for r in self.verification_results if r.final_result == "fail")
        warnings = sum(1 for r in self.verification_results if r.final_result == "warning")
        total = len(self.verification_results)
        
        success_rate = (passed + warnings) / total if total > 0 else 0.0
        
        # 요약 생성
        summary_lines = [
            f"테스트 케이스: {self.test_case_name}",
            f"실행 시간: {self.start_time} ~ {end_time}",
            f"",
            f"=== 검증 결과 요약 ===",
            f"총 액션 수: {total}",
            f"✓ 통과 (PASS): {passed}",
            f"⚠ 경고 (WARNING): {warnings}",
            f"✗ 실패 (FAIL): {failed}",
            f"성공률: {success_rate * 100:.1f}%",
        ]
        
        if failed > 0:
            summary_lines.append("")
            summary_lines.append("=== 실패한 액션 ===")
            for r in self.verification_results:
                if r.final_result == "fail":
                    summary_lines.append(f"  [{r.action_index}] {r.action_description}")
        
        report = ReplayReport(
            test_case_name=self.test_case_name,
            session_id=self.session_id,
            start_time=self.start_time,
            end_time=end_time,
            total_actions=total,
            passed_count=passed,
            failed_count=failed,
            warning_count=warnings,
            success_rate=success_rate,
            verification_results=self.verification_results,
            summary="\n".join(summary_lines)
        )
        
        return report
    
    def save_report(self, report: ReplayReport, output_dir: str = "reports") -> str:
        """보고서 저장
        
        Args:
            report: ReplayReport 객체
            output_dir: 출력 디렉토리
            
        Returns:
            저장된 파일 경로
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # JSON 보고서 저장
        json_path = os.path.join(output_dir, f"{self.test_case_name}_{self.session_id}_report.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 텍스트 보고서 저장
        txt_path = os.path.join(output_dir, f"{self.test_case_name}_{self.session_id}_report.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(report.summary)
            f.write("\n\n")
            f.write("=== 상세 결과 ===\n")
            for r in report.verification_results:
                status = {"pass": "✓", "fail": "✗", "warning": "⚠"}.get(r.final_result, "?")
                f.write(f"{status} [{r.action_index}] {r.action_description}\n")
                f.write(f"    스크린샷 유사도: {r.screenshot_similarity:.3f}\n")
                if r.vision_verified:
                    f.write(f"    Vision LLM 검증: {'통과' if r.vision_match else '실패'}\n")
        
        logger.info(f"보고서 저장: {json_path}")
        return json_path
    
    def print_report(self, report: ReplayReport):
        """보고서 콘솔 출력
        
        Args:
            report: ReplayReport 객체
        """
        print()
        print("=" * 60)
        print(report.summary)
        print("=" * 60)
        print()
    
    def calculate_matching_statistics(self, replay_results: List[ReplayResult]) -> MatchingStatistics:
        """매칭 방법별 통계 계산
        
        Requirements: 4.1, 4.3
        
        Args:
            replay_results: SemanticActionReplayer의 ReplayResult 리스트
            
        Returns:
            MatchingStatistics 객체
        """
        if not replay_results:
            return MatchingStatistics()
        
        total = len(replay_results)
        
        # 매칭 방법별 카운트 (Requirements: 4.1)
        semantic_count = sum(1 for r in replay_results if r.method == 'semantic')
        coordinate_count = sum(1 for r in replay_results if r.method == 'coordinate')
        # 'direct'도 coordinate 기반으로 간주 (원래 좌표 그대로 사용)
        direct_count = sum(1 for r in replay_results if r.method == 'direct')
        failed_count = sum(1 for r in replay_results if r.method == 'failed')
        
        # 좌표 변위 계산 (Requirements: 4.3)
        coord_changes = []
        for r in replay_results:
            if r.coordinate_change is not None:
                dx, dy = r.coordinate_change
                distance = (dx ** 2 + dy ** 2) ** 0.5
                coord_changes.append(distance)
        
        avg_coord_change = sum(coord_changes) / len(coord_changes) if coord_changes else 0.0
        max_coord_change = max(coord_changes) if coord_changes else 0.0
        
        # 신뢰도 점수 통계 (Requirements: 4.2)
        confidence_scores = [r.match_confidence for r in replay_results if r.match_confidence > 0]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        min_confidence = min(confidence_scores) if confidence_scores else 0.0
        max_confidence = max(confidence_scores) if confidence_scores else 0.0
        
        return MatchingStatistics(
            total_actions=total,
            semantic_match_count=semantic_count,
            coordinate_match_count=coordinate_count + direct_count,
            failed_count=failed_count,
            avg_coordinate_change=avg_coord_change,
            max_coordinate_change=max_coord_change,
            avg_match_confidence=avg_confidence,
            min_match_confidence=min_confidence,
            max_match_confidence=max_confidence,
            confidence_scores=confidence_scores
        )
    
    def get_statistics(self, replay_results: List[ReplayResult]) -> Dict[str, Any]:
        """재생 통계 반환
        
        Requirements: 4.1, 4.4
        
        매칭 방법 분류와 신뢰도 점수 통계를 포함한 통계 딕셔너리를 반환한다.
        
        Args:
            replay_results: SemanticActionReplayer의 ReplayResult 리스트
            
        Returns:
            통계 딕셔너리
        """
        stats = self.calculate_matching_statistics(replay_results)
        
        total = stats.total_actions
        
        # 매칭 방법별 비율 계산
        semantic_rate = stats.semantic_match_count / total if total > 0 else 0.0
        coordinate_rate = stats.coordinate_match_count / total if total > 0 else 0.0
        failed_rate = stats.failed_count / total if total > 0 else 0.0
        
        return {
            # 기본 통계
            "total_actions": total,
            "semantic_match_count": stats.semantic_match_count,
            "coordinate_match_count": stats.coordinate_match_count,
            "failed_count": stats.failed_count,
            
            # 비율 (Requirements: 4.4)
            "semantic_match_rate": semantic_rate,
            "coordinate_match_rate": coordinate_rate,
            "failed_rate": failed_rate,
            
            # 좌표 변위 통계 (Requirements: 4.3)
            "avg_coordinate_change": stats.avg_coordinate_change,
            "max_coordinate_change": stats.max_coordinate_change,
            
            # 신뢰도 점수 통계 (Requirements: 4.2)
            "avg_match_confidence": stats.avg_match_confidence,
            "min_match_confidence": stats.min_match_confidence,
            "max_match_confidence": stats.max_match_confidence,
            
            # 매칭 방법 분류 (Requirements: 4.4)
            "matching_breakdown": {
                "semantic": stats.semantic_match_count,
                "coordinate": stats.coordinate_match_count,
                "failed": stats.failed_count
            }
        }
    
    def generate_report_with_matching_stats(
        self, 
        replay_results: List[ReplayResult]
    ) -> ReplayReport:
        """매칭 통계를 포함한 검증 보고서 생성
        
        Requirements: 4.1, 4.4
        
        Args:
            replay_results: SemanticActionReplayer의 ReplayResult 리스트
            
        Returns:
            ReplayReport 객체 (matching_statistics 포함)
        """
        # 기본 보고서 생성
        report = self.generate_report()
        
        # 매칭 통계 추가
        matching_stats = self.calculate_matching_statistics(replay_results)
        report.matching_statistics = matching_stats
        
        # 요약에 매칭 통계 추가
        stats_summary = [
            "",
            "=== 매칭 통계 ===",
            f"의미론적 매칭: {matching_stats.semantic_match_count}회",
            f"좌표 기반 매칭: {matching_stats.coordinate_match_count}회",
            f"실패: {matching_stats.failed_count}회",
        ]
        
        if matching_stats.avg_coordinate_change > 0:
            stats_summary.append(f"평균 좌표 변위: {matching_stats.avg_coordinate_change:.1f}px")
            stats_summary.append(f"최대 좌표 변위: {matching_stats.max_coordinate_change:.1f}px")
        
        if matching_stats.avg_match_confidence > 0:
            stats_summary.append(f"평균 매칭 신뢰도: {matching_stats.avg_match_confidence:.2f}")
        
        report.summary += "\n" + "\n".join(stats_summary)
        
        return report

