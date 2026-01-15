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
    
    Requirements: 1.1, 1.3, 1.4, 2.1, 2.2, 2.3, 6.1, 6.2, 6.4, 6.5, 11.6
    
    Attributes:
        semantic_info: 의미론적 정보 딕셔너리. 클릭 대상 UI 요소의 의도, 타겟 요소, 맥락 정보를 포함.
            - intent: 액션의 의도 (예: "click_button", "start_game")
            - target_element: 클릭 대상 UI 요소 정보 (필수 필드: type, text, description, bounding_box, confidence)
            - context: 화면 상태 및 예상 결과 정보
        screen_transition: 화면 전환 정보 딕셔너리.
        screenshot_before_path: 클릭 직전 스크린샷 경로. Vision LLM 분석에 사용되며,
            의미론적 매칭 시 클릭 대상 UI 요소를 식별하는 데 활용됨. (Requirements: 1.1, 2.2)
        screenshot_after_path: 클릭 직후 스크린샷 경로. 화면 전환 검증에 사용됨.
        ui_state_hash_before: 클릭 전 UI 상태 해시. 화면 전환 검증용.
        ui_state_hash_after: 클릭 후 UI 상태 해시. 화면 전환 검증용.
    """
    
    # 의미론적 정보 (Requirements: 1.3, 1.4, 2.1, 2.3)
    # target_element 구조:
    # {
    #     "type": "button",           # UI 요소 타입 (필수)
    #     "text": "시작",              # UI 요소 텍스트 (필수)
    #     "description": "게임 시작 버튼",  # 설명 (필수)
    #     "bounding_box": {           # 경계 상자 (필수, Requirements: 2.3)
    #         "x": 100,               # 좌상단 X 좌표
    #         "y": 200,               # 좌상단 Y 좌표
    #         "width": 80,            # 너비
    #         "height": 40            # 높이
    #     },
    #     "confidence": 0.95          # 신뢰도 0.0~1.0 (필수, Requirements: 1.4)
    # }
    semantic_info: Dict[str, Any] = field(default_factory=dict)
    # {
    #     "intent": "enter_game",
    #     "target_element": {
    #         "type": "button",
    #         "text": "입장",
    #         "description": "게임 입장 버튼",
    #         "bounding_box": {"x": 100, "y": 200, "width": 80, "height": 40},
    #         "confidence": 0.95
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
    #     "transition_type": "navigation",
    #     "hash_difference": 45
    # }
    
    # 클릭 직전 스크린샷 경로 (Requirements: 1.1, 2.2)
    # 용도: Vision LLM 분석을 통해 클릭 대상 UI 요소의 의미론적 정보를 추출하는 데 사용.
    # 재현 시 의미론적 매칭의 기준이 되는 원본 UI 상태를 보존함.
    screenshot_before_path: Optional[str] = None
    
    # 클릭 직후 스크린샷 경로
    # 용도: 화면 전환 검증 및 기존 검증 기능 유지에 사용.
    screenshot_after_path: Optional[str] = None
    
    # 클릭 좌표 주변 크롭 이미지 경로 (200x200)
    # 용도: Vision LLM이 UI 요소를 감지하지 못했을 때, 클릭 좌표 주변 영역을 저장하여
    # 재현 시 시각적 참고 및 템플릿 매칭에 활용함.
    click_region_crop_path: Optional[str] = None
    
    # UI 상태 해시 (화면 전환 검증용)
    ui_state_hash_before: Optional[str] = None
    ui_state_hash_after: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """SemanticAction을 딕셔너리로 직렬화
        
        모든 필드를 포함하며, None 값은 일관되게 None으로 유지함.
        빈 딕셔너리는 빈 딕셔너리로 유지하여 역직렬화 시 동일한 구조를 복원함.
        
        Requirements: 6.1, 6.4, 6.5
        
        Returns:
            JSON 직렬화 가능한 딕셔너리
        """
        # 중첩 딕셔너리의 깊은 복사를 통해 원본 데이터 보호
        semantic_info_copy = {}
        if self.semantic_info:
            semantic_info_copy = {
                "intent": self.semantic_info.get("intent"),
                "target_element": dict(self.semantic_info.get("target_element", {})) if self.semantic_info.get("target_element") else {},
                "context": dict(self.semantic_info.get("context", {})) if self.semantic_info.get("context") else {}
            }
            # target_element 내부의 bounding_box도 깊은 복사
            if semantic_info_copy.get("target_element") and semantic_info_copy["target_element"].get("bounding_box"):
                semantic_info_copy["target_element"]["bounding_box"] = dict(
                    semantic_info_copy["target_element"]["bounding_box"]
                )
        
        screen_transition_copy = dict(self.screen_transition) if self.screen_transition else {}
        
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
            "semantic_info": semantic_info_copy,
            "screen_transition": screen_transition_copy
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticAction':
        """딕셔너리에서 SemanticAction 복원
        
        모든 중첩 구조를 완전히 복원하며, 누락된 필드는 기본값으로 처리함.
        중첩 딕셔너리(semantic_info, screen_transition)는 깊은 복사하여 원본 데이터 보호.
        
        Requirements: 6.2, 6.4, 6.5
        
        Args:
            data: 직렬화된 딕셔너리
            
        Returns:
            복원된 SemanticAction 인스턴스
        """
        # semantic_info 깊은 복사 및 복원
        raw_semantic_info = data.get("semantic_info", {})
        semantic_info = {}
        if raw_semantic_info:
            semantic_info["intent"] = raw_semantic_info.get("intent")
            
            # target_element 복원 (중첩 구조)
            raw_target = raw_semantic_info.get("target_element", {})
            if raw_target:
                target_element = {
                    "type": raw_target.get("type", "unknown"),
                    "text": raw_target.get("text", ""),
                    "description": raw_target.get("description", ""),
                    "confidence": raw_target.get("confidence", 0.0)
                }
                # bounding_box 복원
                raw_bbox = raw_target.get("bounding_box", {})
                if raw_bbox:
                    target_element["bounding_box"] = {
                        "x": raw_bbox.get("x", 0),
                        "y": raw_bbox.get("y", 0),
                        "width": raw_bbox.get("width", 0),
                        "height": raw_bbox.get("height", 0)
                    }
                else:
                    target_element["bounding_box"] = {"x": 0, "y": 0, "width": 0, "height": 0}
                # visual_features가 있으면 복원 (레거시 호환)
                if "visual_features" in raw_target:
                    target_element["visual_features"] = dict(raw_target.get("visual_features", {}))
                semantic_info["target_element"] = target_element
            else:
                semantic_info["target_element"] = {}
            
            # context 복원
            raw_context = raw_semantic_info.get("context", {})
            if raw_context:
                semantic_info["context"] = {
                    "screen_state": raw_context.get("screen_state", "unknown"),
                    "expected_result": raw_context.get("expected_result", "unknown")
                }
            else:
                semantic_info["context"] = {}
        
        # screen_transition 깊은 복사
        raw_transition = data.get("screen_transition", {})
        screen_transition = {}
        if raw_transition:
            screen_transition = {
                "before_state": raw_transition.get("before_state", "unknown"),
                "after_state": raw_transition.get("after_state", "unknown"),
                "transition_type": raw_transition.get("transition_type", "none"),
                "hash_difference": raw_transition.get("hash_difference", 0)
            }
        
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
            semantic_info=semantic_info,
            screen_transition=screen_transition
        )
    
    def __eq__(self, other: object) -> bool:
        """두 SemanticAction의 동등성 비교
        
        Requirements: 6.3
        
        Args:
            other: 비교 대상 객체
            
        Returns:
            동등 여부
        """
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
            self.ui_state_hash_before == other.ui_state_hash_before and
            self.ui_state_hash_after == other.ui_state_hash_after and
            self.semantic_info == other.semantic_info and
            self.screen_transition == other.screen_transition
        )


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
        
        Requirements: 1.3, 1.4, 2.1, 2.3, 11.2, 11.3
        
        Args:
            image: 분석할 이미지
            x: X 좌표
            y: Y 좌표
            
        Returns:
            표준화된 target_element 구조:
            - type: UI 요소 타입 (필수)
            - text: UI 요소 텍스트 (필수)
            - description: 설명 (필수)
            - bounding_box: 경계 상자 {"x", "y", "width", "height"} (필수)
            - confidence: 신뢰도 0.0~1.0 (필수)
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
                "bounding_box": {"x": x, "y": y, "width": 0, "height": 0},
                "confidence": 0.0
            }
    
    def _find_closest_element(self, ui_data: dict, x: int, y: int) -> Dict[str, Any]:
        """클릭 좌표와 가장 가까운 UI 요소 찾기
        
        Requirements: 1.3, 1.4, 2.1, 2.3
        
        Args:
            ui_data: UI 분석 결과
            x: X 좌표
            y: Y 좌표
            
        Returns:
            가장 가까운 UI 요소 정보 (표준화된 target_element 구조)
            - type: UI 요소 타입 (필수)
            - text: UI 요소 텍스트 (필수)
            - description: 설명 (필수)
            - bounding_box: 경계 상자 {"x", "y", "width", "height"} (필수)
            - confidence: 신뢰도 0.0~1.0 (필수)
        """
        closest = None
        min_distance = float('inf')
        
        # 버튼 검색
        for button in ui_data.get('buttons', []):
            bx, by = button.get('x', 0), button.get('y', 0)
            distance = ((bx - x) ** 2 + (by - y) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                width = button.get('width', 0)
                height = button.get('height', 0)
                # bounding_box 구성: 중심 좌표에서 좌상단 좌표로 변환
                bbox = button.get('bounding_box', {
                    "x": bx - width // 2 if width else bx,
                    "y": by - height // 2 if height else by,
                    "width": width,
                    "height": height
                })
                closest = {
                    "type": "button",
                    "text": button.get('text', ''),
                    "description": f"버튼: {button.get('text', '')}",
                    "bounding_box": bbox,
                    "confidence": button.get('confidence', 0.0)
                }
        
        # 아이콘 검색
        for icon in ui_data.get('icons', []):
            ix, iy = icon.get('x', 0), icon.get('y', 0)
            distance = ((ix - x) ** 2 + (iy - y) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                width = icon.get('width', 0)
                height = icon.get('height', 0)
                bbox = icon.get('bounding_box', {
                    "x": ix - width // 2 if width else ix,
                    "y": iy - height // 2 if height else iy,
                    "width": width,
                    "height": height
                })
                closest = {
                    "type": "icon",
                    "text": icon.get('type', ''),
                    "description": f"아이콘: {icon.get('type', '')}",
                    "bounding_box": bbox,
                    "confidence": icon.get('confidence', 0.0)
                }
        
        # 텍스트 필드 검색
        for text_field in ui_data.get('text_fields', []):
            tx, ty = text_field.get('x', 0), text_field.get('y', 0)
            distance = ((tx - x) ** 2 + (ty - y) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                width = text_field.get('width', 0)
                height = text_field.get('height', 0)
                bbox = text_field.get('bounding_box', {
                    "x": tx - width // 2 if width else tx,
                    "y": ty - height // 2 if height else ty,
                    "width": width,
                    "height": height
                })
                closest = {
                    "type": "text_field",
                    "text": text_field.get('content', ''),
                    "description": f"텍스트: {text_field.get('content', '')}",
                    "bounding_box": bbox,
                    "confidence": text_field.get('confidence', 0.0)
                }
        
        # 가까운 요소가 없으면 기본값 반환 (표준화된 구조)
        if closest is None:
            return {
                "type": "unknown",
                "text": "",
                "description": f"좌표 ({x}, {y})의 알 수 없는 요소",
                "bounding_box": {"x": x, "y": y, "width": 0, "height": 0},
                "confidence": 0.0
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

    def record_click_with_semantic_analysis(
        self, 
        x: int, 
        y: int, 
        button: str = 'left',
        perform_click: bool = False,
        click_delay: float = 0.3
    ) -> SemanticAction:
        """클릭 전 의미론적 분석을 수행하여 액션 기록
        
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
        
        이 메서드는 클릭 직전에 스크린샷을 캡처하고, Vision LLM으로 클릭 좌표의
        UI 요소를 분석하여 semantic_info를 구성한다. 분석 실패 시 OCR 폴백을 사용한다.
        
        Args:
            x: 클릭 X 좌표
            y: 클릭 Y 좌표
            button: 마우스 버튼 ('left', 'right', 'middle')
            perform_click: True이면 실제 클릭 수행, False이면 기록만
            click_delay: 클릭 후 스크린샷 캡처 전 대기 시간 (초)
            
        Returns:
            의미론적 정보가 추가된 SemanticAction
        """
        self._action_counter += 1
        
        # 1. 클릭 직전 스크린샷 캡처 (Requirements: 1.1)
        image_before, path_before, hash_before = self._capture_screenshot("before")
        
        # 기본 액션 생성
        timestamp = datetime.now().isoformat()
        
        # SemanticAction 생성
        semantic_action = SemanticAction(
            timestamp=timestamp,
            action_type='click',
            x=x,
            y=y,
            description=f'클릭 ({x}, {y})',
            button=button,
            screenshot_before_path=path_before,
            ui_state_hash_before=hash_before
        )
        
        # 2. Vision LLM으로 클릭 좌표의 UI 요소 분석 (Requirements: 1.2, 1.3)
        target_element = self._analyze_target_element(image_before, x, y)
        
        # 3. 실제 클릭 수행 (선택적)
        if perform_click:
            pyautogui.click(x, y, button=button)
        
        # 4. 클릭 후 스크린샷 캡처 (기존 검증용 유지)
        import time
        time.sleep(click_delay)  # 화면 전환 대기
        
        image_after, path_after, hash_after = self._capture_screenshot("after")
        
        if image_after:
            semantic_action.screenshot_after_path = path_after
            semantic_action.screenshot_path = path_after  # 기존 호환성
            semantic_action.ui_state_hash_after = hash_after
            
            # 화면 전환 분석
            if image_before:
                transition = self._analyze_screen_transition(
                    hash_before, hash_after, image_before, image_after
                )
                semantic_action.screen_transition = transition
        
        # 의도 추론
        action = Action(
            timestamp=timestamp,
            action_type='click',
            x=x,
            y=y,
            description=f'클릭 ({x}, {y})',
            button=button
        )
        intent = self._infer_intent(action, target_element)
        
        # semantic_info 구성 및 저장 (Requirements: 1.4)
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
        
        logger.info(f"의미론적 클릭 분석 완료: ({x}, {y}), "
                   f"요소: {target_element.get('type', 'unknown')}, "
                   f"신뢰도: {target_element.get('confidence', 0.0):.2f}")
        
        return semantic_action

    def _analyze_target_element(
        self, 
        image: Optional[Image.Image], 
        x: int, 
        y: int
    ) -> Dict[str, Any]:
        """클릭 좌표의 UI 요소 분석 및 target_element 구성
        
        Requirements: 1.3, 1.5
        
        UIAnalyzer.find_element_at_position()을 활용하여 클릭 좌표의 UI 요소를 분석하고,
        표준화된 target_element 구조를 생성한다. Vision LLM 실패 시 OCR 폴백을 사용한다.
        
        Args:
            image: 분석할 이미지 (None이면 빈 결과 반환)
            x: 클릭 X 좌표
            y: 클릭 Y 좌표
            
        Returns:
            target_element 구조:
            - type: UI 요소 타입 (필수)
            - text: UI 요소 텍스트 (필수)
            - description: 설명 (필수)
            - bounding_box: 경계 상자 {"x", "y", "width", "height"} (필수)
            - confidence: 신뢰도 0.0~1.0 (필수)
        """
        # 기본 target_element 구조
        default_target = {
            "type": "unknown",
            "text": "",
            "description": f"좌표 ({x}, {y})의 알 수 없는 요소",
            "bounding_box": {"x": x, "y": y, "width": 0, "height": 0},
            "confidence": 0.0
        }
        
        if image is None:
            logger.warning("분석할 이미지가 없습니다")
            return default_target
        
        try:
            # Vision LLM으로 전체 UI 분석 (재시도 로직 포함)
            ui_data = self.ui_analyzer.analyze_with_retry(image)
            
            # 분석 소스 확인
            source = ui_data.get("source", "unknown")
            
            if source == "failed":
                # Vision LLM과 OCR 모두 실패
                logger.warning(f"UI 분석 실패: {ui_data.get('error', 'unknown error')}")
                return default_target
            
            # UIAnalyzer.find_element_at_position() 활용
            element = self.ui_analyzer.find_element_at_position(ui_data, x, y)
            
            if element is None:
                # tolerance 범위 내에 요소가 없음
                logger.info(f"좌표 ({x}, {y}) 근처에 UI 요소가 없습니다")
                
                # OCR 폴백 결과인 경우 텍스트 필드에서 가장 가까운 것 찾기
                if source == "ocr_fallback" and ui_data.get("text_fields"):
                    return self._find_closest_ocr_text(ui_data["text_fields"], x, y)
                
                return default_target
            
            # target_element 구조 생성
            element_type = element.get("element_type", element.get("type", "unknown"))
            
            # 텍스트 추출 (요소 타입에 따라 다른 필드 사용)
            if element_type == "text_field":
                text = element.get("content", element.get("text", ""))
            else:
                text = element.get("text", element.get("type", ""))
            
            # description 생성
            description = element.get("description", f"{element_type}: {text}")
            
            # bounding_box 추출 또는 계산
            bounding_box = element.get("bounding_box")
            if not bounding_box or not isinstance(bounding_box, dict):
                # bounding_box가 없으면 중심 좌표와 크기로 계산
                elem_x = element.get("x", x)
                elem_y = element.get("y", y)
                width = element.get("width", 0)
                height = element.get("height", 0)
                bounding_box = {
                    "x": int(elem_x - width / 2) if width > 0 else elem_x,
                    "y": int(elem_y - height / 2) if height > 0 else elem_y,
                    "width": int(width),
                    "height": int(height)
                }
            
            target_element = {
                "type": element_type,
                "text": text,
                "description": description,
                "bounding_box": bounding_box,
                "confidence": element.get("confidence", 0.0)
            }
            
            logger.debug(f"target_element 생성: {target_element}")
            return target_element
            
        except Exception as e:
            logger.error(f"target_element 분석 실패: {e}")
            return default_target

    def _find_closest_ocr_text(
        self, 
        text_fields: List[Dict[str, Any]], 
        x: int, 
        y: int
    ) -> Dict[str, Any]:
        """OCR 결과에서 가장 가까운 텍스트 요소 찾기
        
        Requirements: 1.5
        
        Args:
            text_fields: OCR 텍스트 필드 리스트
            x: 클릭 X 좌표
            y: 클릭 Y 좌표
            
        Returns:
            가장 가까운 텍스트 요소의 target_element 구조
        """
        if not text_fields:
            return {
                "type": "unknown",
                "text": "",
                "description": f"좌표 ({x}, {y})의 알 수 없는 요소",
                "bounding_box": {"x": x, "y": y, "width": 0, "height": 0},
                "confidence": 0.0
            }
        
        closest = None
        min_distance = float('inf')
        
        for field in text_fields:
            fx = field.get("x", 0)
            fy = field.get("y", 0)
            distance = ((fx - x) ** 2 + (fy - y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest = field
        
        if closest:
            text = closest.get("content", closest.get("text", ""))
            return {
                "type": "text_field",
                "text": text,
                "description": f"OCR 텍스트: {text}",
                "bounding_box": closest.get("bounding_box", {
                    "x": closest.get("x", x),
                    "y": closest.get("y", y),
                    "width": 0,
                    "height": 0
                }),
                "confidence": closest.get("confidence", 0.5)  # OCR 폴백은 기본 신뢰도 0.5
            }
        
        return {
            "type": "unknown",
            "text": "",
            "description": f"좌표 ({x}, {y})의 알 수 없는 요소",
            "bounding_box": {"x": x, "y": y, "width": 0, "height": 0},
            "confidence": 0.0
        }
    
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
        return [action.to_dict() for action in self.semantic_actions]
    
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
            action = SemanticAction.from_dict(item)
            recorder.semantic_actions.append(action)
        
        return recorder
