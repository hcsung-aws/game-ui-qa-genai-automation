# Design Document (설계 문서)

## Overview (개요)

게임 QA 자동화 프레임워크는 Vision LLM 기반의 UI 분석과 PyAutoGUI를 활용한 액션 자동화를 결합하여, 게임 테스트를 효율적으로 수행하고 재실행 가능한 테스트 케이스를 생성하는 시스템이다.

### 핵심 기능
- AWS Bedrock Claude Sonnet 4.5를 통한 게임 화면 분석
- **pynput 기반 사용자 입력 모니터링 및 기록** (실시간 마우스/키보드 캡처)
- PyAutoGUI 기반 액션 재실행
- 대화형 CLI를 통한 기록 제어 (시작/중지/저장)
- 재실행 가능한 Python 스크립트 자동 생성
- 이미지 해시 기반 UI 상태 검증
- 여러 테스트 케이스 관리

### 기술 스택
- **언어**: Python 3.8+
- **Vision AI**: AWS Bedrock Claude Sonnet 4.5 (`anthropic.claude-sonnet-4-5-20250929-v1:0`)
- **입력 모니터링**: pynput (사용자 입력 캡처)
- **UI 자동화**: PyAutoGUI (액션 재실행)
- **OCR (폴백)**: PaddleOCR
- **이미지 처리**: Pillow, imagehash
- **AWS SDK**: boto3
- **Region**: ap-northeast-2 (서울)

---

## Architecture (아키텍처)

### 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     QA Automation System                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   CLI        │─────▶│  Controller  │─────▶│  Config   │ │
│  │  Interface   │      │              │      │  Manager  │ │
│  └──────────────┘      └──────┬───────┘      └───────────┘ │
│                               │                              │
│                               ▼                              │
│         ┌─────────────────────────────────────┐             │
│         │      Game Process Manager           │             │
│         └─────────────────────────────────────┘             │
│                               │                              │
│         ┌─────────────────────┴─────────────────┐           │
│         ▼                                       ▼           │
│  ┌──────────────┐                      ┌──────────────┐    │
│  │ UI Analyzer  │                      │   Action     │    │
│  │              │                      │   Recorder   │    │
│  │ - Screenshot │                      │              │    │
│  │ - Vision LLM │                      │ - Click      │    │
│  │ - OCR Fallback│                     │ - Type       │    │
│  └──────────────┘                      │ - Wait       │    │
│                                         └──────────────┘    │
│                                                 │            │
│                                                 ▼            │
│                                    ┌──────────────────┐     │
│                                    │  Script          │     │
│                                    │  Generator       │     │
│                                    └──────────────────┘     │
│                                                 │            │
│                                                 ▼            │
│                                    ┌──────────────────┐     │
│                                    │  Test Case       │     │
│                                    │  Manager         │     │
│                                    └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 데이터 흐름

```
사용자 "record" 명령 → CLI Interface → Controller
                                           ↓
                                 Game Process 실행
                                           ↓
                                 Input Monitor 시작 (pynput)
                                           ↓
                    ┌──────────────────────┴──────────────────────┐
                    ↓                                              ↓
          사용자가 실제로 게임 플레이                    백그라운드 모니터링
          (마우스 클릭, 키보드 입력)                     (모든 입력 자동 캡처)
                    ↓                                              ↓
                    └──────────────────────┬──────────────────────┘
                                           ↓
                                 Action Recorder에 실시간 기록
                                 (클릭 좌표, 키 입력, 타임스탬프)
                                           ↓
                    사용자 "stop" 명령 → 기록 중지
                                           ↓
                    사용자 "save" 명령 → Script 생성
                                           ↓
                                 Test Case로 저장
                                           ↓
                    재실행 시 PyAutoGUI로 액션 재현
```

---

## Components and Interfaces (컴포넌트 및 인터페이스)

### 1. ConfigManager

설정 파일을 로드하고 관리하는 컴포넌트.

```python
class ConfigManager:
    """설정 파일 관리"""
    
    def __init__(self, config_path: str = 'config.json'):
        """
        Args:
            config_path: 설정 파일 경로
        """
        self.config_path = config_path
        self.config = {}
    
    def load_config(self) -> dict:
        """설정 파일 로드
        
        Returns:
            설정 딕셔너리
            
        Raises:
            FileNotFoundError: 설정 파일이 없을 때
            json.JSONDecodeError: JSON 형식이 잘못되었을 때
        """
        pass
    
    def create_default_config(self) -> dict:
        """기본 설정 생성
        
        Returns:
            기본 설정 딕셔너리
        """
        pass
    
    def get(self, key_path: str, default=None):
        """중첩된 키 경로로 설정값 가져오기
        
        Args:
            key_path: 점으로 구분된 키 경로 (예: 'aws.region')
            default: 키가 없을 때 반환할 기본값
            
        Returns:
            설정값 또는 기본값
        """
        pass
```

### 2. GameProcessManager

게임 프로세스를 실행하고 관리하는 컴포넌트.

```python
class GameProcessManager:
    """게임 프로세스 관리"""
    
    def __init__(self, config: ConfigManager):
        """
        Args:
            config: 설정 관리자
        """
        self.config = config
        self.process = None
    
    def start_game(self) -> bool:
        """게임 실행
        
        Returns:
            성공 여부
            
        Raises:
            FileNotFoundError: 게임 실행 파일이 없을 때
            subprocess.SubprocessError: 프로세스 실행 실패 시
        """
        pass
    
    def is_game_running(self) -> bool:
        """게임 실행 중인지 확인
        
        Returns:
            실행 중이면 True
        """
        pass
    
    def stop_game(self):
        """게임 프로세스 종료"""
        pass
```

### 3. UIAnalyzer

화면을 캡처하고 Vision LLM으로 분석하는 컴포넌트.

```python
class UIAnalyzer:
    """UI 분석기"""
    
    def __init__(self, config: ConfigManager):
        """
        Args:
            config: 설정 관리자
        """
        self.config = config
        self.bedrock_client = None
        self.ocr_engine = None
    
    def capture_screenshot(self, save_path: str = None) -> Image:
        """현재 화면 캡처
        
        Args:
            save_path: 저장할 경로 (선택사항)
            
        Returns:
            PIL Image 객체
        """
        pass
    
    def analyze_with_vision_llm(self, image: Image) -> dict:
        """Vision LLM으로 UI 분석
        
        Args:
            image: 분석할 이미지
            
        Returns:
            UI 요소 정보 딕셔너리
            {
                "buttons": [{"text": str, "x": int, "y": int, "width": int, "height": int}],
                "icons": [{"type": str, "x": int, "y": int}],
                "text_fields": [{"content": str, "x": int, "y": int}]
            }
            
        Raises:
            BedrockError: API 호출 실패 시
        """
        pass
    
    def analyze_with_ocr(self, image: Image) -> list:
        """OCR로 텍스트 추출 (폴백)
        
        Args:
            image: 분석할 이미지
            
        Returns:
            텍스트 정보 리스트
            [{"text": str, "confidence": float, "bbox": list}]
        """
        pass
    
    def analyze(self, retry_count: int = 3) -> dict:
        """UI 분석 (재시도 로직 포함)
        
        Args:
            retry_count: 최대 재시도 횟수
            
        Returns:
            UI 요소 정보 딕셔너리
        """
        pass
```

### 4. InputMonitor

pynput을 사용하여 사용자의 실제 입력을 모니터링하는 컴포넌트.

```python
from pynput import mouse, keyboard

class InputMonitor:
    """입력 모니터"""
    
    def __init__(self, action_recorder):
        """
        Args:
            action_recorder: 액션 기록기
        """
        self.action_recorder = action_recorder
        self.mouse_listener = None
        self.keyboard_listener = None
        self.is_recording = False
    
    def start_monitoring(self):
        """입력 모니터링 시작"""
        self.is_recording = True
        
        # 마우스 리스너 시작
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener.start()
        
        # 키보드 리스너 시작
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        self.keyboard_listener.start()
    
    def stop_monitoring(self):
        """입력 모니터링 중지"""
        self.is_recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
    
    def _on_mouse_click(self, x, y, button, pressed):
        """마우스 클릭 이벤트 핸들러
        
        Args:
            x: X 좌표
            y: Y 좌표
            button: 마우스 버튼
            pressed: 눌림/뗌 상태
        """
        if pressed and self.is_recording:
            action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=x,
                y=y,
                description=f'클릭 ({x}, {y})',
                button=button.name
            )
            self.action_recorder.record_action(action)
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """마우스 스크롤 이벤트 핸들러"""
        if self.is_recording:
            action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='scroll',
                x=x,
                y=y,
                description=f'스크롤 ({dx}, {dy})',
                scroll_dx=dx,
                scroll_dy=dy
            )
            self.action_recorder.record_action(action)
    
    def _on_key_press(self, key):
        """키보드 입력 이벤트 핸들러
        
        Args:
            key: 눌린 키
        """
        if self.is_recording:
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key)
            
            action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='key_press',
                x=0,
                y=0,
                description=f'키 입력: {key_char}',
                key=key_char
            )
            self.action_recorder.record_action(action)


class Action:
    """액션 데이터 클래스"""
    timestamp: str
    action_type: str  # 'click', 'key_press', 'scroll', 'wait'
    x: int
    y: int
    description: str
    screenshot_path: str = None
    button: str = None  # 'left', 'right', 'middle'
    key: str = None
    scroll_dx: int = None
    scroll_dy: int = None


class ActionRecorder:
    """액션 기록기"""
    
    def __init__(self, config: ConfigManager):
        """
        Args:
            config: 설정 관리자
        """
        self.config = config
        self.actions: List[Action] = []
        self.last_action_time = None
    
    def record_action(self, action: Action):
        """액션 기록
        
        Args:
            action: 기록할 액션
        """
        # 스크린샷 캡처 (설정에 따라)
        if self.config.get('automation.screenshot_on_action', False):
            screenshot_path = f"screenshots/action_{len(self.actions):04d}.png"
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            action.screenshot_path = screenshot_path
        
        # 이전 액션과의 시간 차이 계산
        current_time = datetime.now()
        if self.last_action_time:
            time_diff = (current_time - self.last_action_time).total_seconds()
            if time_diff > 0.5:  # 0.5초 이상 차이나면 wait 액션 추가
                wait_action = Action(
                    timestamp=self.last_action_time.isoformat(),
                    action_type='wait',
                    x=0,
                    y=0,
                    description=f'{time_diff:.1f}초 대기'
                )
                self.actions.append(wait_action)
        
        self.actions.append(action)
        self.last_action_time = current_time
    
    def get_actions(self) -> List[Action]:
        """기록된 액션 목록 반환
        
        Returns:
            액션 리스트
        """
        return self.actions
    
    def clear_actions(self):
        """기록된 액션 초기화"""
        self.actions = []
        self.last_action_time = None
```

### 5. ScriptGenerator

기록된 액션을 Python 스크립트로 변환하는 컴포넌트.

```python
class ScriptGenerator:
    """스크립트 생성기"""
    
    def __init__(self, config: ConfigManager):
        """
        Args:
            config: 설정 관리자
        """
        self.config = config
    
    def generate_replay_script(self, actions: List[Action], output_path: str) -> str:
        """재실행 스크립트 생성
        
        Args:
            actions: 액션 리스트
            output_path: 출력 파일 경로
            
        Returns:
            생성된 스크립트 경로
        """
        pass
    
    def _generate_script_header(self) -> str:
        """스크립트 헤더 생성
        
        Returns:
            헤더 문자열
        """
        pass
    
    def _generate_action_code(self, action: Action) -> str:
        """액션을 Python 코드로 변환
        
        Args:
            action: 변환할 액션
            
        Returns:
            Python 코드 문자열
        """
        pass
```

### 6. TestCaseManager

여러 테스트 케이스를 관리하는 컴포넌트.

```python
class TestCase:
    """테스트 케이스 데이터 클래스"""
    name: str
    created_at: str
    actions: List[Action]
    script_path: str
    json_path: str


class TestCaseManager:
    """테스트 케이스 관리자"""
    
    def __init__(self, test_cases_dir: str = 'test_cases'):
        """
        Args:
            test_cases_dir: 테스트 케이스 저장 디렉토리
        """
        self.test_cases_dir = test_cases_dir
    
    def save_test_case(self, name: str, actions: List[Action]) -> TestCase:
        """테스트 케이스 저장
        
        Args:
            name: 테스트 케이스 이름
            actions: 액션 리스트
            
        Returns:
            저장된 테스트 케이스
        """
        pass
    
    def load_test_case(self, name: str) -> TestCase:
        """테스트 케이스 로드
        
        Args:
            name: 테스트 케이스 이름
            
        Returns:
            로드된 테스트 케이스
            
        Raises:
            FileNotFoundError: 테스트 케이스가 없을 때
        """
        pass
    
    def list_test_cases(self) -> List[TestCase]:
        """모든 테스트 케이스 목록
        
        Returns:
            테스트 케이스 리스트
        """
        pass
    
    def delete_test_case(self, name: str) -> bool:
        """테스트 케이스 삭제
        
        Args:
            name: 테스트 케이스 이름
            
        Returns:
            성공 여부
        """
        pass
```

### 7. CLIInterface

사용자와 상호작용하는 CLI 인터페이스.

```python
class CLIInterface:
    """CLI 인터페이스"""
    
    def __init__(self, controller):
        """
        Args:
            controller: QA 자동화 컨트롤러
        """
        self.controller = controller
    
    def start_interactive_session(self):
        """대화형 세션 시작"""
        print("=== 게임 QA 자동화 시작 ===")
        print("명령어: start, record, stop, analyze, save, list, load, replay")
        print("       pause, mark_error, stats, report, retrain, quit")
        
        while True:
            cmd = input("\n> ").strip().split()
            if not cmd:
                continue
            
            if not self.handle_command(cmd):
                break
    
    def display_help(self):
        """도움말 표시"""
        print("""
사용 가능한 명령어:
  start              - 게임 실행
  record             - 입력 기록 시작 (사용자가 직접 게임 플레이)
  stop               - 입력 기록 중지
  analyze            - 현재 화면 UI 분석
  save <name>        - 기록된 액션을 테스트 케이스로 저장
  list               - 저장된 테스트 케이스 목록
  load <name>        - 테스트 케이스 로드
  replay [--verify]  - 로드된 테스트 케이스 재실행
  pause              - 재실행 일시정지
  mark_error         - 현재 액션을 오동작으로 표시
  stats              - 정확도 통계 표시
  report             - HTML 리포트 생성
  retrain            - 재학습 후보 액션 표시 및 재학습
  quit               - 종료
        """)
    
    def handle_command(self, command: list) -> bool:
        """명령어 처리
        
        Args:
            command: 사용자 입력 명령어 (리스트)
            
        Returns:
            계속 실행 여부 (False면 종료)
        """
        cmd = command[0].lower()
        
        if cmd == "start":
            self.controller.start_game()
        elif cmd == "record":
            self.controller.start_recording()
            print("✓ 입력 기록 시작. 게임을 플레이하세요. 'stop' 명령으로 중지.")
        elif cmd == "stop":
            self.controller.stop_recording()
            print(f"✓ 입력 기록 중지. {len(self.controller.get_actions())}개 액션 기록됨.")
        elif cmd == "analyze":
            ui_data = self.controller.analyze_ui()
            self.display_ui_analysis(ui_data)
        elif cmd == "save":
            if len(command) < 2:
                print("❌ 사용법: save <테스트_케이스_이름>")
            else:
                name = command[1]
                self.controller.save_test_case(name)
                print(f"✓ 테스트 케이스 '{name}' 저장 완료")
        elif cmd == "list":
            test_cases = self.controller.list_test_cases()
            print("\n저장된 테스트 케이스:")
            for tc in test_cases:
                print(f"  - {tc.name} ({tc.created_at})")
        elif cmd == "load":
            if len(command) < 2:
                print("❌ 사용법: load <테스트_케이스_이름>")
            else:
                name = command[1]
                self.controller.load_test_case(name)
                print(f"✓ 테스트 케이스 '{name}' 로드 완료")
        elif cmd == "replay":
            verify = "--verify" in command
            self.controller.replay_test_case(verify=verify)
            print("✓ 재실행 완료")
        elif cmd == "quit":
            return False
        else:
            print(f"❌ 알 수 없는 명령어: {cmd}")
            self.display_help()
        
        return True
    
    def display_ui_analysis(self, ui_data: dict):
        """UI 분석 결과 표시
        
        Args:
            ui_data: UI 요소 정보
        """
        print("\n=== UI 분석 결과 ===")
        print(json.dumps(ui_data, indent=2, ensure_ascii=False))
```

### 8. SemanticActionRecorder

의미론적 맥락 정보를 포함하여 액션을 기록하는 컴포넌트.

```python
@dataclass
class SemanticAction(Action):
    """의미론적 액션 (Action 확장)"""
    
    # 의미론적 정보
    semantic_info: dict = field(default_factory=dict)
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
    
    ui_state_hash_before: str = None
    ui_state_hash_after: str = None


class SemanticActionRecorder(ActionRecorder):
    """의미론적 액션 기록기"""
    
    def __init__(self, config: ConfigManager, ui_analyzer: UIAnalyzer):
        super().__init__(config)
        self.ui_analyzer = ui_analyzer
    
    def record_action_with_context(self, action: Action) -> SemanticAction:
        """맥락 정보를 포함하여 액션 기록
        
        Args:
            action: 기본 액션
            
        Returns:
            의미론적 정보가 추가된 액션
        """
        # 전후 스크린샷 분석
        # Vision LLM으로 UI 요소 분석
        # 화면 전환 분석
        # 의도 추론
        pass
```

### 9. SemanticActionReplayer

의미론적 매칭을 통해 액션을 재실행하는 컴포넌트.

```python
class SemanticActionReplayer:
    """의미론적 액션 재실행기"""
    
    def __init__(self, ui_analyzer: UIAnalyzer, accuracy_tracker):
        self.ui_analyzer = ui_analyzer
        self.accuracy_tracker = accuracy_tracker
    
    def replay_action(self, action: SemanticAction) -> bool:
        """의미론적 액션 재실행
        
        Args:
            action: 재실행할 의미론적 액션
            
        Returns:
            성공 여부
        """
        # 1. 원래 좌표로 시도
        # 2. 실패 시 의미론적 매칭
        # 3. 화면 전환 검증
        # 4. 결과 기록
        pass
    
    def semantic_matching(self, action: SemanticAction, 
                         current_screen) -> dict:
        """의미론적 매칭으로 요소 찾기
        
        Args:
            action: 찾을 액션
            current_screen: 현재 화면
            
        Returns:
            찾은 요소 정보 (좌표 포함)
        """
        pass
```

### 10. AccuracyTracker

테스트 실행의 정확도를 추적하는 컴포넌트.

```python
@dataclass
class ActionExecutionResult:
    """액션 실행 결과"""
    action_id: str
    timestamp: str
    success: bool
    method: str  # 'direct', 'semantic', 'manual'
    coordinate_change: tuple = None
    execution_time: float = 0.0
    failure_reason: str = None


class AccuracyTracker:
    """정확도 추적기"""
    
    def __init__(self, test_case_name: str):
        self.test_case_name = test_case_name
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results: List[ActionExecutionResult] = []
    
    def record_success(self, action: SemanticAction, method: str,
                      coordinate_change: tuple = None):
        """성공 기록"""
        pass
    
    def record_failure(self, action: SemanticAction, reason: str):
        """실패 기록"""
        pass
    
    def calculate_statistics(self) -> dict:
        """통계 계산
        
        Returns:
            {
                "success_rate": float,
                "direct_match_rate": float,
                "semantic_match_rate": float,
                "avg_coordinate_change": float,
                "failure_reasons": dict
            }
        """
        pass
```

### 11. AccuracyReporter

정확도 통계를 시각화하는 컴포넌트.

```python
class AccuracyReporter:
    """정확도 리포터"""
    
    def __init__(self, test_case_name: str):
        self.test_case_name = test_case_name
    
    def show_statistics(self):
        """CLI에서 통계 표시"""
        pass
    
    def generate_html_report(self, output_path: str = None):
        """HTML 리포트 생성
        
        Args:
            output_path: 출력 파일 경로
        """
        pass
```

### 12. ActionRetrainer

실패율이 높은 액션을 재학습하는 컴포넌트.

```python
class ActionRetrainer:
    """액션 재학습기"""
    
    def __init__(self, test_case_manager: TestCaseManager,
                 ui_analyzer: UIAnalyzer):
        self.test_case_manager = test_case_manager
        self.ui_analyzer = ui_analyzer
    
    def find_retraining_candidates(self, test_case_name: str) -> list:
        """재학습 후보 찾기 (실패율 30% 이상)
        
        Args:
            test_case_name: 테스트 케이스 이름
            
        Returns:
            재학습 후보 액션 리스트
        """
        pass
    
    def retrain_action(self, action: SemanticAction) -> SemanticAction:
        """액션 재학습
        
        Args:
            action: 재학습할 액션
            
        Returns:
            개선된 액션
        """
        pass
```

### 13. QAAutomationController

전체 시스템을 조율하는 메인 컨트롤러.

```python
class QAAutomationController:
    """QA 자동화 컨트롤러"""
    
    def __init__(self, config_path: str = 'config.json'):
        """
        Args:
            config_path: 설정 파일 경로
        """
        self.config_manager = ConfigManager(config_path)
        self.game_manager = GameProcessManager(self.config_manager)
        self.ui_analyzer = UIAnalyzer(self.config_manager)
        self.action_recorder = ActionRecorder(self.config_manager)
        self.input_monitor = InputMonitor(self.action_recorder)
        self.script_generator = ScriptGenerator(self.config_manager)
        self.test_case_manager = TestCaseManager()
        self.current_test_case = None
    
    def initialize(self) -> bool:
        """시스템 초기화
        
        Returns:
            성공 여부
        """
        # 설정 로드
        self.config_manager.load_config()
        
        # 필요한 디렉토리 생성
        os.makedirs('screenshots', exist_ok=True)
        os.makedirs('test_cases', exist_ok=True)
        
        return True
    
    def start_game(self) -> bool:
        """게임 시작
        
        Returns:
            성공 여부
        """
        return self.game_manager.start_game()
    
    def start_recording(self):
        """입력 기록 시작"""
        self.action_recorder.clear_actions()
        self.input_monitor.start_monitoring()
    
    def stop_recording(self):
        """입력 기록 중지"""
        self.input_monitor.stop_monitoring()
    
    def get_actions(self) -> List[Action]:
        """기록된 액션 목록 반환
        
        Returns:
            액션 리스트
        """
        return self.action_recorder.get_actions()
    
    def analyze_ui(self) -> dict:
        """UI 분석
        
        Returns:
            UI 요소 정보
        """
        return self.ui_analyzer.analyze()
    
    def save_test_case(self, name: str) -> TestCase:
        """테스트 케이스 저장
        
        Args:
            name: 테스트 케이스 이름
            
        Returns:
            저장된 테스트 케이스
        """
        actions = self.action_recorder.get_actions()
        test_case = self.test_case_manager.save_test_case(name, actions)
        
        # Replay Script 생성
        script_path = f"test_cases/{name}.py"
        self.script_generator.generate_replay_script(actions, script_path)
        
        return test_case
    
    def load_test_case(self, name: str) -> TestCase:
        """테스트 케이스 로드
        
        Args:
            name: 테스트 케이스 이름
            
        Returns:
            로드된 테스트 케이스
        """
        self.current_test_case = self.test_case_manager.load_test_case(name)
        return self.current_test_case
    
    def list_test_cases(self) -> List[TestCase]:
        """테스트 케이스 목록
        
        Returns:
            테스트 케이스 리스트
        """
        return self.test_case_manager.list_test_cases()
    
    def replay_test_case(self, verify: bool = False):
        """테스트 케이스 재실행
        
        Args:
            verify: 검증 모드 활성화 여부
        """
        if not self.current_test_case:
            raise ValueError("로드된 테스트 케이스가 없습니다")
        
        # Replay Script 실행
        script_path = self.current_test_case.script_path
        if verify:
            subprocess.run(['python', script_path, '--verify'])
        else:
            subprocess.run(['python', script_path])
```

---

## Data Models (데이터 모델)

### Configuration Schema

```json
{
  "aws": {
    "region": "ap-northeast-2",
    "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
    "max_tokens": 2000,
    "retry_count": 3,
    "retry_delay": 1.0
  },
  "game": {
    "exe_path": "C:/path/to/game.exe",
    "window_title": "Game Window",
    "startup_wait": 5
  },
  "automation": {
    "action_delay": 0.5,
    "screenshot_on_action": true,
    "screenshot_dir": "screenshots",
    "verify_mode": false,
    "hash_threshold": 5
  },
  "test_cases": {
    "directory": "test_cases"
  }
}
```

### Action JSON Schema

```json
{
  "timestamp": "2025-12-13T10:30:45.123456",
  "action_type": "click",
  "x": 640,
  "y": 400,
  "description": "클릭 (640, 400)",
  "screenshot_path": "screenshots/action_001.png"
}
```

### UI Analysis Response Schema

```json
{
  "buttons": [
    {
      "text": "Start Game",
      "x": 640,
      "y": 400,
      "width": 200,
      "height": 60,
      "confidence": 0.95
    }
  ],
  "icons": [
    {
      "type": "settings",
      "x": 1200,
      "y": 50,
      "confidence": 0.88
    }
  ],
  "text_fields": [
    {
      "content": "Player Name",
      "x": 500,
      "y": 300,
      "confidence": 0.92
    }
  ]
}
```

### Test Case JSON Schema

```json
{
  "name": "login_test",
  "created_at": "2025-12-13T10:30:00",
  "actions": [
    {
      "timestamp": "2025-12-13T10:30:45",
      "action_type": "click",
      "x": 640,
      "y": 400,
      "description": "클릭 (640, 400)"
    }
  ],
  "script_path": "test_cases/login_test.py",
  "json_path": "test_cases/login_test.json"
}
```

---

## Correctness Properties (정확성 속성)

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: 설정 파일 round trip

*For any* 유효한 설정 딕셔너리, 설정을 JSON 파일로 저장한 후 다시 로드하면 원래 설정과 동일한 값을 가져야 한다.

**Validates: Requirements 1.5**

### Property 2: 이미지 인코딩 round trip

*For any* 유효한 이미지, base64로 인코딩한 후 디코딩하면 원래 이미지와 동일해야 한다.

**Validates: Requirements 2.2**

### Property 3: UI 분석 결과 구조 완전성

*For any* UI 분석 결과, 반환된 JSON은 buttons, icons, text_fields 키를 포함해야 하며, 각 요소는 필수 좌표 정보(x, y)를 포함해야 한다.

**Validates: Requirements 2.7**

### Property 4: Vision LLM 재시도 지수 백오프

*For any* Vision LLM 요청 실패 시나리오, 재시도 간격은 지수적으로 증가해야 하며(1초, 2초, 4초), 최대 3회까지만 재시도해야 한다.

**Validates: Requirements 2.5**

### Property 5: 액션 기록 완전성

*For any* 실행된 액션, 기록된 액션은 timestamp, action_type, x, y, description 필드를 모두 포함해야 한다.

**Validates: Requirements 3.4**

### Property 6: 조건부 스크린샷 캡처

*For any* 액션 실행 또는 검증 모드 재실행 시, screenshot-on-action 또는 verify_mode 설정이 활성화되어 있으면 스크린샷 파일이 생성되어야 하고, 비활성화되어 있으면 생성되지 않아야 한다.

**Validates: Requirements 3.5, 7.1**

### Property 7: 대기 시간 정확성

*For any* 양의 정수 대기 시간, 대기 명령 실행 시 실제 경과 시간은 지정된 시간의 ±0.1초 이내여야 한다.

**Validates: Requirements 3.3**

### Property 8: 유효하지 않은 명령 처리

*For any* 유효하지 않은 명령 문자열, 시스템은 오류 메시지와 함께 사용 가능한 명령어 목록을 표시해야 한다.

**Validates: Requirements 4.8**

### Property 9: 스크립트 생성 완전성

*For any* 액션 리스트, 생성된 Replay Script는 모든 액션을 포함해야 하며, 각 액션은 timestamp, action_type, x, y, description을 포함해야 한다.

**Validates: Requirements 5.1, 5.2**

### Property 10: 스크립트 구조 유효성

*For any* 생성된 Replay Script, 스크립트는 유효한 Python 문법을 따라야 하며, replay_actions 함수를 포함해야 한다.

**Validates: Requirements 5.3**

### Property 11: UTF-8 인코딩 보장

*For any* 생성된 Replay Script, 파일은 UTF-8 인코딩으로 저장되어야 하며, 한글 등 유니코드 문자가 손실 없이 저장되어야 한다.

**Validates: Requirements 5.4**

### Property 12: 대기 액션 파싱 정확성

*For any* "N초 대기" 형식의 설명을 가진 대기 액션, 생성된 스크립트는 time.sleep(N)을 포함해야 한다.

**Validates: Requirements 5.5**

### Property 13: 액션 실행 순서 보존

*For any* 액션 리스트, 재실행 시 액션은 원래 기록된 순서대로 실행되어야 한다.

**Validates: Requirements 6.1**

### Property 14: 액션 간 지연 시간 준수

*For any* 설정된 action_delay 값, 재실행 시 각 액션 사이의 실제 경과 시간은 action_delay의 ±0.1초 이내여야 한다.

**Validates: Requirements 6.5**

### Property 15: 이미지 해시 계산 일관성

*For any* 동일한 이미지, 해시를 여러 번 계산해도 동일한 값을 반환해야 한다.

**Validates: Requirements 7.2**

### Property 16: 해시 비교 정확성

*For any* 두 이미지, 이미지가 동일하면 해시 차이는 0이어야 하고, 이미지가 다르면 해시 차이는 0보다 커야 한다.

**Validates: Requirements 7.3**

### Property 17: 검증 실패 임계값 적용

*For any* 해시 차이와 임계값, 차이가 임계값을 초과하면 검증 실패로 로그되어야 하고, 초과하지 않으면 성공으로 처리되어야 한다.

**Validates: Requirements 7.4**

### Property 18: 검증 실패 후 계속 실행

*For any* 여러 액션을 포함한 재실행 스크립트, 중간에 검증 실패가 발생해도 나머지 액션은 계속 실행되어야 하며, 모든 실패는 마지막에 보고되어야 한다.

**Validates: Requirements 7.5**

### Property 19: 테스트 케이스 파일명 일관성

*For any* 유효한 테스트 케이스 이름, 저장된 Replay Script 파일명은 "{name}.py" 형식이어야 하고, JSON 파일명은 "{name}.json" 형식이어야 한다.

**Validates: Requirements 8.2**

### Property 20: 테스트 케이스 serialization round trip

*For any* 액션 리스트, 테스트 케이스로 저장한 후 다시 로드하면 원래 액션 리스트와 동일해야 한다.

**Validates: Requirements 8.3, 8.5**

### Property 21: 테스트 케이스 목록 완전성

*For any* 저장된 테스트 케이스 집합, 목록 조회 시 모든 테스트 케이스가 이름과 생성 타임스탬프와 함께 표시되어야 한다.

**Validates: Requirements 8.4**

### Property 22: 잘못된 설정 파일 처리

*For any* 잘못된 형식의 JSON 설정 파일, 시스템은 검증 오류를 표시하고 기본 설정값을 사용하여 계속 실행되어야 한다.

**Validates: Requirements 9.4**

### Property 23: 스크립트 오류 복구

*For any* 오류를 발생시키는 액션을 포함한 재실행 스크립트, 오류가 발생해도 나머지 액션은 계속 실행되어야 하며, 오류는 로그에 기록되어야 한다.

**Validates: Requirements 9.5**

### Property 24: AWS region 설정 적용

*For any* 유효한 AWS region 문자열, 설정에 지정된 region은 Bedrock 클라이언트 초기화 시 사용되어야 한다.

**Validates: Requirements 10.2**

### Property 25: 게임 경로 설정 적용

*For any* 유효한 파일 경로, 설정에 지정된 게임 실행 파일 경로는 게임 프로세스 시작 시 사용되어야 한다.

**Validates: Requirements 10.3**

### Property 26: 시작 대기 시간 준수

*For any* 양의 정수 시작 대기 시간, 게임 실행 후 실제 대기 시간은 설정된 시간의 ±0.1초 이내여야 한다.

**Validates: Requirements 10.4**

### Property 27: 조건부 스크린샷 설정 적용

*For any* screenshot-on-action 설정값(true/false), 액션 실행 후 스크린샷 캡처 여부는 설정값과 일치해야 한다.

**Validates: Requirements 10.6**

### Property 28: 의미론적 액션 완전성

*For any* 기록된 의미론적 액션, 액션은 물리적 정보(좌표)와 의미론적 정보(의도, 타겟 요소, 맥락)를 모두 포함해야 한다.

**Validates: Requirements 11.6**

### Property 29: 화면 전환 기록

*For any* 클릭 액션, 액션 전후의 스크린샷과 화면 전환 정보(이전 상태, 이후 상태)가 기록되어야 한다.

**Validates: Requirements 11.1, 11.4**

### Property 30: 의미론적 매칭 폴백

*For any* 의미론적 액션 재실행, 원래 좌표에서 실패하면 의미론적 매칭을 시도해야 하고, 매칭 성공 시 새로운 좌표로 액션을 실행해야 한다.

**Validates: Requirements 12.1, 12.2, 12.4**

### Property 31: 화면 전환 검증

*For any* 의미론적 액션 재실행, 액션 실행 후 예상한 화면 전환이 발생했는지 검증해야 하며, 예상과 다르면 경고를 로그해야 한다.

**Validates: Requirements 12.6, 12.7**

### Property 32: 정확도 통계 완전성

*For any* 테스트 재실행 세션, 계산된 통계는 성공률, 직접 매칭률, 의미론적 매칭률, 평균 좌표 변경 거리, 실패 원인 분포를 포함해야 한다.

**Validates: Requirements 13.6**

### Property 33: 액션 실행 결과 기록

*For any* 재실행된 액션, 실행 결과(성공/실패, 방법, 좌표 변경, 실패 원인)가 AccuracyTracker에 기록되어야 한다.

**Validates: Requirements 13.2, 13.3, 13.4**

### Property 34: 오류 표시 및 재분석

*For any* 사용자가 오동작으로 표시한 액션, Vision LLM을 사용하여 재분석하고 개선된 의미론적 정보를 제안해야 한다.

**Validates: Requirements 14.5, 14.6**

### Property 35: 테스트 케이스 업데이트

*For any* 개선된 액션, 사용자가 수락하면 테스트 케이스가 즉시 업데이트되어야 한다.

**Validates: Requirements 14.7**

### Property 36: 실행 이력 표시

*For any* 테스트 케이스, 모든 실행 세션의 이력(날짜, 성공률, 오류 수, 의미론적 매칭 사용률)을 표시할 수 있어야 한다.

**Validates: Requirements 15.1, 15.2**

### Property 37: HTML 리포트 생성

*For any* 테스트 케이스, HTML 리포트는 정확도 추세 그래프, 오류 타입 분포, 가장 문제가 많은 액션 목록을 포함해야 한다.

**Validates: Requirements 15.4**

### Property 38: 재학습 후보 식별

*For any* 테스트 케이스, 실패율이 30%를 초과하는 액션은 자동으로 재학습 후보로 표시되어야 한다.

**Validates: Requirements 16.1**

### Property 39: 패턴 기반 재학습

*For any* 재학습 대상 액션, 성공한 경우와 실패한 경우의 패턴을 분석하여 더 강건한 의미론적 정보를 생성해야 한다.

**Validates: Requirements 16.4, 16.5**

### Property 40: 재학습 효과 검증

*For any* 재학습된 액션, 검증 실행을 수행하고 개선 전후의 정확도를 비교하여 표시해야 한다.

**Validates: Requirements 16.7**

---

## Error Handling (오류 처리)

### 1. 게임 프로세스 오류

**시나리오**: 게임 실행 파일이 존재하지 않거나 실행 권한이 없음

**처리 방법**:
- FileNotFoundError 또는 PermissionError 캐치
- 명확한 오류 메시지 로그 출력
- 사용자에게 경로 확인 요청
- 시스템 종료 (exit code 1)

```python
try:
    process = subprocess.Popen(game_path)
except FileNotFoundError:
    logger.error(f"게임 실행 파일을 찾을 수 없습니다: {game_path}")
    sys.exit(1)
except PermissionError:
    logger.error(f"게임 실행 권한이 없습니다: {game_path}")
    sys.exit(1)
```

### 2. AWS Bedrock 연결 오류

**시나리오**: AWS Bedrock API 호출 실패 (네트워크 오류, 인증 실패, 할당량 초과 등)

**처리 방법**:
- 지수 백오프로 최대 3회 재시도 (1초, 2초, 4초)
- 모든 재시도 실패 시 OCR Engine으로 폴백
- 각 재시도 시도를 로그에 기록

```python
for attempt in range(3):
    try:
        response = bedrock_client.invoke_model(...)
        return response
    except Exception as e:
        logger.warning(f"Vision LLM 호출 실패 (시도 {attempt + 1}/3): {e}")
        if attempt < 2:
            time.sleep(2 ** attempt)
        else:
            logger.info("OCR Engine으로 폴백합니다")
            return self.analyze_with_ocr(image)
```

### 3. PyAutoGUI 실행 오류

**시나리오**: 클릭/타이핑 실행 실패 (창이 비활성화됨, 좌표가 화면 밖 등)

**처리 방법**:
- 오류를 로그에 기록
- 사용자에게 재시도 또는 건너뛰기 선택 요청
- 사용자 선택에 따라 액션 재실행 또는 다음 액션으로 진행

```python
try:
    pyautogui.click(x, y)
except pyautogui.FailSafeException:
    logger.error(f"클릭 실패: ({x}, {y})")
    choice = input("재시도(r) 또는 건너뛰기(s)? ")
    if choice.lower() == 'r':
        return self.execute_click(x, y)
    else:
        return False
```

### 4. 설정 파일 오류

**시나리오**: config.json이 없거나 잘못된 형식

**처리 방법**:
- 파일이 없으면 기본 설정 생성
- JSON 파싱 오류 시 검증 오류 표시하고 기본값 사용
- 경고 메시지 출력 후 계속 실행

```python
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    logger.warning("설정 파일이 없습니다. 기본 설정을 생성합니다.")
    config = self.create_default_config()
except json.JSONDecodeError as e:
    logger.error(f"설정 파일 형식 오류: {e}")
    logger.warning("기본 설정을 사용합니다.")
    config = self.create_default_config()
```

### 5. 재실행 스크립트 오류

**시나리오**: 스크립트 실행 중 액션 실패

**처리 방법**:
- 오류를 로그에 기록
- 실패한 액션 정보 저장
- 나머지 액션 계속 실행
- 마지막에 모든 실패 요약 출력

```python
failures = []
for action in actions:
    try:
        execute_action(action)
    except Exception as e:
        logger.error(f"액션 실행 실패: {action['description']} - {e}")
        failures.append((action, str(e)))

if failures:
    print(f"\n=== {len(failures)}개 액션 실패 ===")
    for action, error in failures:
        print(f"- {action['description']}: {error}")
```

### 6. 스크린샷 캡처 오류

**시나리오**: 화면 캡처 실패 (권한 문제, 메모리 부족 등)

**처리 방법**:
- 오류를 로그에 기록
- 스크린샷 없이 계속 진행
- 사용자에게 경고 메시지 표시

```python
try:
    screenshot = pyautogui.screenshot()
except Exception as e:
    logger.error(f"스크린샷 캡처 실패: {e}")
    logger.warning("스크린샷 없이 계속 진행합니다.")
    screenshot = None
```

---

## Testing Strategy (테스트 전략)

### 1. Property-Based Testing

본 시스템의 정확성을 검증하기 위해 **Hypothesis** 라이브러리를 사용한 property-based testing을 수행한다.

#### 선택 이유
- Python 생태계에서 가장 성숙한 property-based testing 라이브러리
- 풍부한 전략(strategies) 제공으로 복잡한 데이터 생성 가능
- 실패 시 최소 반례(minimal counterexample) 자동 축소
- 테스트 재현을 위한 시드(seed) 관리

#### 설정
- 각 property test는 최소 100회 반복 실행
- 실패 시 자동으로 최소 반례 탐색
- 모든 property test는 design 문서의 property 번호를 주석으로 명시

```python
from hypothesis import given, settings, strategies as st

@settings(max_examples=100)
@given(config=st.dictionaries(
    keys=st.text(min_size=1),
    values=st.one_of(st.text(), st.integers(), st.floats())
))
def test_config_round_trip(config):
    """
    **Feature: game-qa-automation, Property 1: 설정 파일 round trip**
    """
    # 설정 저장
    save_config(config, 'test_config.json')
    # 설정 로드
    loaded_config = load_config('test_config.json')
    # 원본과 동일한지 확인
    assert loaded_config == config
```

#### Property Test 커버리지

각 correctness property는 하나의 property-based test로 구현된다:

- **Property 1-27**: 각각 독립적인 property test 함수로 구현
- **Generators**: 액션, 설정, 이미지, 테스트 케이스 등을 위한 커스텀 전략 정의
- **Invariants**: 각 property가 검증하는 불변 조건 명시

### 2. Unit Testing

Property-based testing을 보완하기 위해 특정 시나리오와 엣지 케이스를 검증하는 unit test를 작성한다.

#### 테스트 대상

**ConfigManager**:
- 기본 설정 생성
- 중첩된 키 경로 접근
- 잘못된 JSON 처리

**UIAnalyzer**:
- Vision LLM API 호출 (mocking)
- OCR 폴백 동작
- 재시도 로직

**ActionRecorder**:
- 각 액션 타입 실행
- 액션 기록 형식
- 스크린샷 캡처 조건

**ScriptGenerator**:
- 스크립트 헤더 생성
- 액션 코드 변환
- UTF-8 인코딩

**TestCaseManager**:
- 테스트 케이스 저장/로드
- 목록 조회
- 파일명 생성

#### 예시

```python
import unittest
from unittest.mock import Mock, patch

class TestUIAnalyzer(unittest.TestCase):
    def test_analyze_with_vision_llm_success(self):
        """Vision LLM 정상 호출 테스트"""
        analyzer = UIAnalyzer(config)
        image = Image.new('RGB', (100, 100))
        
        result = analyzer.analyze_with_vision_llm(image)
        
        self.assertIn('buttons', result)
        self.assertIn('icons', result)
        self.assertIn('text_fields', result)
    
    def test_analyze_with_retry_fallback(self):
        """재시도 후 OCR 폴백 테스트"""
        analyzer = UIAnalyzer(config)
        
        # Vision LLM 실패 시뮬레이션
        with patch.object(analyzer, 'analyze_with_vision_llm', side_effect=Exception):
            result = analyzer.analyze(retry_count=3)
        
        # OCR 결과 반환 확인
        self.assertIsInstance(result, list)
```

### 3. Integration Testing

전체 워크플로우를 검증하는 통합 테스트:

- 게임 실행 → UI 분석 → 액션 실행 → 스크립트 생성 → 재실행
- 테스트 케이스 저장 → 로드 → 재실행
- 검증 모드 재실행

### 4. Test Utilities

테스트를 위한 유틸리티 함수:

```python
def create_test_config(overrides=None):
    """테스트용 설정 생성"""
    config = {
        "aws": {"region": "ap-northeast-2"},
        "game": {"exe_path": "test_game.exe"},
        "automation": {"action_delay": 0.1}
    }
    if overrides:
        config.update(overrides)
    return config

def create_test_actions(count=5):
    """테스트용 액션 리스트 생성"""
    actions = []
    for i in range(count):
        actions.append(Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100 * i,
            y=100 * i,
            description=f'테스트 액션 {i}'
        ))
    return actions
```

### 5. 테스트 실행

```bash
# Phase별 테스트
pytest tests/phase1/ -v  # Phase 1 테스트만
pytest tests/phase2/ -v  # Phase 2 테스트만

# 타입별 테스트
pytest tests/property/ -v  # Property-based tests
pytest tests/unit/ -v      # Unit tests
pytest tests/integration/ -v  # Integration tests

# 전체 테스트
pytest tests/ -v --cov=src --cov-report=html

# 특정 Phase까지의 모든 테스트
pytest tests/phase1/ tests/phase2/ tests/phase3/ -v
```

### 6. 테스트 문서

각 Phase마다 다음 문서를 작성한다:

1. **Unit Test 코드** (`tests/phaseN/test_*.py`)
2. **Integration Test 코드** (`tests/phaseN/test_phaseN_workflow.py`)
3. **Manual Test Guide** (`docs/phaseN_manual_test.md`)
4. **Test Data** (`tests/fixtures/phaseN/`)

**Manual Test Guide 템플릿**:
```markdown
# Phase N 수동 테스트 가이드

## 목적
[이 Phase에서 검증하려는 핵심 기능]

## 준비사항
- [ ] 필요한 환경 설정
- [ ] 테스트 데이터 준비

## 테스트 시나리오 1: [시나리오 이름]
1. [단계 1]
2. [단계 2]
3. [예상 결과 확인]

## 테스트 시나리오 2: [시나리오 이름]
...

## 체크리스트
- [ ] 모든 시나리오 통과
- [ ] 로그에 오류 없음
- [ ] 성능 허용 범위 내

## 문제 발생 시
[트러블슈팅 가이드]
```

---

## Implementation Notes (구현 참고사항)

### 1. 프로젝트 구조

```
game-qa-automation/
├── src/
│   ├── __init__.py
│   ├── config_manager.py              # 설정 관리
│   ├── game_process_manager.py        # 게임 프로세스 관리
│   ├── ui_analyzer.py                 # UI 분석
│   ├── input_monitor.py               # 입력 모니터링 (pynput)
│   ├── action_recorder.py             # 액션 기록
│   ├── semantic_action_recorder.py    # 의미론적 액션 기록
│   ├── semantic_action_replayer.py    # 의미론적 액션 재실행
│   ├── accuracy_tracker.py            # 정확도 추적
│   ├── accuracy_reporter.py           # 정확도 리포팅
│   ├── action_retrainer.py            # 액션 재학습
│   ├── script_generator.py            # 스크립트 생성
│   ├── test_case_manager.py           # 테스트 케이스 관리
│   ├── cli_interface.py               # CLI 인터페이스
│   └── controller.py                  # 메인 컨트롤러
├── tests/
│   ├── property/                      # Property-based tests
│   │   ├── test_config_properties.py
│   │   ├── test_action_properties.py
│   │   ├── test_semantic_properties.py
│   │   ├── test_accuracy_properties.py
│   │   └── test_script_properties.py
│   ├── unit/                          # Unit tests
│   │   ├── test_config_manager.py
│   │   ├── test_ui_analyzer.py
│   │   ├── test_semantic_recorder.py
│   │   ├── test_semantic_replayer.py
│   │   ├── test_accuracy_tracker.py
│   │   └── test_action_retrainer.py
│   └── integration/                   # Integration tests
│       └── test_full_workflow.py
├── test_cases/                        # 저장된 테스트 케이스
├── screenshots/                       # 캡처된 스크린샷
├── accuracy_data/                     # 정확도 데이터
│   └── <test_case_name>/
│       ├── <session_id>_stats.json
│       └── <session_id>_results.json
├── reports/                           # HTML 리포트
├── failures/                          # 실패 스크린샷
├── config.json                        # 설정 파일
├── requirements.txt                   # Python 의존성
├── main.py                            # 진입점
└── README.md                          # 사용 설명서
```

### 2. 의존성

```txt
# requirements.txt
boto3>=1.34.0              # AWS SDK
pynput>=1.7.6              # 입력 모니터링 (마우스/키보드 캡처)
pyautogui>=0.9.54          # GUI 자동화 (액션 재실행)
pillow>=10.0.0             # 이미지 처리
imagehash>=4.3.1           # 이미지 해시
paddleocr>=2.7.0           # OCR (폴백)
plotly>=5.18.0             # 그래프 시각화 (HTML 리포트)
hypothesis>=6.92.0         # Property-based testing
pytest>=7.4.0              # 테스트 프레임워크
pytest-cov>=4.1.0          # 커버리지
```

### 3. 환경 변수

```bash
# AWS 인증
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=ap-northeast-2

# 선택사항
export QA_CONFIG_PATH=config.json
export QA_LOG_LEVEL=INFO
```

### 4. 성능 고려사항

**스크린샷 최적화**:
- 화면 해상도가 1920x1080을 초과하면 리사이즈
- PNG 압축 레벨 조정으로 파일 크기 감소
- 불필요한 스크린샷 자동 정리

**Vision LLM 호출 최적화**:
- 이미지 크기를 1MB 이하로 유지
- 동일한 화면에 대한 중복 분석 방지 (캐싱)
- 배치 분석 지원 (여러 화면을 한 번에 분석)

**메모리 관리**:
- 대용량 스크린샷은 즉시 디스크에 저장
- 액션 리스트가 1000개를 초과하면 경고
- 오래된 테스트 케이스 자동 아카이빙

### 5. 보안 고려사항

**AWS 자격증명**:
- 환경 변수 또는 AWS CLI 프로파일 사용
- 설정 파일에 자격증명 저장 금지
- IAM 역할 기반 인증 권장

**민감 정보 보호**:
- 스크린샷에 민감 정보가 포함될 수 있음
- 테스트 케이스 공유 시 주의
- 자동 마스킹 기능 고려

**파일 권한**:
- 생성된 스크립트는 실행 권한 부여
- 설정 파일은 읽기 전용 권장
- 테스트 케이스 디렉토리 접근 제한

### 6. 확장 가능성

**플러그인 시스템**:
- 커스텀 액션 타입 추가 가능
- 다른 Vision LLM 모델 지원
- 추가 검증 방법 구현

**멀티 플랫폼 지원**:
- Windows, macOS, Linux 호환
- 플랫폼별 키보드/마우스 매핑
- 화면 해상도 자동 감지

**CI/CD 통합**:
- GitHub Actions 워크플로우 예시 제공
- Docker 컨테이너 지원
- 테스트 결과 리포트 자동 생성

### 7. 로깅

```python
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('qa_automation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('QAAutomation')
```

**로그 레벨**:
- DEBUG: 상세한 디버깅 정보
- INFO: 일반적인 실행 정보
- WARNING: 경고 (폴백, 재시도 등)
- ERROR: 오류 (실패한 액션, API 오류 등)
- CRITICAL: 치명적 오류 (시스템 종료)

### 8. 문서화

**코드 문서화**:
- 모든 public 함수/클래스에 docstring 작성
- Google 스타일 docstring 사용
- 타입 힌트 적극 활용

**사용자 문서**:
- README.md: 빠른 시작 가이드
- TUTORIAL.md: 단계별 튜토리얼
- API.md: API 레퍼런스
- TROUBLESHOOTING.md: 문제 해결 가이드

---

## Phased Development Strategy (단계별 개발 전략)

본 시스템은 복잡도가 높으므로, 점진적으로 개발하여 각 단계마다 실제로 동작하는 시스템을 만들어 테스트한다.

### Phase 1: 기본 기록 및 재실행 (MVP)

**목표**: 사용자 입력을 기록하고 재실행할 수 있는 최소 기능 제품

**구현 범위**:
- ConfigManager: 기본 설정 로드
- GameProcessManager: 게임 실행
- InputMonitor: pynput으로 마우스/키보드 캡처
- ActionRecorder: 기본 액션 기록 (좌표만)
- ScriptGenerator: 간단한 재실행 스크립트 생성
- CLIInterface: record, stop, save, replay 명령만

**검증 방법**:
1. 게임 실행
2. record 명령으로 몇 번 클릭
3. save로 저장
4. replay로 재실행 → 같은 위치 클릭 확인

**예상 소요**: 2-3일

---

### Phase 2: UI 분석 통합

**목표**: Vision LLM으로 UI 요소를 분석하여 맥락 정보 추가

**구현 범위**:
- UIAnalyzer: AWS Bedrock Claude Sonnet 4.5 연동
- SemanticActionRecorder: 클릭 시 UI 요소 분석
- 간단한 의미론적 정보 저장 (버튼 텍스트, 타입만)

**검증 방법**:
1. record 중 버튼 클릭
2. 저장된 JSON에서 버튼 텍스트 확인
3. 로그에서 "입장 버튼 클릭" 같은 의미 확인

**예상 소요**: 2-3일

---

### Phase 3: 의미론적 재실행

**목표**: 좌표가 변경되어도 의미로 찾아서 재실행

**구현 범위**:
- SemanticActionReplayer: 의미론적 매칭 구현
- 원래 좌표 실패 시 Vision LLM으로 요소 찾기
- 간단한 성공/실패 로그

**검증 방법**:
1. 테스트 케이스 기록
2. 게임 UI 약간 변경 (버튼 위치 이동)
3. replay 실행 → 새 위치에서도 성공 확인

**예상 소요**: 3-4일

---

### Phase 4: 정확도 추적 기본

**목표**: 재실행 결과를 추적하고 통계 표시

**구현 범위**:
- AccuracyTracker: 성공/실패 기록
- 간단한 통계 계산 (성공률만)
- stats 명령으로 CLI에 표시

**검증 방법**:
1. 여러 번 replay 실행
2. stats 명령으로 성공률 확인
3. 세션별 이력 확인

**예상 소요**: 2일

---

### Phase 5: 대화형 오류 표시

**목표**: 재실행 중 오동작을 표시하고 개선

**구현 범위**:
- InteractiveReplayer: pause, mark_error 명령
- 간단한 재분석 (Vision LLM 재호출)
- 테스트 케이스 업데이트

**검증 방법**:
1. replay 중 pause
2. mark_error로 오류 표시
3. 개선된 정보 확인 및 수락
4. 다시 replay → 성공 확인

**예상 소요**: 2-3일

---

### Phase 6: 통계 시각화

**목표**: HTML 리포트 생성

**구현 범위**:
- AccuracyReporter: HTML 템플릿 생성
- Plotly로 간단한 그래프 (성공률 추세만)
- report 명령

**검증 방법**:
1. 여러 세션 실행
2. report 명령
3. 브라우저에서 HTML 확인

**예상 소요**: 2일

---

### Phase 7: 자동 재학습

**목표**: 실패율 높은 액션 자동 개선

**구현 범위**:
- ActionRetrainer: 재학습 후보 찾기
- 패턴 분석 (간단한 규칙 기반)
- retrain 명령

**검증 방법**:
1. 의도적으로 실패하는 액션 만들기
2. retrain 명령으로 후보 확인
3. 재학습 실행 → 개선 확인

**예상 소요**: 3-4일

---

### Phase 8: 고급 기능 및 최적화

**목표**: 성능 개선 및 추가 기능

**구현 범위**:
- 화면 전환 검증 강화
- OCR 폴백 구현
- 캐싱 및 성능 최적화
- 에러 처리 강화

**예상 소요**: 3-5일

---

## Phase별 의존성

```
Phase 1 (MVP)
    ↓
Phase 2 (UI 분석) ← Phase 1 필수
    ↓
Phase 3 (의미론적 재실행) ← Phase 2 필수
    ↓
Phase 4 (정확도 추적) ← Phase 3 필수
    ↓
Phase 5 (오류 표시) ← Phase 4 필수
    ↓
Phase 6 (시각화) ← Phase 4 필수 (Phase 5 선택)
    ↓
Phase 7 (재학습) ← Phase 4, 5 필수
    ↓
Phase 8 (최적화) ← 모든 Phase 완료 후
```

## 각 Phase의 성공 기준

### Phase 1 성공 기준 및 테스트
- [ ] 게임이 정상적으로 실행됨
- [ ] 마우스 클릭이 기록됨
- [ ] 키보드 입력이 기록됨
- [ ] 재실행 스크립트가 생성됨
- [ ] 재실행 시 같은 좌표에서 클릭됨

**테스트 방법**:
1. **Unit Tests**:
   - `test_config_manager.py`: 설정 로드/저장
   - `test_input_monitor.py`: 입력 이벤트 캡처
   - `test_action_recorder.py`: 액션 기록 형식
   - `test_script_generator.py`: 스크립트 생성 형식

2. **Integration Test**:
   - `test_phase1_workflow.py`: 전체 워크플로우
     ```python
     def test_record_and_replay():
         # 1. 게임 실행
         controller.start_game()
         
         # 2. 기록 시작
         controller.start_recording()
         
         # 3. 시뮬레이션된 입력 (테스트용)
         simulate_click(100, 200)
         simulate_key_press('a')
         
         # 4. 기록 중지
         controller.stop_recording()
         actions = controller.get_actions()
         assert len(actions) == 2
         
         # 5. 저장
         controller.save_test_case("test_case_1")
         
         # 6. 재실행
         controller.load_test_case("test_case_1")
         controller.replay_test_case()
         
         # 7. 검증: 같은 좌표에서 실행되었는지 확인
         assert verify_actions_executed(actions)
     ```

3. **Manual Test Guide** (`docs/phase1_manual_test.md`):
   ```markdown
   # Phase 1 수동 테스트 가이드
   
   ## 준비
   1. 간단한 테스트 게임 준비 (또는 메모장)
   2. config.json 설정 확인
   
   ## 테스트 시나리오 1: 기본 기록
   1. `python main.py` 실행
   2. `start` 명령으로 게임 실행
   3. `record` 명령으로 기록 시작
   4. 게임에서 3번 클릭
   5. `stop` 명령으로 기록 중지
   6. "3개 액션 기록됨" 메시지 확인
   
   ## 테스트 시나리오 2: 재실행
   1. `save test1` 명령으로 저장
   2. `test_cases/test1.py` 파일 생성 확인
   3. `replay` 명령으로 재실행
   4. 같은 위치에서 클릭되는지 육안 확인
   
   ## 예상 결과
   - 모든 클릭이 정확한 좌표에서 재현됨
   - 타이밍이 자연스러움
   ```

### Phase 2 성공 기준 및 테스트
- [ ] Vision LLM API 호출 성공
- [ ] 버튼 텍스트가 추출됨
- [ ] UI 요소 타입이 식별됨
- [ ] 의미론적 정보가 JSON에 저장됨

**테스트 방법**:
1. **Unit Tests**:
   - `test_ui_analyzer.py`: Vision LLM 호출 (mocking)
   - `test_semantic_recorder.py`: 의미론적 정보 추출

2. **Integration Test**:
   - `test_phase2_ui_analysis.py`:
     ```python
     def test_semantic_action_recording():
         # 1. 테스트 이미지 준비 (버튼이 있는 화면)
         test_image = load_test_image("button_screen.png")
         
         # 2. UI 분석
         result = ui_analyzer.analyze_with_vision_llm(test_image)
         
         # 3. 버튼 정보 확인
         assert "buttons" in result
         assert len(result["buttons"]) > 0
         assert result["buttons"][0]["text"] == "입장"
         
         # 4. 의미론적 액션 기록
         action = semantic_recorder.record_click(640, 400)
         
         # 5. 의미론적 정보 확인
         assert action.semantic_info["target_element"]["text"] == "입장"
         assert action.semantic_info["target_element"]["type"] == "button"
     ```

3. **Manual Test Guide** (`docs/phase2_manual_test.md`):
   ```markdown
   # Phase 2 수동 테스트 가이드
   
   ## 준비
   1. AWS 자격증명 설정
   2. 버튼이 명확한 게임 화면 준비
   
   ## 테스트 시나리오: UI 분석
   1. 게임 실행 및 기록 시작
   2. "입장" 버튼 클릭
   3. 기록 중지 및 저장
   4. `test_cases/test1.json` 파일 열기
   5. semantic_info 필드 확인:
      - target_element.text = "입장"
      - target_element.type = "button"
   
   ## 예상 결과
   - JSON에 의미론적 정보가 포함됨
   - 버튼 텍스트가 정확히 추출됨
   ```

### Phase 3 성공 기준 및 테스트
- [ ] 원래 좌표로 먼저 시도함
- [ ] 실패 시 의미론적 매칭 시도함
- [ ] 버튼 위치가 바뀌어도 찾아서 클릭함
- [ ] 로그에 매칭 방법이 기록됨

**테스트 방법**:
1. **Unit Tests**:
   - `test_semantic_replayer.py`: 의미론적 매칭 로직

2. **Integration Test**:
   - `test_phase3_semantic_replay.py`:
     ```python
     def test_semantic_matching_on_ui_change():
         # 1. 원본 UI에서 기록
         original_button_pos = (640, 400)
         action = record_button_click(original_button_pos, "입장")
         
         # 2. UI 변경 시뮬레이션 (버튼 위치 이동)
         new_button_pos = (700, 450)
         simulate_ui_change(button_text="입장", new_pos=new_button_pos)
         
         # 3. 재실행
         result = replayer.replay_action(action)
         
         # 4. 검증
         assert result.success == True
         assert result.method == "semantic"
         assert result.coordinate_change == (60, 50)
     ```

3. **Property-Based Test**:
   - `test_semantic_properties.py`:
     ```python
     @given(button_text=st.text(min_size=1),
            original_pos=st.tuples(st.integers(0, 1920), st.integers(0, 1080)),
            new_pos=st.tuples(st.integers(0, 1920), st.integers(0, 1080)))
     def test_semantic_matching_always_finds_button(button_text, original_pos, new_pos):
         """Property: 버튼 텍스트가 같으면 위치가 바뀌어도 찾아야 함"""
         # 기록
         action = create_semantic_action(original_pos, button_text)
         
         # UI 변경
         update_button_position(button_text, new_pos)
         
         # 재실행
         result = replayer.replay_action(action)
         
         # 검증
         assert result.success == True
     ```

4. **Manual Test Guide** (`docs/phase3_manual_test.md`):
   ```markdown
   # Phase 3 수동 테스트 가이드
   
   ## 테스트 시나리오: UI 변경 대응
   1. 게임에서 "입장" 버튼 클릭 기록
   2. 저장
   3. 게임 UI 변경 (버튼 위치 이동 또는 크기 변경)
   4. 재실행
   5. 로그 확인: "의미론적 매칭 성공 (좌표 변경: ...)"
   6. 새 위치에서 클릭되는지 확인
   
   ## 예상 결과
   - 버튼 위치가 바뀌어도 성공적으로 클릭됨
   - 로그에 좌표 변경 거리가 표시됨
   ```

### Phase 4 성공 기준 및 테스트
- [ ] 각 액션의 성공/실패가 기록됨
- [ ] 세션별 통계가 계산됨
- [ ] stats 명령으로 통계 표시됨
- [ ] 통계가 JSON 파일로 저장됨

**테스트 방법**:
1. **Unit Tests**:
   - `test_accuracy_tracker.py`: 통계 계산 로직
     ```python
     def test_calculate_statistics():
         tracker = AccuracyTracker("test_case")
         
         # 성공 3개, 실패 2개 기록
         tracker.record_success(action1, "direct")
         tracker.record_success(action2, "semantic", (10, 20))
         tracker.record_success(action3, "direct")
         tracker.record_failure(action4, "element_not_found")
         tracker.record_failure(action5, "unexpected_transition")
         
         stats = tracker.calculate_statistics()
         
         assert stats["success_rate"] == 60.0  # 3/5
         assert stats["direct_match_rate"] == 40.0  # 2/5
         assert stats["semantic_match_rate"] == 20.0  # 1/5
         assert "element_not_found" in stats["failure_reasons"]
     ```

2. **Property-Based Test**:
   - `test_accuracy_properties.py`:
     ```python
     @given(successes=st.integers(0, 100),
            failures=st.integers(0, 100))
     def test_success_rate_calculation(successes, failures):
         """Property: 성공률은 항상 0-100 사이"""
         tracker = AccuracyTracker("test")
         
         for _ in range(successes):
             tracker.record_success(create_action(), "direct")
         for _ in range(failures):
             tracker.record_failure(create_action(), "error")
         
         stats = tracker.calculate_statistics()
         
         if successes + failures > 0:
             assert 0 <= stats["success_rate"] <= 100
     ```

3. **Manual Test Guide** (`docs/phase4_manual_test.md`):
   ```markdown
   # Phase 4 수동 테스트 가이드
   
   ## 테스트 시나리오: 정확도 추적
   1. 테스트 케이스 3번 재실행
   2. `stats` 명령 실행
   3. 출력 확인:
      - 세션 ID
      - 성공률
      - 직접 매칭 vs 의미론적 매칭 비율
   4. `accuracy_data/test_case/` 디렉토리 확인
   5. JSON 파일들이 생성되었는지 확인
   
   ## 예상 결과
   - 각 세션의 통계가 표시됨
   - JSON 파일에 상세 데이터가 저장됨
   ```

### Phase 5 성공 기준 및 테스트
- [ ] pause 명령으로 일시정지됨
- [ ] mark_error로 오류 표시 가능
- [ ] Vision LLM으로 재분석됨
- [ ] 개선된 정보로 업데이트됨

**테스트 방법**:
- **Manual Test Guide** (`docs/phase5_manual_test.md`): 대화형 기능은 수동 테스트 중심
- **Integration Test**: 오류 표시 후 테스트 케이스 업데이트 검증

### Phase 6 성공 기준 및 테스트
- [ ] HTML 파일이 생성됨
- [ ] 그래프가 표시됨
- [ ] 브라우저에서 정상 렌더링됨

**테스트 방법**:
- **Unit Test**: HTML 생성 로직
- **Visual Test**: 브라우저에서 렌더링 확인
- **Manual Test Guide** (`docs/phase6_manual_test.md`)

### Phase 7 성공 기준 및 테스트
- [ ] 실패율 30% 이상 액션이 감지됨
- [ ] 재학습 후보 목록이 표시됨
- [ ] 재학습 실행 후 정확도 향상됨

**테스트 방법**:
- **Unit Test**: 재학습 후보 찾기 로직
- **Integration Test**: 재학습 전후 정확도 비교
- **Manual Test Guide** (`docs/phase7_manual_test.md`)

### Phase 8 성공 기준 및 테스트
- [ ] 전체 워크플로우가 안정적으로 동작함
- [ ] 성능이 허용 범위 내임
- [ ] 모든 에러가 우아하게 처리됨

**테스트 방법**:
- **End-to-End Test**: 전체 워크플로우
- **Performance Test**: 응답 시간 측정
- **Stress Test**: 대량 액션 처리
- **Error Injection Test**: 다양한 오류 시나리오

---

## Future Enhancements (향후 개선사항)

### Phase 9+ 기능

1. **멀티 모니터 지원**
   - 특정 모니터 선택 기능
   - 모니터 간 좌표 변환

2. **GPU 가속 스크린샷**
   - NVIDIA NVENC 활용
   - 실시간 화면 캡처 성능 향상

3. **실시간 UI 변화 감지**
   - 화면 diff 알고리즘
   - 변화 감지 시 자동 분석

4. **자동 테스트 케이스 생성**
   - 게임 플레이 자동 기록
   - AI 기반 테스트 시나리오 추천

5. **CI/CD 파이프라인 통합**
   - Jenkins, GitLab CI 플러그인
   - 자동 회귀 테스트 실행

6. **테스트 결과 리포트**
   - HTML/PDF 리포트 생성
   - 스크린샷 비교 시각화
   - 성능 메트릭 차트

7. **협업 기능**
   - 테스트 케이스 공유 플랫폼
   - 팀 대시보드
   - 실시간 테스트 실행 모니터링

8. **고급 검증**
   - 픽셀 단위 비교
   - 특정 영역만 검증
   - 동적 임계값 조정

---

## Glossary (용어집)

- **Property-Based Testing**: 입력 공간 전체에 대해 속성이 유지되는지 검증하는 테스트 방법
- **Round Trip**: 데이터를 변환한 후 역변환하여 원본과 동일한지 확인하는 패턴
- **Exponential Backoff**: 재시도 간격을 지수적으로 증가시키는 재시도 전략
- **Image Hash**: 이미지의 시각적 특징을 해시값으로 변환한 것
- **Invariant**: 프로그램 실행 중 항상 참이어야 하는 조건
- **Idempotence**: 동일한 연산을 여러 번 수행해도 결과가 동일한 성질
- **Serialization**: 데이터 구조를 저장 가능한 형식으로 변환하는 과정

---

**문서 끝**
