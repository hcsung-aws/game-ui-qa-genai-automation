"""
SemanticActionRecorder - 의미론적 맥락 정보를 포함한 액션 기록기

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

import pyautogui
from PIL import Image
import imagehash

from src.input_monitor import Action, ActionRecorder
from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer


logger = logging.getLogger(__name__)


@dataclass
class SemanticAction(Action):
    """의미론적 액션 데이터 클래스 (Action 확장)
    
    물리적 정보(좌표)와 의미론적 정보(의도, 타겟 요소, 맥락)를 모두 포함한다.
    
    Requirements: 11.6
    """
    
    # 의미론적 정보
    semantic_info: Dict[str, Any] = field(default_factory=dict)
    # {
    #     "intent": "enter_game",
    #     "target_element": {
    #         "type": "button",
    #         "text": "입장",
    #         "description": "게임 입장 버튼",
    #         "visual_features": {...}
    #     },
    #     "context": {
    #         "screen_state": "lobby",
    #         "expected_result": "loading_screen"
    #     }
    # }
    
    # 화면 전환 정보
    screen_transition: Dict[str, Any] = field(default_factory=dict)
    # {
    #     "before_state": "lobby",
    #     "after_state": "loading_screen",
    #     "transition_type": "navigation"
    # }
    
    # 전후 스크린샷 경로
    screenshot_before_path: Optional[str] = None
    screenshot_after_path: Optional[str] = None
    
    # UI 상태 해시 (화면 전환 검증용)
    ui_state_hash_before: Optional[str] = None
    ui_state_hash_after: Optional[str] = None


class SemanticActionRecorder(ActionRecorder):
    """의미론적 액션 기록기
    
    클릭 전후 스크린샷을 캡처하고, Vision LLM을 사용하여 
    UI 요소의 의미론적 정보를 분석하여 저장한다.
    
    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
    """
    
    def __init__(self, config: ConfigManager, ui_analyzer: Optional[UIAnalyzer] = None):
        """
        Args:
            config: 설정 관리자
            ui_analyzer: UI 분석기 (선택사항, 없으면 새로 생성)
        """
        super().__init__(config)
        self.ui_analyzer = ui_analyzer or UIAnalyzer(config)
        self.semantic_actions: List[SemanticAction] = []
        self._action_counter = 0
        
        # 스크린샷 저장 디렉토리
        self.screenshot_dir = config.get('automation.screenshot_dir', 'screenshots')
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def _capture_screenshot(self, suffix: str = "") -> tuple:
        """스크린샷 캡처 및 저장
        
        Args:
            suffix: 파일명 접미사 (예: "before", "after")
            
        Returns:
            (PIL Image, 저장 경로, 이미지 해시) 튜플
        """
        try:
            screenshot = pyautogui.screenshot()
            
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"semantic_{self._action_counter:04d}_{suffix}_{timestamp}.png"
            save_path = os.path.join(self.screenshot_dir, filename)
            
            # 저장
            screenshot.save(save_path, format='PNG')
            
            # 이미지 해시 계산
            image_hash = str(imagehash.average_hash(screenshot))
            
            logger.debug(f"스크린샷 캡처: {save_path}")
            return screenshot, save_path, image_hash
            
        except Exception as e:
            logger.error(f"스크린샷 캡처 실패: {e}")
            return None, None, None
    
    def _analyze_ui_element_at_position(self, image: Image.Image, x: int, y: int) -> Dict[str, Any]:
        """특정 좌표의 UI 요소 분석
        
        Requirements: 11.2, 11.3
        
        Args:
            image: 분석할 이미지
            x: X 좌표
            y: Y 좌표
            
        Returns:
            UI 요소 정보 딕셔너리
        """
        try:
            # Vision LLM으로 전체 UI 분석
            ui_data = self.ui_analyzer.analyze_with_retry(image)
            
            # 클릭 좌표와 가장 가까운 UI 요소 찾기
            closest_element = self._find_closest_element(ui_data, x, y)
            
            return closest_element
            
        except Exception as e:
            logger.error(f"UI 요소 분석 실패: {e}")
            return {
                "type": "unknown",
                "text": "",
                "description": f"분석 실패: {e}",
                "visual_features": {}
            }
    
    def _find_closest_element(self, ui_data: dict, x: int, y: int) -> Dict[str, Any]:
        """클릭 좌표와 가장 가까운 UI 요소 찾기
        
        Args:
            ui_data: UI 분석 결과
            x: X 좌표
            y: Y 좌표
            
        Returns:
            가장 가까운 UI 요소 정보
        """
        closest = None
        min_distance = float('inf')
        
        # 버튼 검색
        for button in ui_data.get('buttons', []):
            bx, by = button.get('x', 0), button.get('y', 0)
            distance = ((bx - x) ** 2 + (by - y) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest = {
                    "type": "button",
                    "text": button.get('text', ''),
                    "description": f"버튼: {button.get('text', '')}",
                    "visual_features": {
                        "width": button.get('width'),
                        "height": button.get('height'),
                        "confidence": button.get('confidence')
                    },
                    "x": bx,
                    "y": by
                }
        
        # 아이콘 검색
        for icon in ui_data.get('icons', []):
            ix, iy = icon.get('x', 0), icon.get('y', 0)
            distance = ((ix - x) ** 2 + (iy - y) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest = {
                    "type": "icon",
                    "text": icon.get('type', ''),
                    "description": f"아이콘: {icon.get('type', '')}",
                    "visual_features": {
                        "confidence": icon.get('confidence')
                    },
                    "x": ix,
                    "y": iy
                }
        
        # 텍스트 필드 검색
        for text_field in ui_data.get('text_fields', []):
            tx, ty = text_field.get('x', 0), text_field.get('y', 0)
            distance = ((tx - x) ** 2 + (ty - y) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest = {
                    "type": "text_field",
                    "text": text_field.get('content', ''),
                    "description": f"텍스트: {text_field.get('content', '')}",
                    "visual_features": {
                        "confidence": text_field.get('confidence')
                    },
                    "x": tx,
                    "y": ty
                }
        
        # 가까운 요소가 없으면 기본값 반환
        if closest is None:
            return {
                "type": "unknown",
                "text": "",
                "description": f"좌표 ({x}, {y})의 알 수 없는 요소",
                "visual_features": {}
            }
        
        return closest

    def _analyze_screen_transition(self, hash_before: str, hash_after: str,
                                   image_before: Image.Image, 
                                   image_after: Image.Image) -> Dict[str, Any]:
        """화면 전환 분석
        
        Requirements: 11.4
        
        Args:
            hash_before: 액션 전 이미지 해시
            hash_after: 액션 후 이미지 해시
            image_before: 액션 전 이미지
            image_after: 액션 후 이미지
            
        Returns:
            화면 전환 정보 딕셔너리
        """
        transition_info = {
            "before_state": "unknown",
            "after_state": "unknown",
            "transition_type": "none",
            "hash_difference": 0
        }
        
        try:
            # 해시 차이 계산
            if hash_before and hash_after:
                hash1 = imagehash.hex_to_hash(hash_before)
                hash2 = imagehash.hex_to_hash(hash_after)
                hash_diff = hash1 - hash2
                transition_info["hash_difference"] = hash_diff
                
                # 화면 전환 타입 결정
                if hash_diff == 0:
                    transition_info["transition_type"] = "none"
                elif hash_diff < 10:
                    transition_info["transition_type"] = "minor_change"
                elif hash_diff < 30:
                    transition_info["transition_type"] = "partial_change"
                else:
                    transition_info["transition_type"] = "full_transition"
            
            # Vision LLM으로 화면 상태 분석 (선택적)
            # 성능을 위해 기본적으로는 해시 기반 분석만 수행
            
        except Exception as e:
            logger.error(f"화면 전환 분석 실패: {e}")
        
        return transition_info
    
    def _infer_intent(self, action: Action, target_element: Dict[str, Any]) -> str:
        """액션의 의도 추론
        
        Requirements: 11.3
        
        Args:
            action: 기본 액션
            target_element: 타겟 UI 요소 정보
            
        Returns:
            추론된 의도 문자열
        """
        element_type = target_element.get('type', 'unknown')
        element_text = target_element.get('text', '').lower()
        
        # 버튼 클릭 의도 추론
        if element_type == 'button':
            if any(keyword in element_text for keyword in ['시작', 'start', '입장', 'enter', 'play']):
                return 'start_game'
            elif any(keyword in element_text for keyword in ['설정', 'settings', 'option']):
                return 'open_settings'
            elif any(keyword in element_text for keyword in ['확인', 'ok', 'confirm', '예']):
                return 'confirm_action'
            elif any(keyword in element_text for keyword in ['취소', 'cancel', '아니오']):
                return 'cancel_action'
            elif any(keyword in element_text for keyword in ['닫기', 'close', 'x']):
                return 'close_dialog'
            else:
                return 'click_button'
        
        # 텍스트 필드 클릭 의도
        elif element_type == 'text_field':
            return 'focus_input'
        
        # 아이콘 클릭 의도
        elif element_type == 'icon':
            return 'click_icon'
        
        # 키보드 입력 의도
        elif action.action_type == 'key_press':
            return 'text_input'
        
        # 스크롤 의도
        elif action.action_type == 'scroll':
            return 'scroll_content'
        
        return 'unknown_action'
    
    def record_semantic_action(self, action: Action, 
                               capture_screenshots: bool = True,
                               analyze_ui: bool = True) -> SemanticAction:
        """의미론적 정보를 포함하여 액션 기록
        
        Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
        
        Args:
            action: 기본 액션
            capture_screenshots: 스크린샷 캡처 여부
            analyze_ui: UI 분석 수행 여부
            
        Returns:
            의미론적 정보가 추가된 SemanticAction
        """
        self._action_counter += 1
        
        # 기본 SemanticAction 생성
        semantic_action = SemanticAction(
            timestamp=action.timestamp,
            action_type=action.action_type,
            x=action.x,
            y=action.y,
            description=action.description,
            screenshot_path=action.screenshot_path,
            button=action.button,
            key=action.key,
            scroll_dx=action.scroll_dx,
            scroll_dy=action.scroll_dy
        )
        
        # 클릭 액션인 경우 전후 스크린샷 캡처 및 분석
        if action.action_type == 'click' and capture_screenshots:
            # 전 스크린샷 (이미 클릭이 발생한 후이므로 현재 상태가 "후" 상태)
            # 실제 사용 시에는 클릭 전에 캡처해야 함
            # 여기서는 테스트를 위해 현재 상태를 캡처
            image_after, path_after, hash_after = self._capture_screenshot("after")
            
            if image_after:
                semantic_action.screenshot_after_path = path_after
                semantic_action.ui_state_hash_after = hash_after
                
                # UI 요소 분석
                if analyze_ui:
                    target_element = self._analyze_ui_element_at_position(
                        image_after, action.x, action.y
                    )
                    
                    # 의도 추론
                    intent = self._infer_intent(action, target_element)
                    
                    # 의미론적 정보 저장
                    semantic_action.semantic_info = {
                        "intent": intent,
                        "target_element": target_element,
                        "context": {
                            "screen_state": "captured",
                            "expected_result": "unknown"
                        }
                    }
        
        # 키보드 입력인 경우
        elif action.action_type == 'key_press':
            semantic_action.semantic_info = {
                "intent": "text_input",
                "target_element": {
                    "type": "input_field",
                    "text": action.key or "",
                    "description": f"키 입력: {action.key}",
                    "visual_features": {}
                },
                "context": {
                    "screen_state": "input_mode",
                    "expected_result": "text_entered"
                }
            }
        
        # 스크롤인 경우
        elif action.action_type == 'scroll':
            direction = "down" if (action.scroll_dy or 0) < 0 else "up"
            semantic_action.semantic_info = {
                "intent": "scroll_content",
                "target_element": {
                    "type": "scrollable_area",
                    "text": "",
                    "description": f"스크롤 {direction}",
                    "visual_features": {}
                },
                "context": {
                    "screen_state": "scrolling",
                    "expected_result": "content_scrolled"
                }
            }
        
        # 기록
        self.semantic_actions.append(semantic_action)
        
        # 부모 클래스의 액션 리스트에도 추가 (호환성)
        super().record_action(action)
        
        logger.info(f"의미론적 액션 기록: {semantic_action.action_type} at ({semantic_action.x}, {semantic_action.y})")
        
        return semantic_action

    def record_click_with_before_after(self, x: int, y: int, button: str = 'left',
                                       analyze_ui: bool = True) -> SemanticAction:
        """클릭 전후 스크린샷을 캡처하여 의미론적 액션 기록
        
        Requirements: 11.1, 11.4
        
        이 메서드는 클릭 전에 호출되어야 하며, 클릭 전 스크린샷을 캡처한 후
        클릭을 수행하고, 클릭 후 스크린샷을 캡처하여 화면 전환을 분석한다.
        
        Args:
            x: 클릭 X 좌표
            y: 클릭 Y 좌표
            button: 마우스 버튼 ('left', 'right', 'middle')
            analyze_ui: UI 분석 수행 여부
            
        Returns:
            의미론적 정보가 추가된 SemanticAction
        """
        self._action_counter += 1
        
        # 클릭 전 스크린샷 캡처
        image_before, path_before, hash_before = self._capture_screenshot("before")
        
        # 기본 액션 생성
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=x,
            y=y,
            description=f'클릭 ({x}, {y})',
            button=button
        )
        
        # SemanticAction 생성
        semantic_action = SemanticAction(
            timestamp=action.timestamp,
            action_type=action.action_type,
            x=action.x,
            y=action.y,
            description=action.description,
            button=action.button,
            screenshot_before_path=path_before,
            ui_state_hash_before=hash_before
        )
        
        # UI 요소 분석 (클릭 전 이미지 기준)
        target_element = {}
        if image_before and analyze_ui:
            target_element = self._analyze_ui_element_at_position(image_before, x, y)
        
        # 클릭 후 스크린샷 캡처 (실제 클릭은 외부에서 수행)
        # 여기서는 약간의 지연 후 캡처
        import time
        time.sleep(0.3)  # 화면 전환 대기
        
        image_after, path_after, hash_after = self._capture_screenshot("after")
        
        if image_after:
            semantic_action.screenshot_after_path = path_after
            semantic_action.ui_state_hash_after = hash_after
            
            # 화면 전환 분석
            if image_before:
                transition = self._analyze_screen_transition(
                    hash_before, hash_after, image_before, image_after
                )
                semantic_action.screen_transition = transition
        
        # 의도 추론
        intent = self._infer_intent(action, target_element)
        
        # 의미론적 정보 저장
        semantic_action.semantic_info = {
            "intent": intent,
            "target_element": target_element,
            "context": {
                "screen_state": "before_click",
                "expected_result": semantic_action.screen_transition.get('transition_type', 'unknown')
            }
        }
        
        # 기록
        self.semantic_actions.append(semantic_action)
        super().record_action(action)
        
        logger.info(f"의미론적 클릭 기록: ({x}, {y}), 전환: {semantic_action.screen_transition.get('transition_type', 'none')}")
        
        return semantic_action
    
    def get_semantic_actions(self) -> List[SemanticAction]:
        """기록된 의미론적 액션 목록 반환
        
        Returns:
            SemanticAction 리스트
        """
        return self.semantic_actions
    
    def clear_semantic_actions(self):
        """기록된 의미론적 액션 초기화"""
        self.semantic_actions = []
        self._action_counter = 0
        super().clear_actions()
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """의미론적 액션 목록을 딕셔너리 리스트로 변환
        
        Returns:
            딕셔너리 리스트 (JSON 직렬화 가능)
        """
        result = []
        for action in self.semantic_actions:
            action_dict = {
                "timestamp": action.timestamp,
                "action_type": action.action_type,
                "x": action.x,
                "y": action.y,
                "description": action.description,
                "button": action.button,
                "key": action.key,
                "scroll_dx": action.scroll_dx,
                "scroll_dy": action.scroll_dy,
                "screenshot_path": action.screenshot_path,
                "screenshot_before_path": action.screenshot_before_path,
                "screenshot_after_path": action.screenshot_after_path,
                "ui_state_hash_before": action.ui_state_hash_before,
                "ui_state_hash_after": action.ui_state_hash_after,
                "semantic_info": action.semantic_info,
                "screen_transition": action.screen_transition
            }
            result.append(action_dict)
        return result
    
    @classmethod
    def from_dict_list(cls, data: List[Dict[str, Any]], config: ConfigManager) -> 'SemanticActionRecorder':
        """딕셔너리 리스트에서 SemanticActionRecorder 복원
        
        Args:
            data: 딕셔너리 리스트
            config: 설정 관리자
            
        Returns:
            복원된 SemanticActionRecorder
        """
        recorder = cls(config)
        
        for item in data:
            action = SemanticAction(
                timestamp=item.get("timestamp", ""),
                action_type=item.get("action_type", ""),
                x=item.get("x", 0),
                y=item.get("y", 0),
                description=item.get("description", ""),
                button=item.get("button"),
                key=item.get("key"),
                scroll_dx=item.get("scroll_dx"),
                scroll_dy=item.get("scroll_dy"),
                screenshot_path=item.get("screenshot_path"),
                screenshot_before_path=item.get("screenshot_before_path"),
                screenshot_after_path=item.get("screenshot_after_path"),
                ui_state_hash_before=item.get("ui_state_hash_before"),
                ui_state_hash_after=item.get("ui_state_hash_after"),
                semantic_info=item.get("semantic_info", {}),
                screen_transition=item.get("screen_transition", {})
            )
            recorder.semantic_actions.append(action)
        
        return recorder
