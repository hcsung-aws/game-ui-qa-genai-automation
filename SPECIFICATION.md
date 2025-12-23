# Unreal 게임 QA 자동화 시스템 명세서

## 개요

AWS Bedrock + Rekognition + PyAutoGUI를 활용한 블랙박스 게임 테스트 자동화 시스템

**핵심 기능:**
- 자연어 명령으로 테스트 시나리오 정의
- Rekognition으로 UI 요소 자동 감지 및 좌표 추출
- 테스트 스크립트 자동 생성
- 반복 실행 및 자동 검증

**실행 환경:**
- **WSL (Linux)**: Kiro CLI, AWS API 호출, 스크립트 생성, 결과 분석
- **Windows**: 게임 실행, PyAutoGUI 제어, 스크린샷 캡처
- **통신**: 공유 파일 시스템 (`/mnt/c/`), JSON 파일로 명령/결과 전달

---

## WSL-Windows 하이브리드 아키텍처

### 환경 제약사항

1. **Kiro CLI는 WSL에서 실행**
   - Linux 환경이므로 Windows GUI 직접 제어 불가
   - PyAutoGUI는 GUI 환경 필요

2. **게임은 Windows에서 실행**
   - Unreal 빌드는 Windows 네이티브 실행 파일
   - 스크린샷 캡처도 Windows에서만 가능

### 해결 방안: 역할 분리

```
┌─────────────────────────────────────────────────────────────┐
│                         WSL (Linux)                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Kiro CLI / Main Orchestrator                         │  │
│  │  - AWS Bedrock API 호출 (이미지 분석, 의사결정)       │  │
│  │  - AWS Rekognition API 호출 (UI 요소 감지)           │  │
│  │  - Windows 실행 스크립트 생성                         │  │
│  │  - 결과 분석 및 리포트 생성                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↕                                │
│                  공유 파일 시스템 (/mnt/c/)                 │
│                  - 명령 JSON 파일                           │
│                  - 스크린샷 PNG 파일                        │
│                  - 결과 JSON 파일                           │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                       Windows                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Windows Python + PyAutoGUI                           │  │
│  │  - 게임 실행 (subprocess)                             │  │
│  │  - 마우스/키보드 제어 (pyautogui)                     │  │
│  │  - 스크린샷 캡처 (pyautogui.screenshot)               │  │
│  │  - 명령 JSON 읽기 → 실행 → 결과 JSON 저장            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 실행 흐름

1. **WSL**: 사용자 명령 받음 → Bedrock로 단계 분해
2. **WSL**: Windows 실행 명령 JSON 생성 (`/mnt/c/.../command.json`)
3. **WSL**: Windows Python 실행 (`python.exe windows_executor.py`)
4. **Windows**: JSON 읽기 → 게임 실행 → 클릭 → 스크린샷 저장
5. **WSL**: 스크린샷 읽기 → Rekognition/Bedrock 분석
6. **반복**

---

## WSL-Windows 통신 프로토콜

### 명령 전달 (WSL → Windows)

**command.json 구조:**
```json
{
  "action": "click",
  "target": {"x": 960, "y": 540},
  "screenshot_before": "/mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots/step_1_before.png",
  "screenshot_after": "/mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots/step_1_after.png",
  "wait_time": 2.0
}
```

### 결과 전달 (Windows → WSL)

**result.json 구조:**
```json
{
  "status": "success",
  "action_executed": "click",
  "coordinates": {"x": 960, "y": 540},
  "timestamp": 1702345678.123,
  "screenshot_saved": true,
  "error": null
}
```

### Windows 실행기 (windows_executor.py)

```python
# windows_executor.py
# Windows에서 실행되는 PyAutoGUI 제어 스크립트
import pyautogui
import json
import time
import subprocess
from pathlib import Path

COMMAND_FILE = "C:/Users/hcsung/work/q/unreal-qa-automation/command.json"
RESULT_FILE = "C:/Users/hcsung/work/q/unreal-qa-automation/result.json"

def execute_command():
    """명령 JSON 읽고 실행"""
    
    # 명령 읽기
    with open(COMMAND_FILE, 'r') as f:
        cmd = json.load(f)
    
    result = {
        "status": "success",
        "action_executed": cmd['action'],
        "timestamp": time.time(),
        "error": None
    }
    
    try:
        if cmd['action'] == 'launch_game':
            # 게임 실행
            subprocess.Popen([cmd['game_exe']])
            time.sleep(cmd.get('wait_time', 10))
            
        elif cmd['action'] == 'click':
            # 클릭 전 스크린샷
            if 'screenshot_before' in cmd:
                screenshot = pyautogui.screenshot()
                # Windows 경로로 변환
                win_path = cmd['screenshot_before'].replace('/mnt/c/', 'C:/')
                screenshot.save(win_path)
            
            # 클릭 실행
            x, y = cmd['target']['x'], cmd['target']['y']
            pyautogui.click(x, y)
            result['coordinates'] = {'x': x, 'y': y}
            
            # 대기
            time.sleep(cmd.get('wait_time', 2))
            
            # 클릭 후 스크린샷
            if 'screenshot_after' in cmd:
                screenshot = pyautogui.screenshot()
                win_path = cmd['screenshot_after'].replace('/mnt/c/', 'C:/')
                screenshot.save(win_path)
                result['screenshot_saved'] = True
        
        elif cmd['action'] == 'type_text':
            pyautogui.write(cmd['text'], interval=0.1)
            
        elif cmd['action'] == 'press_key':
            pyautogui.press(cmd['key'])
            
        elif cmd['action'] == 'screenshot':
            screenshot = pyautogui.screenshot()
            win_path = cmd['path'].replace('/mnt/c/', 'C:/')
            screenshot.save(win_path)
            result['screenshot_saved'] = True
    
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
    
    # 결과 저장
    with open(RESULT_FILE, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result

if __name__ == "__main__":
    execute_command()
```

### WSL 오케스트레이터 (wsl_orchestrator.py)

```python
# wsl_orchestrator.py
# WSL에서 실행되는 메인 스크립트
import boto3
import json
import time
import subprocess
from pathlib import Path

class WSLOrchestrator:
    def __init__(self, work_dir="/mnt/c/Users/hcsung/work/q/unreal-qa-automation"):
        self.work_dir = Path(work_dir)
        self.command_file = self.work_dir / "command.json"
        self.result_file = self.work_dir / "result.json"
        self.windows_python = "/mnt/c/Program Files/Python313/python.exe"
        self.windows_executor = self.work_dir / "windows_executor.py"
        
        # AWS 클라이언트
        self.rekognition = boto3.client('rekognition', region_name='ap-northeast-2')
        self.bedrock = boto3.client('bedrock-runtime', region_name='ap-northeast-2')
    
    def send_command_to_windows(self, command):
        """WSL에서 Windows로 명령 전달"""
        
        # 명령 JSON 저장
        with open(self.command_file, 'w') as f:
            json.dump(command, f, indent=2)
        
        # Windows Python으로 실행
        # WSL 경로를 Windows 경로로 변환
        win_executor_path = str(self.windows_executor).replace('/mnt/c/', 'C:/')
        
        result = subprocess.run(
            [self.windows_python, win_executor_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Windows 실행 오류: {result.stderr}")
            return None
        
        # 결과 읽기
        time.sleep(0.5)  # 파일 쓰기 완료 대기
        with open(self.result_file, 'r') as f:
            return json.load(f)
    
    def launch_game(self, game_exe):
        """게임 실행"""
        command = {
            'action': 'launch_game',
            'game_exe': game_exe,
            'wait_time': 10
        }
        return self.send_command_to_windows(command)
    
    def click_and_capture(self, x, y, step_num):
        """클릭 및 스크린샷 캡처"""
        command = {
            'action': 'click',
            'target': {'x': x, 'y': y},
            'screenshot_before': f'/mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots/step_{step_num}_before.png',
            'screenshot_after': f'/mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots/step_{step_num}_after.png',
            'wait_time': 2.0
        }
        return self.send_command_to_windows(command)
    
    def capture_screenshot(self, path):
        """스크린샷만 캡처"""
        command = {
            'action': 'screenshot',
            'path': path
        }
        return self.send_command_to_windows(command)
    
    def analyze_with_rekognition(self, screenshot_path):
        """Rekognition으로 UI 요소 분석 (WSL에서 실행)"""
        with open(screenshot_path, 'rb') as image:
            response = self.rekognition.detect_text(Image={'Bytes': image.read()})
        
        elements = []
        for text in response['TextDetections']:
            if text['Type'] == 'LINE':
                bbox = text['Geometry']['BoundingBox']
                elements.append({
                    'text': text['DetectedText'],
                    'confidence': text['Confidence'],
                    'bbox': bbox
                })
        
        return elements
    
    def decide_with_bedrock(self, screenshot_path, step_description, detected_elements):
        """Bedrock Claude로 다음 액션 결정 (WSL에서 실행)"""
        import base64
        
        with open(screenshot_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        prompt = f"""
현재 단계: {step_description}
감지된 UI 요소: {json.dumps(detected_elements, ensure_ascii=False)}

다음 액션을 JSON으로 답변:
{{"target_text": "클릭할 텍스트", "reason": "이유"}}
"""
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                    {"type": "text", "text": prompt}
                ]
            }]
        })
        
        response = self.bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=body
        )
        
        result = json.loads(response['body'].read())
        return json.loads(result['content'][0]['text'])

# 사용 예시
if __name__ == "__main__":
    orchestrator = WSLOrchestrator()
    
    # 1. 게임 실행 (Windows에서)
    orchestrator.launch_game("C:/Builds/MyGame/Windows/MyGame.exe")
    
    # 2. 초기 스크린샷 캡처 (Windows에서)
    orchestrator.capture_screenshot("/mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots/initial.png")
    
    # 3. UI 요소 분석 (WSL에서)
    elements = orchestrator.analyze_with_rekognition(
        "/mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots/initial.png"
    )
    print(f"감지된 요소: {len(elements)}개")
    
    # 4. 다음 액션 결정 (WSL에서)
    action = orchestrator.decide_with_bedrock(
        "/mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots/initial.png",
        "로그인 버튼 클릭",
        elements
    )
    print(f"결정된 액션: {action}")
    
    # 5. 클릭 실행 (Windows에서)
    orchestrator.click_and_capture(960, 540, step_num=1)
```

---

## 시스템 아키텍처

```
[사용자 자연어 명령]
    ↓
[Phase 1: 학습 모드]
    ├─ Bedrock Claude: 명령 해석 및 단계 분해
    ├─ 게임 실행 (PyAutoGUI)
    ├─ 각 단계마다:
    │   ├─ 스크린샷 캡처
    │   ├─ Rekognition DetectText: 버튼/텍스트 감지
    │   ├─ Bedrock Claude: 다음 액션 결정
    │   ├─ PyAutoGUI: 클릭/입력 실행
    │   └─ 좌표 및 액션 기록
    └─ 테스트 스크립트 자동 생성
    
[Phase 2: 실행 모드]
    ├─ 생성된 스크립트 실행
    ├─ 각 단계마다:
    │   ├─ 스크린샷 캡처
    │   ├─ Rekognition: 예상 화면과 비교
    │   └─ 성공/실패 판정
    └─ 결과 리포트 생성
```

---

## Phase 1: 학습 모드 (테스트 스크립트 생성)

### 1.1 사용자 입력 처리

**입력 예시:**
```
"게임을 실행하고 로그인 버튼을 클릭한 다음, 
아이디 testuser, 비밀번호 testpass로 로그인하고, 
메인 메뉴에서 설정 버튼을 눌러 설정 화면이 나오는지 확인"
```

**처리 과정:**
1. Bedrock Claude에 자연어 명령 전달
2. 구조화된 단계로 분해

**출력 예시:**
```json
{
  "steps": [
    {"action": "launch_game", "description": "게임 실행"},
    {"action": "find_and_click", "target": "로그인 버튼"},
    {"action": "input_text", "field": "아이디", "value": "testuser"},
    {"action": "input_text", "field": "비밀번호", "value": "testpass"},
    {"action": "find_and_click", "target": "로그인 확인"},
    {"action": "wait_for_screen", "expected": "메인 메뉴"},
    {"action": "find_and_click", "target": "설정 버튼"},
    {"action": "verify_screen", "expected": "설정 화면"}
  ]
}
```

### 1.2 게임 실행 및 초기화

```python
import subprocess
import time
import pyautogui

GAME_EXE = "C:/Builds/MyGame/Windows/MyGame.exe"

# 게임 실행
process = subprocess.Popen([GAME_EXE])
time.sleep(10)  # 로딩 대기

# 초기 화면 캡처
screenshot = pyautogui.screenshot()
screenshot.save("step_0_initial.png")
```

### 1.3 Rekognition으로 UI 요소 감지

**DetectText API 사용:**

```python
import boto3
import json

rekognition = boto3.client('rekognition', region_name='ap-northeast-2')

def detect_ui_elements(image_path):
    """화면에서 텍스트 및 좌표 추출"""
    with open(image_path, 'rb') as image:
        response = rekognition.detect_text(Image={'Bytes': image.read()})
    
    elements = []
    for text in response['TextDetections']:
        if text['Type'] == 'LINE':  # 단어가 아닌 라인 단위
            bbox = text['Geometry']['BoundingBox']
            elements.append({
                'text': text['DetectedText'],
                'confidence': text['Confidence'],
                'left': bbox['Left'],      # 0~1 비율
                'top': bbox['Top'],
                'width': bbox['Width'],
                'height': bbox['Height']
            })
    
    return elements
```

**좌표 변환 (비율 → 픽셀):**

```python
def get_click_coordinates(bbox, screen_width=1920, screen_height=1080):
    """Rekognition 바운딩 박스를 실제 클릭 좌표로 변환"""
    center_x = (bbox['left'] + bbox['width'] / 2) * screen_width
    center_y = (bbox['top'] + bbox['height'] / 2) * screen_height
    return int(center_x), int(center_y)
```

### 1.4 Bedrock Claude로 다음 액션 결정

```python
bedrock = boto3.client('bedrock-runtime', region_name='ap-northeast-2')

def decide_next_action(current_step, detected_elements, screenshot_path):
    """현재 단계와 감지된 UI 요소를 기반으로 다음 액션 결정"""
    
    # 스크린샷을 base64로 인코딩
    import base64
    with open(screenshot_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Bedrock Claude 호출
    prompt = f"""
현재 테스트 단계: {current_step['description']}
목표 액션: {current_step['action']}
찾아야 할 대상: {current_step.get('target', 'N/A')}

화면에서 감지된 텍스트:
{json.dumps(detected_elements, indent=2, ensure_ascii=False)}

이 화면에서 다음 액션을 수행하려면 어떤 텍스트를 클릭해야 하나요?
JSON 형식으로 답변해주세요:
{{"target_text": "클릭할 텍스트", "reason": "이유"}}
"""
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    })
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    return json.loads(result['content'][0]['text'])
```

### 1.5 액션 실행 및 기록

```python
def execute_and_record_action(action_decision, detected_elements, step_num):
    """액션 실행 및 기록"""
    
    # 타겟 텍스트 찾기
    target_text = action_decision['target_text']
    target_element = None
    
    for element in detected_elements:
        if target_text.lower() in element['text'].lower():
            target_element = element
            break
    
    if not target_element:
        print(f"❌ '{target_text}' 텍스트를 찾을 수 없음")
        return None
    
    # 클릭 좌표 계산
    x, y = get_click_coordinates(target_element)
    
    # 실제 클릭
    pyautogui.click(x, y)
    print(f"✅ ({x}, {y}) 클릭: {target_text}")
    
    # 액션 기록
    action_record = {
        'step': step_num,
        'action': 'click',
        'target_text': target_text,
        'coordinates': {'x': x, 'y': y},
        'bbox': target_element,
        'timestamp': time.time()
    }
    
    time.sleep(2)  # 화면 전환 대기
    
    # 결과 스크린샷
    screenshot = pyautogui.screenshot()
    screenshot_path = f"step_{step_num}_after.png"
    screenshot.save(screenshot_path)
    
    return action_record
```

### 1.6 스크립트 자동 생성

```python
def generate_test_script(action_records, test_name):
    """기록된 액션들을 실행 가능한 Python 스크립트로 변환"""
    
    script = f'''# Auto-generated test script: {test_name}
import pyautogui
import time
import subprocess

GAME_EXE = "C:/Builds/MyGame/Windows/MyGame.exe"

def run_test():
    """자동 생성된 테스트"""
    
    # 게임 실행
    print("게임 실행 중...")
    subprocess.Popen([GAME_EXE])
    time.sleep(10)
    
'''
    
    for i, record in enumerate(action_records):
        script += f'''    # Step {record['step']}: {record['target_text']}
    print("Step {record['step']}: {record['target_text']} 클릭")
    pyautogui.click({record['coordinates']['x']}, {record['coordinates']['y']})
    time.sleep(2)
    pyautogui.screenshot("verify_step_{record['step']}.png")
    
'''
    
    script += '''    print("✅ 테스트 완료")
    
if __name__ == "__main__":
    run_test()
'''
    
    # 스크립트 저장
    script_path = f"generated_{test_name}.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script)
    
    print(f"✅ 스크립트 생성 완료: {script_path}")
    return script_path
```

### 1.7 검증 데이터 저장

```python
def save_verification_data(action_records, test_name):
    """각 단계의 예상 화면 설명 저장 (이미지 대신 텍스트로)"""
    
    verification_data = {
        'test_name': test_name,
        'steps': []
    }
    
    for record in action_records:
        screenshot_path = f"step_{record['step']}_after.png"
        
        # Bedrock Claude로 화면 설명 생성
        description = describe_screen_with_bedrock(screenshot_path)
        
        verification_data['steps'].append({
            'step': record['step'],
            'action': record['target_text'],
            'expected_screen_description': description,
            'reference_screenshot': screenshot_path
        })
    
    # JSON으로 저장
    with open(f"{test_name}_verification.json", 'w', encoding='utf-8') as f:
        json.dump(verification_data, indent=2, ensure_ascii=False, fp=f)
    
    print(f"✅ 검증 데이터 저장: {test_name}_verification.json")

def describe_screen_with_bedrock(screenshot_path):
    """Bedrock Claude로 화면 설명 생성"""
    import base64
    
    with open(screenshot_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                {"type": "text", "text": "이 게임 화면을 간단히 설명해주세요. 어떤 UI 요소들이 보이나요?"}
            ]
        }]
    })
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    return result['content'][0]['text']
```

---

## Phase 2: 실행 모드 (자동 반복 테스트)

### 2.1 생성된 스크립트 실행

```python
# 생성된 스크립트를 그대로 실행
import subprocess

result = subprocess.run(['python', 'generated_login_test.py'], 
                       capture_output=True, text=True)
print(result.stdout)
```

### 2.2 Rekognition으로 검증

```python
def verify_test_execution(test_name):
    """생성된 스크린샷과 예상 화면 비교"""
    
    # 검증 데이터 로드
    with open(f"{test_name}_verification.json", 'r', encoding='utf-8') as f:
        verification_data = json.load(f)
    
    results = []
    
    for step_data in verification_data['steps']:
        step_num = step_data['step']
        expected_desc = step_data['expected_screen_description']
        
        # 실행 중 캡처된 스크린샷
        actual_screenshot = f"verify_step_{step_num}.png"
        
        # Bedrock Claude로 현재 화면 설명
        actual_desc = describe_screen_with_bedrock(actual_screenshot)
        
        # 두 설명 비교
        is_match = compare_descriptions(expected_desc, actual_desc)
        
        results.append({
            'step': step_num,
            'action': step_data['action'],
            'expected': expected_desc,
            'actual': actual_desc,
            'passed': is_match
        })
        
        print(f"Step {step_num}: {'✅ PASS' if is_match else '❌ FAIL'}")
    
    return results

def compare_descriptions(expected, actual):
    """Bedrock Claude로 두 화면 설명이 유사한지 판단"""
    
    prompt = f"""
다음 두 게임 화면 설명이 같은 화면을 나타내는지 판단해주세요:

예상 화면:
{expected}

실제 화면:
{actual}

같은 화면이면 "YES", 다르면 "NO"로만 답변해주세요.
"""
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 10,
        "messages": [{
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        }]
    })
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=body
    )
    
    result = json.loads(response['body'].read())
    answer = result['content'][0]['text'].strip().upper()
    
    return "YES" in answer
```

### 2.3 결과 리포트 생성

```python
def generate_test_report(test_name, results):
    """테스트 결과 HTML 리포트 생성"""
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report: {test_name}</title>
    <style>
        body {{ font-family: Arial; margin: 20px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>Test Report: {test_name}</h1>
    <h2>Summary: {passed}/{total} Passed</h2>
    <table>
        <tr>
            <th>Step</th>
            <th>Action</th>
            <th>Status</th>
            <th>Expected</th>
            <th>Actual</th>
        </tr>
"""
    
    for r in results:
        status_class = 'pass' if r['passed'] else 'fail'
        status_text = '✅ PASS' if r['passed'] else '❌ FAIL'
        
        html += f"""
        <tr>
            <td>{r['step']}</td>
            <td>{r['action']}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{r['expected'][:100]}...</td>
            <td>{r['actual'][:100]}...</td>
        </tr>
"""
    
    html += """
    </table>
</body>
</html>
"""
    
    report_path = f"{test_name}_report.html"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 리포트 생성: {report_path}")
    return report_path
```

---

## 전체 워크플로우 통합

### 메인 실행 스크립트

```python
# main_qa_automation.py
import boto3
import pyautogui
import time
import json
from pathlib import Path

class UnrealQAAutomation:
    def __init__(self, game_exe_path, region='ap-northeast-2'):
        self.game_exe = game_exe_path
        self.rekognition = boto3.client('rekognition', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.action_records = []
    
    def learn_mode(self, user_command, test_name):
        """Phase 1: 학습 모드"""
        print(f"\n=== 학습 모드 시작: {test_name} ===\n")
        
        # 1. 자연어 명령을 단계로 분해
        steps = self.parse_user_command(user_command)
        print(f"총 {len(steps)}개 단계로 분해됨")
        
        # 2. 게임 실행
        self.launch_game()
        
        # 3. 각 단계 실행
        for i, step in enumerate(steps):
            print(f"\n--- Step {i+1}: {step['description']} ---")
            
            # 사용자 확인
            user_input = input("이 단계를 진행하시겠습니까? (y/n): ")
            if user_input.lower() != 'y':
                print("단계 건너뜀")
                continue
            
            # 스크린샷 캡처
            screenshot_path = f"step_{i}_before.png"
            pyautogui.screenshot(screenshot_path)
            
            # UI 요소 감지
            elements = self.detect_ui_elements(screenshot_path)
            print(f"감지된 UI 요소: {len(elements)}개")
            
            # 다음 액션 결정
            action = self.decide_next_action(step, elements, screenshot_path)
            print(f"결정된 액션: {action}")
            
            # 액션 실행 및 기록
            record = self.execute_and_record_action(action, elements, i)
            if record:
                self.action_records.append(record)
        
        # 4. 스크립트 생성
        script_path = self.generate_test_script(self.action_records, test_name)
        
        # 5. 검증 데이터 저장
        self.save_verification_data(self.action_records, test_name)
        
        print(f"\n✅ 학습 완료! 생성된 스크립트: {script_path}")
        return script_path
    
    def execute_mode(self, test_name):
        """Phase 2: 실행 모드"""
        print(f"\n=== 실행 모드 시작: {test_name} ===\n")
        
        # 1. 생성된 스크립트 실행
        import subprocess
        result = subprocess.run(['python', f'generated_{test_name}.py'],
                               capture_output=True, text=True)
        print(result.stdout)
        
        # 2. 결과 검증
        results = self.verify_test_execution(test_name)
        
        # 3. 리포트 생성
        report_path = self.generate_test_report(test_name, results)
        
        print(f"\n✅ 실행 완료! 리포트: {report_path}")
        return results
    
    # ... (위에서 정의한 모든 메서드들)

# 사용 예시
if __name__ == "__main__":
    automation = UnrealQAAutomation(
        game_exe_path="C:/Builds/MyGame/Windows/MyGame.exe"
    )
    
    # Phase 1: 학습
    user_command = """
    게임을 실행하고 로그인 버튼을 클릭한 다음,
    아이디 testuser, 비밀번호 testpass로 로그인하고,
    메인 메뉴에서 설정 버튼을 눌러 설정 화면이 나오는지 확인
    """
    
    automation.learn_mode(user_command, test_name="login_test")
    
    # Phase 2: 반복 실행
    automation.execute_mode(test_name="login_test")
```

---

## 실행 단계별 가이드

### 0단계: 환경 확인 및 설정

#### WSL 환경 확인
```bash
# WSL에서 Windows Python 접근 확인
which python.exe
# 출력 예: /mnt/c/Program Files/Python313/python.exe

# Windows Python 버전 확인
"/mnt/c/Program Files/Python313/python.exe" --version
```

#### Windows Python 패키지 설치
```bash
# WSL에서 Windows Python에 패키지 설치
"/mnt/c/Program Files/Python313/python.exe" -m pip install pyautogui pillow

# 또는 Windows PowerShell에서 직접:
# pip install pyautogui pillow
```

#### WSL Python 패키지 설치
```bash
# WSL에서 AWS SDK 설치
pip install boto3

# AWS 자격 증명 설정
aws configure
```

#### 작업 디렉토리 생성
```bash
# WSL에서 실행
mkdir -p /mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots
cd /mnt/c/Users/hcsung/work/q/unreal-qa-automation
```

#### 필수 파일 생성
```bash
# windows_executor.py 생성 (위 코드 참조)
# wsl_orchestrator.py 생성 (위 코드 참조)
```

### 1단계: 학습 모드 실행

```bash
# WSL에서 실행
cd /mnt/c/Users/hcsung/work/q/unreal-qa-automation
python wsl_orchestrator.py --mode learn --test-name login_test
```

**진행 과정:**
1. **WSL**: 자연어 명령 입력 받음
2. **WSL**: Bedrock Claude로 단계 분해
3. **WSL → Windows**: 게임 실행 명령 전달
4. **Windows**: 게임 실행
5. **각 단계마다:**
   - **WSL**: 사용자 확인 요청
   - **WSL → Windows**: 스크린샷 캡처 명령
   - **Windows**: 스크린샷 저장
   - **WSL**: Rekognition으로 UI 분석
   - **WSL**: Bedrock으로 액션 결정
   - **WSL → Windows**: 클릭 명령 전달
   - **Windows**: 클릭 실행
6. **WSL**: 스크립트 자동 생성

**생성되는 파일:**
- `generated_login_test.py` - 실행 스크립트 (Windows용)
- `login_test_verification.json` - 검증 데이터
- `screenshots/step_*_before.png`, `step_*_after.png` - 참조 스크린샷

### 2단계: 실행 모드 (반복 테스트)

```bash
# WSL에서 실행
python wsl_orchestrator.py --mode execute --test-name login_test
```

**진행 과정:**
1. **WSL**: 생성된 스크립트 읽기
2. **WSL → Windows**: 각 단계 명령 전달
3. **Windows**: 게임 제어 및 스크린샷 캡처
4. **WSL**: Rekognition + Bedrock으로 검증
5. **WSL**: HTML 리포트 생성

**생성되는 파일:**
- `screenshots/verify_step_*.png` - 실행 중 캡처
- `login_test_report.html` - 결과 리포트

### 3단계: 빠른 테스트 (간소화 버전)

```bash
# WSL에서 간단한 테스트
python quick_test.py
```

**quick_test.py:**
```python
#!/usr/bin/env python3
from wsl_orchestrator import WSLOrchestrator

orchestrator = WSLOrchestrator()

# 1. 게임 실행
print("1. 게임 실행...")
orchestrator.launch_game("C:/Builds/MyGame/Windows/MyGame.exe")

# 2. 초기 화면 캡처
print("2. 초기 화면 캡처...")
orchestrator.capture_screenshot("/mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots/test.png")

# 3. UI 분석
print("3. UI 분석...")
elements = orchestrator.analyze_with_rekognition(
    "/mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots/test.png"
)

for elem in elements:
    print(f"  - {elem['text']} (신뢰도: {elem['confidence']:.1f}%)")

# 4. 화면 중앙 클릭
print("4. 화면 중앙 클릭...")
orchestrator.click_and_capture(960, 540, step_num=1)

print("✅ 테스트 완료!")
```

### 4단계: CI/CD 통합 (GitHub Actions)

```yaml
# .github/workflows/game-qa.yml
name: Game QA Automation

on:
  push:
    branches: [main]

jobs:
  qa-test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install Windows dependencies
        run: pip install pyautogui pillow
      
      - name: Setup WSL
        uses: Vampire/setup-wsl@v1
      
      - name: Install WSL dependencies
        shell: wsl-bash {0}
        run: |
          pip install boto3
          aws configure set aws_access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws configure set aws_secret_access_key ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws configure set region ap-northeast-2
      
      - name: Run QA Tests
        shell: wsl-bash {0}
        run: |
          cd /mnt/c/Users/runner/work/project
          python wsl_orchestrator.py --mode execute --test-name login_test
      
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: qa-report
          path: '*_report.html'
```

---

## 환경별 경로 변환

### WSL → Windows 경로 변환

```python
def wsl_to_windows_path(wsl_path):
    """WSL 경로를 Windows 경로로 변환"""
    # /mnt/c/Users/... → C:/Users/...
    return wsl_path.replace('/mnt/c/', 'C:/').replace('/mnt/d/', 'D:/')

def windows_to_wsl_path(win_path):
    """Windows 경로를 WSL 경로로 변환"""
    # C:/Users/... → /mnt/c/Users/...
    return win_path.replace('C:/', '/mnt/c/').replace('D:/', '/mnt/d/')
```

### 실행 파일 경로 예시

```python
# WSL에서 Windows Python 실행
WINDOWS_PYTHON = "/mnt/c/Program Files/Python313/python.exe"

# 게임 실행 파일 (Windows 경로로 전달)
GAME_EXE = "C:/Builds/MyGame/Windows/MyGame.exe"

# 스크린샷 저장 (WSL 경로, Windows에서 변환)
SCREENSHOT_PATH = "/mnt/c/Users/hcsung/work/q/unreal-qa-automation/screenshots/test.png"
```

---

## 실행 단계별 가이드 (구버전)

---

## 비용 최적화

### Rekognition 비용
- DetectText: $1.50 per 1,000 images
- 테스트 1회 (10단계): 약 $0.015

### Bedrock 비용
- Claude 3.5 Sonnet:
  - Input: $3 per 1M tokens
  - Output: $15 per 1M tokens
- 이미지 1장: ~1,600 tokens
- 테스트 1회 (10단계): 약 $0.05

**월 1,000회 테스트 시: 약 $65**

### 비용 절감 방법
1. **Phase 1에서만 Bedrock 사용**, Phase 2는 좌표만 사용
2. **이미지 설명을 캐싱**하여 재사용
3. **실패한 단계만 재검증**

---

## WSL-Windows 환경 트러블슈팅

### 문제 1: Windows Python을 찾을 수 없음

**증상:**
```bash
bash: python.exe: command not found
```

**해결:**
```bash
# Windows Python 경로 확인
ls /mnt/c/Program\ Files/Python*/python.exe

# 또는 Python Launcher 사용
ls /mnt/c/Windows/py.exe

# 전체 경로로 실행
"/mnt/c/Program Files/Python313/python.exe" --version
```

### 문제 2: PyAutoGUI가 스크린샷을 캡처하지 못함

**증상:**
```
OSError: screen grab failed
```

**원인:** Windows에서 실행되지 않음

**해결:**
- `windows_executor.py`가 반드시 Windows Python으로 실행되어야 함
- WSL Python이 아닌 `python.exe`로 실행 확인

### 문제 3: 파일 경로 오류

**증상:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'C:/Users/...'
```

**원인:** WSL과 Windows 경로 혼용

**해결:**
```python
# WSL에서 파일 읽기: WSL 경로 사용
with open('/mnt/c/Users/hcsung/work/test.png', 'rb') as f:
    data = f.read()

# Windows Python에 경로 전달: Windows 경로 사용
command = {'path': 'C:/Users/hcsung/work/test.png'}
```

### 문제 4: 권한 오류

**증상:**
```
PermissionError: [Errno 13] Permission denied
```

**해결:**
```bash
# Windows 파일 권한 확인
ls -la /mnt/c/Users/hcsung/work/q/unreal-qa-automation/

# 필요시 권한 변경 (Windows에서)
# icacls "C:\Users\hcsung\work\q\unreal-qa-automation" /grant Users:F
```

### 문제 5: JSON 파일 동기화 지연

**증상:** Windows가 파일을 쓰기 전에 WSL이 읽으려고 시도

**해결:**
```python
# WSL에서 파일 읽기 전 대기
import time
time.sleep(0.5)

# 또는 파일 존재 확인
import os
while not os.path.exists(result_file):
    time.sleep(0.1)
```

### 문제 6: 게임이 실행되지 않음

**증상:** `subprocess.Popen`이 실패

**해결:**
```python
# Windows에서 실행 파일 경로 확인
import os
if not os.path.exists(game_exe):
    print(f"게임 실행 파일을 찾을 수 없음: {game_exe}")

# 절대 경로 사용
game_exe = "C:/Builds/MyGame/Windows/MyGame.exe"

# 작업 디렉토리 지정
subprocess.Popen([game_exe], cwd="C:/Builds/MyGame/Windows/")
```

### 디버깅 팁

#### 1. Windows Python 실행 확인
```bash
# WSL에서
"/mnt/c/Program Files/Python313/python.exe" -c "import pyautogui; print(pyautogui.size())"
# 출력: Size(width=1920, height=1080)
```

#### 2. 스크린샷 테스트
```bash
# WSL에서 Windows Python으로 스크린샷 테스트
"/mnt/c/Program Files/Python313/python.exe" -c "import pyautogui; pyautogui.screenshot('C:/Users/hcsung/test.png')"

# WSL에서 확인
ls -lh /mnt/c/Users/hcsung/test.png
```

#### 3. 경로 변환 테스트
```python
# test_paths.py
wsl_path = "/mnt/c/Users/hcsung/work/test.png"
win_path = wsl_path.replace('/mnt/c/', 'C:/')
print(f"WSL: {wsl_path}")
print(f"Windows: {win_path}")

# 파일 존재 확인
import os
print(f"WSL에서 접근 가능: {os.path.exists(wsl_path)}")
```

#### 4. 로그 파일 활용
```python
# windows_executor.py에 로깅 추가
import logging
logging.basicConfig(
    filename='C:/Users/hcsung/work/q/unreal-qa-automation/windows_executor.log',
    level=logging.DEBUG
)

logging.info(f"명령 수신: {cmd}")
logging.info(f"클릭 실행: ({x}, {y})")
```

---

## 한계 및 해결 방안

### 한계점

1. **동적 UI 위치 변화**
   - 해결: Rekognition으로 매번 재탐지

2. **복잡한 3D 게임 화면**
   - 해결: OCR 대신 Custom Labels 학습

3. **네트워크 지연**
   - 해결: 대기 시간 동적 조정

### 고급 기능 확장

1. **Rekognition Custom Labels**
   - 특정 버튼/아이콘 학습
   - 텍스트 없는 UI 요소 감지

2. **비디오 녹화 및 분석**
   - 전체 테스트 과정 녹화
   - 실패 시 비디오로 디버깅

3. **멀티 해상도 지원**
   - 다양한 해상도에서 테스트
   - 좌표 자동 스케일링

---

## 결론

이 시스템은 **WSL-Windows 하이브리드 아키텍처**를 통해 게임 내부 코드 없이도 완전 자동화된 QA 테스트를 가능하게 합니다.

**핵심 장점:**
- ✅ 자연어로 테스트 정의
- ✅ 좌표 자동 감지 (Rekognition)
- ✅ 스크립트 자동 생성
- ✅ 반복 실행 및 검증
- ✅ 이미지 대신 텍스트 설명으로 용량 절감
- ✅ **WSL에서 Kiro CLI로 제어, Windows에서 게임 실행**

**WSL-Windows 분리의 이점:**
- **WSL**: AWS API 호출, 데이터 분석, 스크립트 생성 (Linux 도구 활용)
- **Windows**: 게임 실행, GUI 제어 (네이티브 환경)
- **공유 파일 시스템**: 간단한 JSON 기반 통신

**실행 환경 요구사항:**
- WSL2 (Ubuntu 20.04 이상 권장)
- Windows 10/11
- Windows Python 3.8+ (PyAutoGUI 지원)
- WSL Python 3.8+ (boto3 지원)
- AWS 계정 (Bedrock, Rekognition 접근 권한)

**다음 단계:**
1. `windows_executor.py` 구현 (Windows에서 실행)
2. `wsl_orchestrator.py` 구현 (WSL에서 실행)
3. 간단한 테스트로 검증 (`quick_test.py`)
4. 전체 학습/실행 모드 구현
5. CI/CD 파이프라인 통합

**예상 개발 시간:**
- 기본 구현: 1-2일
- 테스트 및 디버깅: 1일
- 고급 기능 추가: 1-2일
- **총 3-5일**
