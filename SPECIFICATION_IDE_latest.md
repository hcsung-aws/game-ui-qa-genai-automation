# Unreal 게임 QA 자동화 명세서 (Kiro IDE 기반)

**작성일**: 2025-12-13  
**버전**: 1.0  
**목적**: Kiro IDE에서 게임 실행 → Claude Sonnet 4.5로 UI 분석 → PyAutoGUI로 자동화 → 반복 실행 스크립트 생성

---

## 1. 시스템 아키텍처

```
[게임 EXE] → [스크린샷] → [Claude Sonnet 4.5] → [UI 분석 결과]
                ↓                                      ↓
         [PyAutoGUI] ← ← ← ← ← ← ← ← ← ← ← [좌표/액션 추출]
                ↓
         [액션 기록] → [재실행 스크립트 생성]
```

### 기술 스택
- **Vision LLM**: AWS Bedrock Claude Sonnet 4.5 (`anthropic.claude-sonnet-4-5-20250929-v1:0`)
- **UI 자동화**: PyAutoGUI
- **OCR (보조)**: PaddleOCR (94% 정확도)
- **리전**: ap-northeast-2 (서울)
- **실행 환경**: Kiro IDE

---

## 2. 워크플로우

### Phase 1: 초기 설정 및 게임 실행
```python
# 1. 게임 실행
import subprocess
game_path = "C:/path/to/game.exe"
process = subprocess.Popen(game_path)

# 2. 게임 창 활성화 대기
import time
time.sleep(5)  # 게임 로딩 대기
```

### Phase 2: UI 분석 및 액션 기록
```python
import pyautogui
import boto3
import json
import base64
from datetime import datetime

# Bedrock 클라이언트 초기화
bedrock = boto3.client('bedrock-runtime', region_name='ap-northeast-2')

# 액션 기록 리스트
actions = []

def capture_and_analyze():
    """현재 화면 캡처 및 Claude 분석"""
    # 스크린샷 캡처
    screenshot = pyautogui.screenshot()
    screenshot.save('temp_screen.png')
    
    # 이미지 인코딩
    with open('temp_screen.png', 'rb') as f:
        img_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Claude Sonnet 4.5 호출
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_data}},
                {"type": "text", "text": """이 게임 UI를 분석하여 JSON으로 응답:
{
  "buttons": [{"text": "버튼명", "x": 100, "y": 200, "width": 80, "height": 40}],
  "icons": [{"type": "아이콘종류", "x": 300, "y": 150}],
  "text_fields": [{"content": "텍스트내용", "x": 400, "y": 100}]
}"""}
            ]
        }]
    })
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-sonnet-4-5-20250929-v1:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    return json.loads(result['content'][0]['text'])

def record_action(action_type, x, y, description):
    """액션 기록"""
    actions.append({
        "timestamp": datetime.now().isoformat(),
        "type": action_type,
        "x": x,
        "y": y,
        "description": description
    })
```

### Phase 3: 대화형 UI 탐색 및 액션 실행
```python
def interactive_qa_session():
    """Kiro IDE에서 대화형으로 QA 진행"""
    print("=== 게임 QA 자동화 세션 시작 ===")
    print("명령어: analyze, click <x> <y>, type <text>, wait <seconds>, save, quit")
    
    while True:
        cmd = input("\n명령 입력> ").strip().split()
        
        if cmd[0] == "analyze":
            # 현재 화면 분석
            ui_data = capture_and_analyze()
            print(json.dumps(ui_data, indent=2, ensure_ascii=False))
            
        elif cmd[0] == "click":
            # 클릭 실행
            x, y = int(cmd[1]), int(cmd[2])
            pyautogui.click(x, y)
            record_action("click", x, y, f"클릭: ({x}, {y})")
            print(f"✓ 클릭 완료: ({x}, {y})")
            
        elif cmd[0] == "type":
            # 텍스트 입력
            text = " ".join(cmd[1:])
            pyautogui.write(text)
            record_action("type", 0, 0, f"입력: {text}")
            print(f"✓ 입력 완료: {text}")
            
        elif cmd[0] == "wait":
            # 대기
            seconds = int(cmd[1])
            time.sleep(seconds)
            record_action("wait", 0, 0, f"대기: {seconds}초")
            print(f"✓ {seconds}초 대기 완료")
            
        elif cmd[0] == "save":
            # 스크립트 저장
            save_replay_script()
            print("✓ 재실행 스크립트 저장 완료")
            
        elif cmd[0] == "quit":
            print("세션 종료")
            break
```

### Phase 4: 재실행 스크립트 생성
```python
def save_replay_script():
    """기록된 액션을 재실행 스크립트로 저장"""
    script_content = '''#!/usr/bin/env python3
"""
자동 생성된 게임 QA 재실행 스크립트
생성일: {timestamp}
"""
import pyautogui
import time

def replay_actions():
    """기록된 액션 재실행"""
    actions = {actions_json}
    
    for action in actions:
        print(f"[{{action['timestamp']}}] {{action['description']}}")
        
        if action['type'] == 'click':
            pyautogui.click(action['x'], action['y'])
        elif action['type'] == 'type':
            pyautogui.write(action['description'].replace('입력: ', ''))
        elif action['type'] == 'wait':
            wait_time = int(action['description'].split(':')[1].replace('초', '').strip())
            time.sleep(wait_time)
        
        time.sleep(0.5)  # 액션 간 기본 대기

if __name__ == "__main__":
    print("=== 게임 QA 재실행 시작 ===")
    replay_actions()
    print("=== 재실행 완료 ===")
'''.format(
        timestamp=datetime.now().isoformat(),
        actions_json=json.dumps(actions, indent=4, ensure_ascii=False)
    )
    
    with open('qa_replay_script.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
```

---

## 3. 실행 가이드

### 3.1 Kiro IDE에서 초기 실행
```bash
# 1. 필요한 패키지 설치
pip install pyautogui boto3 pillow paddleocr

# 2. AWS 자격증명 설정
export AWS_REGION=ap-northeast-2
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# 3. 메인 스크립트 실행
python qa_automation_main.py
```

### 3.2 대화형 QA 세션 예시
```
명령 입력> analyze
{
  "buttons": [
    {"text": "Start Game", "x": 640, "y": 400, "width": 200, "height": 60}
  ]
}

명령 입력> click 640 400
✓ 클릭 완료: (640, 400)

명령 입력> wait 3
✓ 3초 대기 완료

명령 입력> analyze
{
  "buttons": [
    {"text": "New Game", "x": 640, "y": 300},
    {"text": "Load Game", "x": 640, "y": 400}
  ]
}

명령 입력> click 640 300
✓ 클릭 완료: (640, 300)

명령 입력> save
✓ 재실행 스크립트 저장 완료

명령 입력> quit
세션 종료
```

### 3.3 재실행 및 검증
```bash
# 생성된 스크립트 실행
python qa_replay_script.py

# 검증 모드로 실행 (스크린샷 비교)
python qa_replay_script.py --verify
```

---

## 4. 고급 기능

### 4.1 OCR 폴백 (PaddleOCR)
```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='en')

def ocr_fallback(image_path):
    """Claude 실패 시 OCR 사용"""
    result = ocr.ocr(image_path)
    texts = []
    for line in result[0]:
        texts.append({
            "text": line[1][0],
            "confidence": line[1][1],
            "bbox": line[0]
        })
    return texts
```

### 4.2 스크린샷 비교 검증
```python
from PIL import Image
import imagehash

def verify_ui_state(expected_hash):
    """UI 상태 검증"""
    screenshot = pyautogui.screenshot()
    current_hash = imagehash.average_hash(screenshot)
    return current_hash - expected_hash < 5  # 유사도 임계값
```

### 4.3 에러 처리 및 재시도
```python
def robust_click(x, y, max_retries=3):
    """재시도 로직이 있는 클릭"""
    for attempt in range(max_retries):
        try:
            pyautogui.click(x, y)
            time.sleep(0.5)
            
            # UI 변화 확인
            ui_data = capture_and_analyze()
            if ui_changed(ui_data):
                return True
        except Exception as e:
            print(f"재시도 {attempt + 1}/{max_retries}: {e}")
    
    return False
```

---

## 5. 파일 구조

```
unreal-qa-automation/
├── SPECIFICATION_IDE_latest.md          # 본 명세서
├── qa_automation_main.py                # 메인 스크립트
├── qa_replay_script.py                  # 자동 생성된 재실행 스크립트
├── actions_log.json                     # 액션 기록 JSON
├── screenshots/                         # 캡처된 스크린샷
│   ├── step_001.png
│   ├── step_002.png
│   └── ...
└── config.json                          # 설정 파일
```

---

## 6. 설정 파일 (config.json)

```json
{
  "aws": {
    "region": "ap-northeast-2",
    "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0"
  },
  "game": {
    "exe_path": "C:/path/to/game.exe",
    "window_title": "Game Window Title",
    "startup_wait": 5
  },
  "automation": {
    "action_delay": 0.5,
    "screenshot_on_action": true,
    "verify_mode": false
  }
}
```

---

## 7. 통합 메인 스크립트 (qa_automation_main.py)

```python
#!/usr/bin/env python3
import json
import subprocess
import pyautogui
import boto3
import base64
from datetime import datetime
import time

class GameQAAutomation:
    def __init__(self, config_path='config.json'):
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=self.config['aws']['region']
        )
        self.actions = []
        self.process = None
    
    def start_game(self):
        """게임 실행"""
        self.process = subprocess.Popen(self.config['game']['exe_path'])
        time.sleep(self.config['game']['startup_wait'])
        print("✓ 게임 실행 완료")
    
    def analyze_ui(self):
        """Claude Sonnet 4.5로 UI 분석"""
        screenshot = pyautogui.screenshot()
        screenshot.save('temp.png')
        
        with open('temp.png', 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_data}},
                    {"type": "text", "text": "게임 UI의 모든 클릭 가능한 요소를 JSON으로 반환"}
                ]
            }]
        })
        
        response = self.bedrock.invoke_model(
            modelId=self.config['aws']['model_id'],
            body=body
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
    
    def record_action(self, action_type, x, y, desc):
        """액션 기록"""
        self.actions.append({
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "x": x,
            "y": y,
            "description": desc
        })
    
    def interactive_session(self):
        """대화형 세션"""
        print("=== 게임 QA 자동화 시작 ===")
        print("명령: analyze | click <x> <y> | wait <sec> | save | quit")
        
        while True:
            cmd = input("\n> ").strip().split()
            if not cmd:
                continue
            
            if cmd[0] == "analyze":
                print(self.analyze_ui())
            elif cmd[0] == "click" and len(cmd) == 3:
                x, y = int(cmd[1]), int(cmd[2])
                pyautogui.click(x, y)
                self.record_action("click", x, y, f"클릭 ({x},{y})")
                print(f"✓ 클릭: ({x}, {y})")
            elif cmd[0] == "wait" and len(cmd) == 2:
                sec = int(cmd[1])
                time.sleep(sec)
                self.record_action("wait", 0, 0, f"{sec}초 대기")
                print(f"✓ {sec}초 대기")
            elif cmd[0] == "save":
                self.save_replay_script()
                print("✓ 스크립트 저장 완료")
            elif cmd[0] == "quit":
                break
    
    def save_replay_script(self):
        """재실행 스크립트 저장"""
        with open('qa_replay_script.py', 'w', encoding='utf-8') as f:
            f.write(f'''#!/usr/bin/env python3
import pyautogui
import time

actions = {json.dumps(self.actions, indent=2, ensure_ascii=False)}

for action in actions:
    print(f"[{{action['timestamp']}}] {{action['description']}}")
    if action['type'] == 'click':
        pyautogui.click(action['x'], action['y'])
    elif action['type'] == 'wait':
        time.sleep(int(action['description'].split('초')[0]))
    time.sleep(0.5)
''')

if __name__ == "__main__":
    qa = GameQAAutomation()
    qa.start_game()
    qa.interactive_session()
```

---

## 8. 검증 및 테스트

### 8.1 단위 테스트
```python
def test_claude_connection():
    """Claude Sonnet 4.5 연결 테스트"""
    # 테스트 이미지로 API 호출 확인

def test_pyautogui():
    """PyAutoGUI 동작 테스트"""
    # 마우스 이동, 클릭 테스트

def test_replay_script():
    """재실행 스크립트 검증"""
    # 저장된 스크립트 실행 및 결과 확인
```

### 8.2 통합 테스트
```bash
# 전체 워크플로우 테스트
python qa_automation_main.py --test-mode
```

---

## 9. 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| Claude API 타임아웃 | 이미지 크기 과다 | 이미지 리사이즈 (1920x1080 이하) |
| PyAutoGUI 클릭 실패 | 게임 창 비활성화 | 창 활성화 후 재시도 |
| OCR 인식 실패 | 스타일화된 폰트 | Claude Vision 사용 |
| 재실행 스크립트 오류 | 타이밍 이슈 | wait 시간 증가 |

---

## 10. 향후 개선 사항

- [ ] 멀티 모니터 지원
- [ ] GPU 가속 스크린샷
- [ ] 실시간 UI 변화 감지
- [ ] 자동 테스트 케이스 생성
- [ ] CI/CD 파이프라인 통합
- [ ] 테스트 결과 리포트 자동 생성

---

**문서 끝**
