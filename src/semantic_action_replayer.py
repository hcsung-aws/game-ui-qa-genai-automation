"""
SemanticActionReplayer - 의미론적 매칭을 통한 액션 재실행기

Requirements: 12.1, 12.2, 12.3, 12.4, 12.6
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

import pyautogui
from PIL import Image
import imagehash

from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer
from src.semantic_action_recorder import SemanticAction
from src.window_capture import WindowCapture


logger = logging.getLogger(__name__)


@dataclass
class ReplayResult:
    """액션 재실행 결과"""
    action_id: str
    success: bool
    method: str  # 'direct', 'semantic', 'coordinate', 'failed'
    original_coords: Tuple[int, int]
    actual_coords: Optional[Tuple[int, int]] = None
    coordinate_change: Optional[Tuple[int, int]] = None
    match_confidence: float = 0.0  # 매칭 신뢰도 점수 (Requirements: 4.2)
    screen_transition_verified: bool = False
    expected_transition: str = ""
    actual_transition: str = ""
    error_message: str = ""
    execution_time: float = 0.0


class SemanticActionReplayer:
    """의미론적 액션 재실행기
    
    원래 좌표로 먼저 시도하고, 실패 시 의미론적 매칭을 통해
    UI 요소를 찾아 액션을 재실행한다.
    
    Requirements: 12.1, 12.2, 12.3, 12.4, 12.6
    """
    
    def __init__(self, config: ConfigManager, ui_analyzer: Optional[UIAnalyzer] = None):
        """
        Args:
            config: 설정 관리자
            ui_analyzer: UI 분석기 (선택사항, 없으면 새로 생성)
        """
        self.config = config
        self.ui_analyzer = ui_analyzer or UIAnalyzer(config)
        self.results: List[ReplayResult] = []
        self._action_counter = 0
        
        # 윈도우 캡처 (좌표 변환용)
        window_title = config.get('game.window_title', '')
        self._window_capture = WindowCapture(window_title)
        self._window_capture.find_window()
    
    def replay_action(self, action: SemanticAction) -> ReplayResult:
        """의미론적 액션 재실행
        
        Requirements: 12.1, 12.2, 12.4, 12.6
        
        1. 원래 좌표로 먼저 시도
        2. 실패 시 의미론적 매칭 시도
        3. 화면 전환 검증
        
        Args:
            action: 재실행할 의미론적 액션
            
        Returns:
            ReplayResult 객체
        """
        self._action_counter += 1
        start_time = time.time()
        
        result = ReplayResult(
            action_id=f"action_{self._action_counter:04d}",
            success=False,
            method='failed',
            original_coords=(action.x, action.y)
        )
        
        try:
            # 클릭 액션 처리
            if action.action_type == 'click':
                result = self._replay_click_action(action, result)
            
            # 키보드 입력 처리
            elif action.action_type == 'key_press':
                result = self._replay_key_action(action, result)
            
            # 스크롤 처리
            elif action.action_type == 'scroll':
                result = self._replay_scroll_action(action, result)
            
            # 대기 처리
            elif action.action_type == 'wait':
                result = self._replay_wait_action(action, result)
            
            else:
                result.error_message = f"지원하지 않는 액션 타입: {action.action_type}"
                logger.warning(result.error_message)
        
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"액션 재실행 실패: {e}")
        
        result.execution_time = time.time() - start_time
        self.results.append(result)
        
        return result

    def _replay_click_action(self, action: SemanticAction, 
                             result: ReplayResult) -> ReplayResult:
        """클릭 액션 재실행
        
        Requirements: 12.1, 12.2, 12.4
        
        Args:
            action: 재실행할 클릭 액션
            result: 결과 객체
            
        Returns:
            업데이트된 ReplayResult
        """
        x, y = action.x, action.y
        
        # 1. 원래 좌표로 먼저 시도 (Requirements: 12.1)
        logger.info(f"원래 좌표로 클릭 시도: ({x}, {y})")
        
        # 클릭 전 스크린샷 캡처
        screenshot_before = self._capture_screenshot()
        hash_before = self._calculate_hash(screenshot_before) if screenshot_before else None
        
        # 원래 좌표에서 예상 UI 요소 확인
        element_found_at_original = self._verify_element_at_position(
            screenshot_before, x, y, action.semantic_info
        )
        
        if element_found_at_original:
            # 원래 좌표에서 요소 발견 - 직접 클릭
            self._execute_click(x, y, action.button or 'left')
            result.method = 'direct'
            result.actual_coords = (x, y)
            result.success = True
            logger.info(f"직접 매칭 성공: ({x}, {y})")
        else:
            # 2. 의미론적 매칭 시도 (Requirements: 12.2, 12.3, 12.4)
            logger.info("원래 좌표에서 요소를 찾지 못함. 의미론적 매칭 시도...")
            
            new_coords = self._semantic_matching(action, screenshot_before)
            
            if new_coords:
                new_x, new_y = new_coords
                self._execute_click(new_x, new_y, action.button or 'left')
                result.method = 'semantic'
                result.actual_coords = (new_x, new_y)
                result.coordinate_change = (new_x - x, new_y - y)
                result.success = True
                logger.info(f"의미론적 매칭 성공: ({new_x}, {new_y}), 변경: {result.coordinate_change}")
            else:
                result.error_message = "의미론적 매칭 실패: 요소를 찾을 수 없음"
                logger.warning(result.error_message)
        
        # 3. 화면 전환 검증 (Requirements: 12.6)
        if result.success:
            time.sleep(0.3)  # 화면 전환 대기
            result = self._verify_screen_transition(action, result, hash_before)
        
        return result

    def replay_click_with_semantic_matching(self, action: SemanticAction) -> ReplayResult:
        """의미론적 매칭을 우선 적용하여 클릭 재생
        
        Requirements: 3.1, 3.3, 3.4, 3.5
        
        1. 현재 화면 캡처 및 UI 분석
        2. _find_matching_element()로 매칭 시도
        3. 신뢰도 0.7 이상이면 매칭된 좌표 사용
        4. 0.7 미만이면 원래 좌표로 폴백
        5. 좌표 차이 로그 기록
        
        Args:
            action: 재실행할 의미론적 액션
            
        Returns:
            ReplayResult 객체
        """
        self._action_counter += 1
        start_time = time.time()
        
        x, y = action.x, action.y
        
        result = ReplayResult(
            action_id=f"action_{self._action_counter:04d}",
            success=False,
            method='failed',
            original_coords=(x, y),
            match_confidence=0.0
        )
        
        try:
            # 1. 현재 화면 캡처 및 UI 분석 (Requirements: 3.1)
            logger.info(f"의미론적 매칭 클릭 시도: 원래 좌표 ({x}, {y})")
            screenshot_before = self._capture_screenshot()
            hash_before = self._calculate_hash(screenshot_before) if screenshot_before else None
            
            if screenshot_before is None:
                # 스크린샷 실패 시 원래 좌표로 폴백
                logger.warning("스크린샷 캡처 실패, 원래 좌표로 폴백")
                self._execute_click(x, y, action.button or 'left')
                result.method = 'coordinate'
                result.actual_coords = (x, y)
                result.success = True
                result.match_confidence = 0.0
            else:
                # UI 분석
                semantic_info = action.semantic_info
                target_element = semantic_info.get('target_element', {}) if semantic_info else {}
                
                if not target_element:
                    # 의미론적 정보 없음 - 원래 좌표로 폴백
                    logger.info("의미론적 정보 없음, 원래 좌표로 폴백")
                    self._execute_click(x, y, action.button or 'left')
                    result.method = 'coordinate'
                    result.actual_coords = (x, y)
                    result.success = True
                    result.match_confidence = 0.0
                else:
                    # Vision LLM으로 현재 화면 분석
                    try:
                        ui_data = self.ui_analyzer.analyze_with_retry(screenshot_before)
                        
                        # 2. _find_matching_element()로 매칭 시도
                        matched_coords, confidence = self._find_matching_element(ui_data, target_element)
                        result.match_confidence = confidence
                        
                        # 3. 신뢰도 0.7 이상이면 매칭된 좌표 사용 (Requirements: 3.3)
                        if matched_coords and confidence >= 0.7:
                            new_x, new_y = matched_coords
                            self._execute_click(new_x, new_y, action.button or 'left')
                            result.method = 'semantic'
                            result.actual_coords = (new_x, new_y)
                            result.coordinate_change = (new_x - x, new_y - y)
                            result.success = True
                            
                            # 5. 좌표 차이 로그 기록 (Requirements: 3.5)
                            logger.info(
                                f"의미론적 매칭 성공: 신뢰도 {confidence:.2f}, "
                                f"좌표 ({new_x}, {new_y}), "
                                f"변경 ({new_x - x}, {new_y - y})"
                            )
                        else:
                            # 4. 0.7 미만이면 원래 좌표로 폴백 (Requirements: 3.4)
                            logger.info(
                                f"매칭 신뢰도 부족 ({confidence:.2f} < 0.7), 원래 좌표로 폴백"
                            )
                            self._execute_click(x, y, action.button or 'left')
                            result.method = 'coordinate'
                            result.actual_coords = (x, y)
                            result.success = True
                            
                    except Exception as e:
                        # UI 분석 실패 시 원래 좌표로 폴백
                        logger.warning(f"UI 분석 실패: {e}, 원래 좌표로 폴백")
                        self._execute_click(x, y, action.button or 'left')
                        result.method = 'coordinate'
                        result.actual_coords = (x, y)
                        result.success = True
                        result.match_confidence = 0.0
            
            # 화면 전환 검증
            if result.success:
                time.sleep(0.3)
                result = self._verify_screen_transition(action, result, hash_before)
                
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"의미론적 매칭 클릭 실패: {e}")
        
        result.execution_time = time.time() - start_time
        self.results.append(result)
        
        return result
    
    def _replay_key_action(self, action: SemanticAction, 
                           result: ReplayResult) -> ReplayResult:
        """키보드 액션 재실행
        
        Args:
            action: 재실행할 키보드 액션
            result: 결과 객체
            
        Returns:
            업데이트된 ReplayResult
        """
        key = action.key
        if key:
            try:
                pyautogui.press(key)
                result.success = True
                result.method = 'direct'
                logger.info(f"키 입력 성공: {key}")
            except Exception as e:
                result.error_message = f"키 입력 실패: {e}"
                logger.error(result.error_message)
        else:
            result.error_message = "키 정보가 없습니다"
        
        return result
    
    def _replay_scroll_action(self, action: SemanticAction, 
                              result: ReplayResult) -> ReplayResult:
        """스크롤 액션 재실행
        
        Args:
            action: 재실행할 스크롤 액션
            result: 결과 객체
            
        Returns:
            업데이트된 ReplayResult
        """
        try:
            scroll_amount = action.scroll_dy or 0
            # 윈도우 상대 좌표를 스크린 절대 좌표로 변환
            screen_x, screen_y = self._convert_to_screen_coords(action.x, action.y)
            pyautogui.scroll(scroll_amount, x=screen_x, y=screen_y)
            result.success = True
            result.method = 'direct'
            result.actual_coords = (action.x, action.y)
            logger.info(f"스크롤 성공: 윈도우({action.x}, {action.y}) -> 스크린({screen_x}, {screen_y}), 양: {scroll_amount}")
        except Exception as e:
            result.error_message = f"스크롤 실패: {e}"
            logger.error(result.error_message)
        
        return result
    
    def _replay_wait_action(self, action: SemanticAction, 
                            result: ReplayResult) -> ReplayResult:
        """대기 액션 재실행
        
        Args:
            action: 재실행할 대기 액션
            result: 결과 객체
            
        Returns:
            업데이트된 ReplayResult
        """
        try:
            # 설명에서 대기 시간 추출 (예: "1.5초 대기")
            import re
            match = re.search(r'(\d+\.?\d*)초', action.description)
            if match:
                wait_time = float(match.group(1))
            else:
                wait_time = 1.0  # 기본 대기 시간
            
            time.sleep(wait_time)
            result.success = True
            result.method = 'direct'
            logger.info(f"대기 완료: {wait_time}초")
        except Exception as e:
            result.error_message = f"대기 실패: {e}"
            logger.error(result.error_message)
        
        return result

    def _capture_screenshot(self) -> Optional[Image.Image]:
        """현재 화면 캡처
        
        Returns:
            PIL Image 객체 또는 None
        """
        try:
            return pyautogui.screenshot()
        except Exception as e:
            logger.error(f"스크린샷 캡처 실패: {e}")
            return None
    
    def _calculate_hash(self, image: Image.Image) -> str:
        """이미지 해시 계산
        
        Args:
            image: PIL Image 객체
            
        Returns:
            해시 문자열
        """
        return str(imagehash.average_hash(image))
    
    def _get_window_offset(self) -> Tuple[int, int]:
        """게임 윈도우의 화면상 오프셋 가져오기
        
        Returns:
            (offset_x, offset_y) 윈도우 좌상단의 스크린 좌표
        """
        if self._window_capture and self._window_capture._hwnd:
            rect = self._window_capture.get_window_rect()
            if rect:
                return (rect[0], rect[1])  # left, top
        return (0, 0)
    
    def _convert_to_screen_coords(self, window_x: int, window_y: int) -> Tuple[int, int]:
        """윈도우 기준 상대 좌표를 스크린 절대 좌표로 변환
        
        Args:
            window_x: 윈도우 기준 X 좌표
            window_y: 윈도우 기준 Y 좌표
            
        Returns:
            (screen_x, screen_y) 스크린 절대 좌표
        """
        offset_x, offset_y = self._get_window_offset()
        return (window_x + offset_x, window_y + offset_y)
    
    def _execute_click(self, x: int, y: int, button: str = 'left'):
        """클릭 실행 (윈도우 상대 좌표를 스크린 좌표로 변환하여 클릭)
        
        Args:
            x: X 좌표 (윈도우 기준 상대 좌표)
            y: Y 좌표 (윈도우 기준 상대 좌표)
            button: 마우스 버튼 ('left', 'right', 'middle')
        """
        # 윈도우 상대 좌표를 스크린 절대 좌표로 변환
        screen_x, screen_y = self._convert_to_screen_coords(x, y)
        
        action_delay = self.config.get('automation.action_delay', 0.5)
        pyautogui.click(screen_x, screen_y, button=button)
        logger.debug(f"클릭 실행: 윈도우({x}, {y}) -> 스크린({screen_x}, {screen_y})")
        time.sleep(action_delay)
    
    def _verify_element_at_position(self, image: Optional[Image.Image], 
                                    x: int, y: int,
                                    semantic_info: Dict[str, Any]) -> bool:
        """특정 좌표에 예상 UI 요소가 있는지 확인
        
        Requirements: 12.1
        
        Args:
            image: 현재 화면 이미지
            x: X 좌표
            y: Y 좌표
            semantic_info: 예상 의미론적 정보
            
        Returns:
            요소 발견 여부
        """
        if image is None:
            return True  # 이미지가 없으면 원래 좌표로 시도
        
        if not semantic_info:
            return True  # 의미론적 정보가 없으면 원래 좌표로 시도
        
        try:
            # Vision LLM으로 현재 화면 분석
            ui_data = self.ui_analyzer.analyze_with_retry(image)
            
            # 예상 요소 정보
            target_element = semantic_info.get('target_element', {})
            expected_type = target_element.get('type', '')
            expected_text = target_element.get('text', '').lower()
            
            if not expected_type and not expected_text:
                return True  # 비교할 정보가 없으면 원래 좌표로 시도
            
            # 해당 좌표 근처에서 일치하는 요소 찾기
            tolerance = 50  # 픽셀 허용 오차
            
            # 버튼 검색
            for button in ui_data.get('buttons', []):
                bx, by = button.get('x', 0), button.get('y', 0)
                if abs(bx - x) <= tolerance and abs(by - y) <= tolerance:
                    if expected_type == 'button':
                        button_text = button.get('text', '').lower()
                        if expected_text and expected_text in button_text:
                            return True
                        elif not expected_text:
                            return True
            
            # 아이콘 검색
            for icon in ui_data.get('icons', []):
                ix, iy = icon.get('x', 0), icon.get('y', 0)
                if abs(ix - x) <= tolerance and abs(iy - y) <= tolerance:
                    if expected_type == 'icon':
                        return True
            
            # 텍스트 필드 검색
            for text_field in ui_data.get('text_fields', []):
                tx, ty = text_field.get('x', 0), text_field.get('y', 0)
                if abs(tx - x) <= tolerance and abs(ty - y) <= tolerance:
                    if expected_type == 'text_field':
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"요소 확인 중 오류: {e}")
            return True  # 오류 시 원래 좌표로 시도
    
    def _find_matching_element(self, 
                               current_ui_data: Dict[str, Any], 
                               target_element: Dict[str, Any]) -> Tuple[Optional[Tuple[int, int]], float]:
        """현재 UI 데이터에서 target_element와 매칭되는 요소 탐색
        
        Requirements: 3.2
        
        텍스트 유사도 + 타입 매칭 점수를 계산하여 가장 높은 점수의 요소와 신뢰도를 반환한다.
        
        Args:
            current_ui_data: 현재 화면의 UI 분석 데이터
            target_element: 찾고자 하는 대상 요소 정보
            
        Returns:
            (매칭된 좌표, 신뢰도) 또는 (None, 0.0)
        """
        if not current_ui_data or not target_element:
            return (None, 0.0)
        
        expected_type = target_element.get('type', '')
        expected_text = target_element.get('text', '')
        expected_description = target_element.get('description', '')
        
        best_match = None
        best_score = 0.0
        
        # 버튼에서 매칭
        if expected_type in ['button', 'unknown', '']:
            for button in current_ui_data.get('buttons', []):
                score = self._calculate_match_score(
                    button, expected_type, expected_text, expected_description
                )
                if score > best_score:
                    best_score = score
                    best_match = (button.get('x', 0), button.get('y', 0))
        
        # 아이콘에서 매칭
        if expected_type in ['icon', 'unknown', '']:
            for icon in current_ui_data.get('icons', []):
                score = self._calculate_match_score(
                    icon, expected_type, expected_text, expected_description
                )
                if score > best_score:
                    best_score = score
                    best_match = (icon.get('x', 0), icon.get('y', 0))
        
        # 텍스트 필드에서 매칭
        if expected_type in ['text_field', 'input_field', 'unknown', '']:
            for text_field in current_ui_data.get('text_fields', []):
                score = self._calculate_match_score(
                    text_field, expected_type, expected_text, expected_description
                )
                if score > best_score:
                    best_score = score
                    best_match = (text_field.get('x', 0), text_field.get('y', 0))
        
        return (best_match, best_score)

    def _semantic_matching(self, action: SemanticAction, 
                          current_screen: Optional[Image.Image]) -> Optional[Tuple[int, int]]:
        """의미론적 매칭으로 요소 찾기
        
        Requirements: 12.2, 12.3, 12.4
        
        Args:
            action: 찾을 액션
            current_screen: 현재 화면 이미지
            
        Returns:
            찾은 좌표 (x, y) 또는 None
        """
        if current_screen is None:
            current_screen = self._capture_screenshot()
        
        if current_screen is None:
            return None
        
        semantic_info = action.semantic_info
        if not semantic_info:
            return None
        
        target_element = semantic_info.get('target_element', {})
        
        try:
            # Vision LLM으로 현재 화면 분석
            ui_data = self.ui_analyzer.analyze_with_retry(current_screen)
            
            # _find_matching_element 활용
            best_match, best_score = self._find_matching_element(ui_data, target_element)
            
            # 최소 점수 임계값
            if best_score >= 0.3:
                logger.info(f"의미론적 매칭 발견: 점수 {best_score:.2f}, 좌표 {best_match}")
                return best_match
            
            return None
            
        except Exception as e:
            logger.error(f"의미론적 매칭 중 오류: {e}")
            return None

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 문자열의 유사도 계산
        
        Requirements: 3.2
        
        점수 우선순위:
        1. 완전 일치 → 1.0
        2. 문자 집합 유사도 (Jaccard) → 0.0 ~ 0.85
        3. 부분 문자열 포함 → 0.3 ~ 0.5 (폴백용, 낮은 신뢰도)
        
        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            
        Returns:
            유사도 점수 (0.0 ~ 1.0)
        """
        # None 또는 빈 문자열 처리
        if not text1 or not text2:
            return 0.0
        
        # 원본 텍스트가 동일하면 1.0 반환 (정규화 전 체크)
        if text1 == text2:
            return 1.0
        
        # 1. 정규화 (대소문자 무시, 공백 정규화)
        import re
        normalized1 = re.sub(r'\s+', ' ', str(text1).lower().strip())
        normalized2 = re.sub(r'\s+', ' ', str(text2).lower().strip())
        
        # 빈 문자열 처리 (정규화 후 둘 다 빈 문자열이면 동등하므로 1.0)
        if not normalized1 and not normalized2:
            return 1.0
        
        # 한쪽만 빈 문자열이면 0.0
        if not normalized1 or not normalized2:
            return 0.0
        
        # 2. 완전 일치 → 1.0
        if normalized1 == normalized2:
            return 1.0
        
        # 3. Jaccard 유사도 계산 (문자 집합 기반)
        set1 = set(normalized1)
        set2 = set(normalized2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        # 순서를 고려한 추가 점수 (연속 일치 문자)
        common_prefix_len = 0
        for c1, c2 in zip(normalized1, normalized2):
            if c1 == c2:
                common_prefix_len += 1
            else:
                break
        
        prefix_bonus = common_prefix_len / max(len(normalized1), len(normalized2)) * 0.15
        
        # Jaccard 점수: 0.0 ~ 0.85 범위
        jaccard_score = min(jaccard * 0.85 + prefix_bonus, 0.85)
        
        # 4. 부분 문자열 매칭 (Jaccard보다 낮은 점수로 폴백)
        shorter = normalized1 if len(normalized1) <= len(normalized2) else normalized2
        longer = normalized2 if len(normalized1) <= len(normalized2) else normalized1
        
        if shorter in longer:
            ratio = len(shorter) / len(longer)
            substring_score = 0.3 + (ratio * 0.2)  # 0.3 ~ 0.5 범위
            # Jaccard가 더 높으면 Jaccard 사용, 아니면 부분 문자열 점수
            return max(jaccard_score, substring_score)
        
        return jaccard_score

    def _calculate_match_score(self, element: Dict[str, Any],
                               expected_type: str,
                               expected_text: str,
                               expected_description: str) -> float:
        """요소 매칭 점수 계산
        
        Args:
            element: UI 요소 정보
            expected_type: 예상 타입
            expected_text: 예상 텍스트
            expected_description: 예상 설명
            
        Returns:
            매칭 점수 (0.0 ~ 1.0)
        """
        score = 0.0
        
        # 텍스트 매칭 (가장 중요) - _calculate_text_similarity 활용
        element_text = element.get('text', element.get('content', element.get('type', '')))
        
        if expected_text:
            text_similarity = self._calculate_text_similarity(expected_text, element_text)
            score += text_similarity * 0.5  # 텍스트 유사도에 0.5 가중치
        
        # 설명 매칭
        if expected_description and expected_text:
            desc_similarity = self._calculate_text_similarity(expected_text, expected_description)
            if desc_similarity > 0.5:
                element_text_lower = element_text.lower() if element_text else ''
                expected_text_lower = expected_text.lower() if expected_text else ''
                if expected_text_lower in element_text_lower:
                    score += 0.2
        
        # 타입 매칭
        element_type = element.get('type', '')
        if expected_type and expected_type == element_type:
            score += 0.2
        
        # 신뢰도 가중치
        confidence = element.get('confidence', 0.5)
        score *= (0.5 + confidence * 0.5)
        
        return min(score, 1.0)
    
    def _verify_screen_transition(self, action: SemanticAction, 
                                  result: ReplayResult,
                                  hash_before: Optional[str]) -> ReplayResult:
        """화면 전환 검증
        
        Requirements: 12.6, 12.7
        
        Args:
            action: 실행된 액션
            result: 현재 결과 객체
            hash_before: 액션 전 화면 해시
            
        Returns:
            업데이트된 ReplayResult
        """
        expected_transition = action.screen_transition.get('transition_type', 'unknown')
        result.expected_transition = expected_transition
        
        try:
            # 액션 후 스크린샷 캡처
            screenshot_after = self._capture_screenshot()
            if screenshot_after is None:
                result.screen_transition_verified = False
                result.actual_transition = 'capture_failed'
                return result
            
            hash_after = self._calculate_hash(screenshot_after)
            
            # 해시 차이 계산
            if hash_before:
                hash1 = imagehash.hex_to_hash(hash_before)
                hash2 = imagehash.hex_to_hash(hash_after)
                hash_diff = hash1 - hash2
                
                # 실제 전환 타입 결정
                if hash_diff == 0:
                    actual_transition = 'none'
                elif hash_diff < 10:
                    actual_transition = 'minor_change'
                elif hash_diff < 30:
                    actual_transition = 'partial_change'
                else:
                    actual_transition = 'full_transition'
                
                result.actual_transition = actual_transition
                
                # 전환 검증
                if expected_transition == 'unknown':
                    result.screen_transition_verified = True
                elif expected_transition == actual_transition:
                    result.screen_transition_verified = True
                    logger.info(f"화면 전환 검증 성공: {actual_transition}")
                else:
                    # 예상과 다른 전환 - 경고 로그 (Requirements: 12.7)
                    result.screen_transition_verified = False
                    logger.warning(
                        f"화면 전환 불일치: 예상 '{expected_transition}', "
                        f"실제 '{actual_transition}' (해시 차이: {hash_diff})"
                    )
            else:
                result.actual_transition = 'unknown'
                result.screen_transition_verified = True  # 비교 불가
        
        except Exception as e:
            logger.error(f"화면 전환 검증 실패: {e}")
            result.screen_transition_verified = False
            result.actual_transition = 'error'
        
        return result
    
    def replay_actions(self, actions: List[SemanticAction]) -> List[ReplayResult]:
        """여러 액션 순차 재실행
        
        Args:
            actions: 재실행할 액션 리스트
            
        Returns:
            ReplayResult 리스트
        """
        results = []
        
        for i, action in enumerate(actions):
            logger.info(f"액션 {i+1}/{len(actions)} 재실행: {action.description}")
            result = self.replay_action(action)
            results.append(result)
            
            if not result.success:
                logger.warning(f"액션 {i+1} 실패: {result.error_message}")
        
        return results
    
    def get_results(self) -> List[ReplayResult]:
        """재실행 결과 목록 반환
        
        Returns:
            ReplayResult 리스트
        """
        return self.results
    
    def clear_results(self):
        """재실행 결과 초기화"""
        self.results = []
        self._action_counter = 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """재실행 통계 계산
        
        Requirements: 4.1, 4.2, 4.3, 4.4
        
        Returns:
            통계 딕셔너리
        """
        if not self.results:
            return {
                "total_actions": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0,
                "direct_match_count": 0,
                "semantic_match_count": 0,
                "coordinate_match_count": 0,
                "failed_count": 0,
                "direct_match_rate": 0.0,
                "semantic_match_rate": 0.0,
                "coordinate_match_rate": 0.0,
                "avg_coordinate_change": 0.0,
                "max_coordinate_change": 0.0,
                "avg_match_confidence": 0.0,
                "transition_verified_count": 0,
                "transition_mismatch_count": 0
            }
        
        total = len(self.results)
        success_count = sum(1 for r in self.results if r.success)
        direct_count = sum(1 for r in self.results if r.method == 'direct')
        semantic_count = sum(1 for r in self.results if r.method == 'semantic')
        coordinate_count = sum(1 for r in self.results if r.method == 'coordinate')
        failed_count = sum(1 for r in self.results if r.method == 'failed')
        
        # 좌표 변경 거리 계산 (Requirements: 4.3)
        coord_changes = [
            (r.coordinate_change[0]**2 + r.coordinate_change[1]**2)**0.5
            for r in self.results
            if r.coordinate_change is not None
        ]
        avg_coord_change = sum(coord_changes) / len(coord_changes) if coord_changes else 0.0
        max_coord_change = max(coord_changes) if coord_changes else 0.0
        
        # 매칭 신뢰도 통계 (Requirements: 4.2)
        confidences = [r.match_confidence for r in self.results if r.match_confidence > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # 화면 전환 검증 통계
        transition_verified = sum(1 for r in self.results if r.screen_transition_verified)
        transition_mismatch = sum(
            1 for r in self.results 
            if r.success and not r.screen_transition_verified
        )
        
        return {
            "total_actions": total,
            "success_count": success_count,
            "failure_count": total - success_count,
            "success_rate": success_count / total if total > 0 else 0.0,
            "direct_match_count": direct_count,
            "semantic_match_count": semantic_count,
            "coordinate_match_count": coordinate_count,
            "failed_count": failed_count,
            "direct_match_rate": direct_count / total if total > 0 else 0.0,
            "semantic_match_rate": semantic_count / total if total > 0 else 0.0,
            "coordinate_match_rate": coordinate_count / total if total > 0 else 0.0,
            "avg_coordinate_change": avg_coord_change,
            "max_coordinate_change": max_coord_change,
            "avg_match_confidence": avg_confidence,
            "transition_verified_count": transition_verified,
            "transition_mismatch_count": transition_mismatch
        }
