# 의미론적 액션 및 오차율 측정 설계 (Design Document - Semantic Actions & Accuracy Tracking)

이 문서는 game-qa-automation의 design.md에 추가될 내용입니다.

---

## Semantic Action Recording (의미론적 액션 기록)

### 개요

단순히 좌표만 기록하는 것이 아니라, 사용자 액션의 **의도와 맥락**을 함께 저장하여 UI 변경에 강건한 테스트를 만든다.

### SemanticAction 데이터 모델

```python
@dataclass
class SemanticAction:
    """의미론적 액션 데이터 클래스"""
    
    # 기본 정보
    timestamp: str
    action_type: str  # 'click', 'key_press', 'scroll'
    
    # 물리적 정보
    x: int
    y: int
    button: str = None  # 'left', 'right', 'middle'
    key: str = None
    scroll_dx: int = None
    scroll_dy: int = None
    
    # 의미론적 정보
    semantic_info: dict = field(default_factory=dict)
    # {
    #     "intent": "enter_game",  # 액션의 의도
    #     "target_element": {
    #         "type": "button",
    #         "text": "입장",
    #         "description": "게임 입장 버튼",
    #         "visual_features": {
    #             "color": "blue",
    #             "shape": "rounded_rectangle",
    #             "icon": "door"
    #         },
    #         "relative_position": "center_bottom"
    #     },
    #     "context": {
    #         "screen_state": "lobby",
    #         "nearby_elements": ["설정 버튼", "친구 목록"],
    #         "expected_result": "loading_screen"
    #     }
    # }
    
    # 검증 정보
    screenshot_before: str = None
    screenshot_after: str = None
    ui_state_hash_before: str = None
    ui_state_hash_after: str = None
```

### SemanticActionRecorder 컴포넌트

```python
class SemanticActionRecorder:
    """의미론적 액션 기록기"""
    
    def __init__(self, config: ConfigManager, ui_analyzer: UIAnalyzer):
        self.config = config
        self.ui_analyzer = ui_analyzer
        self.actions: List[SemanticAction] = []
        self.last_action_time = None
    
    def on_click(self, x: int, y: int, button):
        """클릭 이벤트 처리 (의미론적 정보 포함)"""
        
        # 1. 클릭 전 화면 캡처
        screenshot_before = pyautogui.screenshot()
        screenshot_before_path = self._save_screenshot(screenshot_before, "before")
        
        # 2. 클릭 영역 분석 (Vision LLM)
        region = self._extract_region(screenshot_before, x, y, radius=100)
        element_info = self._analyze_element(region, x, y)
        
        # 3. 전체 화면 컨텍스트 분석
        screen_context = self._analyze_screen_context(screenshot_before)
        
        # 4. 클릭 실행 (실제 사용자 클릭이므로 이미 실행됨)
        time.sleep(0.5)  # UI 반응 대기
        
        # 5. 클릭 후 화면 캡처
        screenshot_after = pyautogui.screenshot()
        screenshot_after_path = self._save_screenshot(screenshot_after, "after")
        
        # 6. 화면 전환 분석
        transition_info = self._analyze_transition(
            screenshot_before, 
            screenshot_after
        )
        
        # 7. 의미론적 액션 생성
        action = SemanticAction(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=x,
            y=y,
            button=button.name,
            semantic_info={
                "intent": self._infer_intent(element_info, transition_info),
                "target_element": element_info,
                "context": {
                    "screen_state": screen_context["state"],
                    "nearby_elements": screen_context["nearby_elements"],
                    "expected_result": transition_info["result_state"]
                }
            },
            screenshot_before=screenshot_before_path,
            screenshot_after=screenshot_after_path,
            ui_state_hash_before=self._compute_hash(screenshot_before),
            ui_state_hash_after=self._compute_hash(screenshot_after)
        )
        
        self.actions.append(action)
        logger.info(f"의미론적 액션 기록: {action.semantic_info['intent']}")
```

---

    def _analyze_element(self, region_image, x, y) -> dict:
        """UI 요소 분석 (Vision LLM)"""
        
        prompt = f"""
        좌표 ({x}, {y}) 주변의 UI 요소를 분석해주세요.
        
        다음 정보를 JSON으로 반환:
        {{
            "type": "요소 타입 (button, icon, text_field, image 등)",
            "text": "텍스트 내용 (있는 경우)",
            "description": "이 요소의 기능/의미 (예: 게임 입장 버튼)",
            "visual_features": {{
                "color": "주요 색상",
                "shape": "모양 (circle, rectangle, rounded_rectangle 등)",
                "icon": "아이콘 설명 (있는 경우)"
            }},
            "relative_position": "화면 내 상대적 위치 (center, top_left, bottom_right 등)"
        }}
        """
        
        result = self.ui_analyzer.analyze_with_vision_llm(
            region_image, 
            prompt
        )
        return json.loads(result)
    
    def _analyze_screen_context(self, screenshot) -> dict:
        """전체 화면 컨텍스트 분석"""
        
        prompt = """
        이 게임 화면의 상태를 분석해주세요.
        
        다음 정보를 JSON으로 반환:
        {
            "state": "화면 상태 (lobby, game, settings, loading 등)",
            "nearby_elements": ["주요 UI 요소 목록"],
            "scene_description": "화면 전체 설명"
        }
        """
        
        result = self.ui_analyzer.analyze_with_vision_llm(
            screenshot,
            prompt
        )
        return json.loads(result)
    
    def _analyze_transition(self, before, after) -> dict:
        """화면 전환 분석"""
        
        # 이미지 해시 비교로 변화 감지
        hash_before = imagehash.average_hash(before)
        hash_after = imagehash.average_hash(after)
        difference = hash_before - hash_after
        
        if difference < 5:
            # 변화 없음
            return {
                "changed": False,
                "result_state": "same"
            }
        
        # Vision LLM으로 변화 분석
        prompt = """
        두 화면을 비교하여 어떤 전환이 일어났는지 분석해주세요.
        
        JSON 형식으로 반환:
        {
            "changed": true,
            "transition_type": "전환 타입 (scene_change, popup_open, loading_start 등)",
            "result_state": "전환 후 상태",
            "success": "의도한 전환인지 여부 (true/false)"
        }
        """
        
        # 두 이미지를 함께 전송
        result = self.ui_analyzer.analyze_transition_with_vision_llm(
            before,
            after,
            prompt
        )
        return json.loads(result)
    
    def _infer_intent(self, element_info, transition_info) -> str:
        """액션의 의도 추론"""
        
        # 요소 타입과 전환 정보를 조합하여 의도 추론
        element_desc = element_info.get("description", "")
        transition_type = transition_info.get("transition_type", "")
        
        # 간단한 규칙 기반 추론 (추후 ML 모델로 대체 가능)
        if "입장" in element_desc or "enter" in element_desc.lower():
            return "enter_game"
        elif "설정" in element_desc or "settings" in element_desc.lower():
            return "open_settings"
        elif "확인" in element_desc or "ok" in element_desc.lower():
            return "confirm_action"
        else:
            return f"click_{element_info.get('type', 'unknown')}"
```

---

## Semantic Action Replay (의미론적 액션 재실행)

### SemanticActionReplayer 컴포넌트

```python
class SemanticActionReplayer:
    """의미론적 액션 재실행기"""
    
    def __init__(self, ui_analyzer: UIAnalyzer, accuracy_tracker):
        self.ui_analyzer = ui_analyzer
        self.accuracy_tracker = accuracy_tracker
    
    def replay_action(self, action: SemanticAction) -> bool:
        """의미론적 액션 재실행"""
        
        logger.info(f"재실행: {action.semantic_info['intent']}")
        
        # 1. 현재 화면 캡처
        current_screen = pyautogui.screenshot()
        
        # 2. 먼저 원래 좌표로 시도
        if self._try_original_coordinates(action, current_screen):
            self.accuracy_tracker.record_success(action, method="direct")
            return True
        
        # 3. 원래 좌표 실패 시 의미론적 매칭
        logger.info("원래 좌표 실패, 의미론적 매칭 시도...")
        matched_element = self._semantic_matching(action, current_screen)
        
        if matched_element:
            # 찾은 좌표로 액션 실행
            new_x, new_y = matched_element["x"], matched_element["y"]
            self._execute_action(action.action_type, new_x, new_y, action)
            
            # 결과 검증
            time.sleep(0.5)
            after_screen = pyautogui.screenshot()
            
            if self._verify_transition(action, current_screen, after_screen):
                self.accuracy_tracker.record_success(
                    action,
                    method="semantic",
                    coordinate_change=(new_x - action.x, new_y - action.y)
                )
                return True
            else:
                self.accuracy_tracker.record_failure(
                    action,
                    reason="unexpected_transition"
                )
                return False
        else:
            # 요소를 찾지 못함
            self.accuracy_tracker.record_failure(
                action,
                reason="element_not_found"
            )
            return False
```
