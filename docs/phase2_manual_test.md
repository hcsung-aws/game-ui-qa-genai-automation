# Phase 2 Manual Test Guide (수동 테스트 가이드)

## 개요

이 문서는 Game QA Automation System의 Phase 2 기능에 대한 수동 테스트 가이드입니다.
Phase 2는 Vision LLM 기반 UI 분석 및 의미론적 액션 기록 기능을 포함합니다.

### 테스트 대상 컴포넌트
- UIAnalyzer (Vision LLM 기반 UI 분석)
- SemanticActionRecorder (의미론적 액션 기록)

### 사전 요구사항
- Phase 1 테스트 완료
- Python 3.8 이상
- 필수 패키지 설치: `pip install -r requirements.txt`
- AWS 자격 증명 설정 (Bedrock 접근용)
- Windows 운영체제

---

## 테스트 환경 설정

### 1. AWS 자격 증명 확인

```powershell
# AWS CLI 설치 확인
aws --version

# 자격 증명 확인
aws sts get-caller-identity

# Bedrock 접근 권한 확인 (ap-northeast-2 리전)
aws bedrock list-foundation-models --region ap-northeast-2 --query "modelSummaries[?contains(modelId, 'claude')]"
```

### 2. 설정 파일 확인

`config.json`에서 AWS 설정이 올바른지 확인합니다:

```json
{
  "aws": {
    "region": "ap-northeast-2",
    "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
    "max_tokens": 2000,
    "retry_count": 3,
    "retry_delay": 1.0
  }
}
```

### 3. PaddleOCR 설치 확인 (OCR 폴백용)

```powershell
# PaddleOCR 설치 확인
python -c "from paddleocr import PaddleOCR; print('PaddleOCR 설치됨')"
```

---

## 테스트 시나리오

### 시나리오 1: 스크린샷 캡처 기능

**목적**: UIAnalyzer가 현재 화면을 정상적으로 캡처하는지 확인

**테스트 단계**:
1. Python 인터프리터 실행
2. 다음 코드 실행:

```python
from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer

config = ConfigManager()
config.load_config()
analyzer = UIAnalyzer(config)

# 스크린샷 캡처
image = analyzer.capture_screenshot("screenshots/test_capture.png")
print(f"이미지 크기: {image.size}")
print(f"이미지 모드: {image.mode}")
```

**예상 결과**:
- `screenshots/test_capture.png` 파일이 생성됨
- 이미지 크기가 현재 화면 해상도와 일치
- PNG 형식으로 저장됨

**검증 항목**:
- [ ] 스크린샷 파일이 생성됨
- [ ] 이미지 크기가 올바름
- [ ] 이미지가 현재 화면을 정확히 캡처함

**관련 Requirements**: 2.1

---

### 시나리오 2: 이미지 Base64 인코딩/디코딩

**목적**: 이미지의 base64 인코딩 및 디코딩이 정상 동작하는지 확인

**테스트 단계**:
1. Python 인터프리터에서 다음 코드 실행:

```python
from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer
from PIL import Image

config = ConfigManager()
config.load_config()
analyzer = UIAnalyzer(config)

# 스크린샷 캡처
original = analyzer.capture_screenshot()

# Base64 인코딩
encoded = analyzer.encode_image_to_base64(original)
print(f"인코딩된 문자열 길이: {len(encoded)}")

# Base64 디코딩
decoded = analyzer.decode_base64_to_image(encoded)
print(f"디코딩된 이미지 크기: {decoded.size}")

# 원본과 비교
print(f"크기 일치: {original.size == decoded.size}")
print(f"모드 일치: {original.mode == decoded.mode}")
```

**예상 결과**:
- 인코딩된 문자열이 생성됨
- 디코딩된 이미지가 원본과 동일한 크기/모드를 가짐

**검증 항목**:
- [ ] Base64 인코딩이 성공함
- [ ] 디코딩된 이미지 크기가 원본과 일치
- [ ] 디코딩된 이미지 모드가 원본과 일치

**관련 Requirements**: 2.2

---

### 시나리오 3: Vision LLM UI 분석

**목적**: AWS Bedrock Claude를 통한 UI 분석이 정상 동작하는지 확인

**사전 조건**:
- AWS 자격 증명이 설정되어 있어야 함
- Bedrock Claude 모델 접근 권한이 있어야 함

**테스트 단계**:
1. 테스트할 게임 또는 애플리케이션 화면을 준비
2. Python 인터프리터에서 다음 코드 실행:

```python
from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer

config = ConfigManager()
config.load_config()
analyzer = UIAnalyzer(config)

# 스크린샷 캡처
image = analyzer.capture_screenshot()

# Vision LLM으로 분석
try:
    result = analyzer.analyze_with_vision_llm(image)
    print("=== UI 분석 결과 ===")
    print(f"버튼: {len(result.get('buttons', []))}개")
    print(f"아이콘: {len(result.get('icons', []))}개")
    print(f"텍스트 필드: {len(result.get('text_fields', []))}개")
    
    # 상세 정보 출력
    for btn in result.get('buttons', []):
        print(f"  버튼: {btn.get('text')} at ({btn.get('x')}, {btn.get('y')})")
except Exception as e:
    print(f"분석 실패: {e}")
```

**예상 결과**:
- UI 요소 정보가 JSON 형식으로 반환됨
- buttons, icons, text_fields 키가 포함됨
- 각 요소에 x, y 좌표가 포함됨

**검증 항목**:
- [ ] Vision LLM API 호출이 성공함
- [ ] 응답에 buttons, icons, text_fields 키가 포함됨
- [ ] 각 UI 요소에 좌표 정보(x, y)가 포함됨
- [ ] 버튼에 text 정보가 포함됨

**관련 Requirements**: 2.3, 2.4, 2.7

---

### 시나리오 4: Vision LLM 재시도 로직 (지수 백오프)

**목적**: Vision LLM 요청 실패 시 지수 백오프 재시도가 정상 동작하는지 확인

**테스트 단계**:
1. 로깅을 활성화하여 재시도 동작 확인:

```python
import logging
logging.basicConfig(level=logging.INFO)

from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer

config = ConfigManager()
config.load_config()
analyzer = UIAnalyzer(config)

# 스크린샷 캡처
image = analyzer.capture_screenshot()

# 재시도 로직이 포함된 분석 실행
result = analyzer.analyze_with_retry(image, retry_count=3)
print(f"분석 소스: {result.get('source', 'unknown')}")
```

**예상 결과**:
- 성공 시: `source: vision_llm`
- 실패 후 OCR 폴백 시: `source: ocr_fallback`
- 로그에서 재시도 간격 확인 (1초, 2초, 4초...)

**검증 항목**:
- [ ] 첫 번째 시도 실패 시 재시도가 수행됨
- [ ] 재시도 간격이 지수적으로 증가함 (1초 → 2초 → 4초)
- [ ] 최대 3회까지만 재시도함
- [ ] 모든 재시도 실패 시 OCR 폴백이 시도됨

**관련 Requirements**: 2.5

---

### 시나리오 5: OCR 폴백 기능

**목적**: Vision LLM 실패 시 PaddleOCR 폴백이 정상 동작하는지 확인

**테스트 단계**:
1. Python 인터프리터에서 다음 코드 실행:

```python
from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer

config = ConfigManager()
config.load_config()
analyzer = UIAnalyzer(config)

# 스크린샷 캡처
image = analyzer.capture_screenshot()

# OCR 직접 테스트
ocr_results = analyzer.analyze_with_ocr(image)
print(f"OCR 결과: {len(ocr_results)}개 텍스트 추출")

for item in ocr_results[:5]:  # 처음 5개만 출력
    print(f"  텍스트: {item['text']}, 좌표: ({item['x']}, {item['y']}), 신뢰도: {item['confidence']:.2f}")
```

**예상 결과**:
- 화면의 텍스트가 추출됨
- 각 텍스트에 좌표와 신뢰도 정보가 포함됨

**검증 항목**:
- [ ] PaddleOCR이 정상 초기화됨
- [ ] 텍스트가 추출됨
- [ ] 각 결과에 text, x, y, confidence, bbox 필드가 포함됨

**관련 Requirements**: 2.6

---

### 시나리오 6: 통합 UI 분석 (analyze 메서드)

**목적**: 전체 UI 분석 파이프라인이 정상 동작하는지 확인

**테스트 단계**:
1. Python 인터프리터에서 다음 코드 실행:

```python
import logging
logging.basicConfig(level=logging.INFO)

from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer

config = ConfigManager()
config.load_config()
analyzer = UIAnalyzer(config)

# 통합 분석 실행 (스크린샷 저장 포함)
result = analyzer.analyze(save_screenshot=True)

print("=== 통합 UI 분석 결과 ===")
print(f"소스: {result.get('source', 'unknown')}")
print(f"버튼: {len(result.get('buttons', []))}개")
print(f"아이콘: {len(result.get('icons', []))}개")
print(f"텍스트 필드: {len(result.get('text_fields', []))}개")

if 'error' in result:
    print(f"오류: {result['error']}")
```

**예상 결과**:
- 스크린샷이 `screenshots/analysis_*.png`로 저장됨
- UI 분석 결과가 반환됨
- source 필드에 분석 방법이 표시됨

**검증 항목**:
- [ ] 스크린샷이 저장됨
- [ ] UI 분석 결과가 반환됨
- [ ] source 필드가 'vision_llm' 또는 'ocr_fallback'임
- [ ] 오류 발생 시 error 필드에 메시지가 포함됨

**관련 Requirements**: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7

---

### 시나리오 7: 의미론적 액션 기록 - 클릭 이벤트

**목적**: SemanticActionRecorder가 클릭 이벤트를 의미론적 정보와 함께 기록하는지 확인

**테스트 단계**:
1. Python 인터프리터에서 다음 코드 실행:

```python
import logging
logging.basicConfig(level=logging.INFO)

from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer
from src.semantic_action_recorder import SemanticActionRecorder
from src.input_monitor import Action
from datetime import datetime

config = ConfigManager()
config.load_config()
ui_analyzer = UIAnalyzer(config)
recorder = SemanticActionRecorder(config, ui_analyzer)

# 테스트용 클릭 액션 생성
click_action = Action(
    timestamp=datetime.now().isoformat(),
    action_type='click',
    x=500,
    y=300,
    description='테스트 클릭 (500, 300)',
    button='left'
)

# 의미론적 액션 기록 (UI 분석 비활성화로 빠른 테스트)
semantic_action = recorder.record_semantic_action(click_action, capture_screenshots=True, analyze_ui=False)

print("=== 의미론적 액션 정보 ===")
print(f"타입: {semantic_action.action_type}")
print(f"좌표: ({semantic_action.x}, {semantic_action.y})")
print(f"스크린샷 후: {semantic_action.screenshot_after_path}")
print(f"해시 후: {semantic_action.ui_state_hash_after}")
```

**예상 결과**:
- 클릭 후 스크린샷이 캡처됨
- 이미지 해시가 계산됨
- SemanticAction 객체가 생성됨

**검증 항목**:
- [ ] 스크린샷 파일이 생성됨
- [ ] ui_state_hash_after가 계산됨
- [ ] semantic_actions 리스트에 액션이 추가됨

**관련 Requirements**: 11.1, 11.6

---

### 시나리오 8: 의미론적 액션 기록 - UI 요소 분석

**목적**: 클릭한 UI 요소의 의미론적 정보가 분석되는지 확인

**테스트 단계**:
1. 버튼이 있는 화면을 준비 (예: 메모장의 메뉴)
2. Python 인터프리터에서 다음 코드 실행:

```python
import logging
logging.basicConfig(level=logging.INFO)

from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer
from src.semantic_action_recorder import SemanticActionRecorder
from src.input_monitor import Action
from datetime import datetime

config = ConfigManager()
config.load_config()
ui_analyzer = UIAnalyzer(config)
recorder = SemanticActionRecorder(config, ui_analyzer)

# 화면의 특정 위치 클릭 (버튼이 있는 위치로 조정)
click_action = Action(
    timestamp=datetime.now().isoformat(),
    action_type='click',
    x=100,  # 실제 버튼 위치로 조정
    y=50,   # 실제 버튼 위치로 조정
    description='버튼 클릭',
    button='left'
)

# 의미론적 액션 기록 (UI 분석 활성화)
semantic_action = recorder.record_semantic_action(click_action, capture_screenshots=True, analyze_ui=True)

print("=== 의미론적 정보 ===")
print(f"의도: {semantic_action.semantic_info.get('intent', 'unknown')}")
print(f"타겟 요소: {semantic_action.semantic_info.get('target_element', {})}")
print(f"컨텍스트: {semantic_action.semantic_info.get('context', {})}")
```

**예상 결과**:
- 클릭한 위치의 UI 요소가 분석됨
- 의도(intent)가 추론됨
- 타겟 요소 정보가 저장됨

**검증 항목**:
- [ ] semantic_info에 intent 필드가 포함됨
- [ ] semantic_info에 target_element 필드가 포함됨
- [ ] target_element에 type, text, description이 포함됨

**관련 Requirements**: 11.2, 11.3

---

### 시나리오 9: 화면 전환 분석

**목적**: 클릭 전후 화면 전환이 분석되는지 확인

**테스트 단계**:
1. 클릭 시 화면이 변경되는 UI 준비 (예: 대화상자 열기)
2. Python 인터프리터에서 다음 코드 실행:

```python
import logging
logging.basicConfig(level=logging.INFO)

from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer
from src.semantic_action_recorder import SemanticActionRecorder

config = ConfigManager()
config.load_config()
ui_analyzer = UIAnalyzer(config)
recorder = SemanticActionRecorder(config, ui_analyzer)

# 클릭 전후 스크린샷을 캡처하는 메서드 사용
# 실제 클릭은 수동으로 수행해야 함
print("3초 후 현재 마우스 위치에서 클릭 전후 분석을 시작합니다...")
print("클릭 시 화면이 변경되는 버튼 위에 마우스를 올려두세요.")

import time
time.sleep(3)

import pyautogui
x, y = pyautogui.position()
print(f"분석 위치: ({x}, {y})")

# 클릭 전후 분석
semantic_action = recorder.record_click_with_before_after(x, y, analyze_ui=False)

print("=== 화면 전환 분석 결과 ===")
print(f"전환 타입: {semantic_action.screen_transition.get('transition_type', 'unknown')}")
print(f"해시 차이: {semantic_action.screen_transition.get('hash_difference', 0)}")
print(f"전 스크린샷: {semantic_action.screenshot_before_path}")
print(f"후 스크린샷: {semantic_action.screenshot_after_path}")
```

**예상 결과**:
- 클릭 전후 스크린샷이 캡처됨
- 화면 전환 타입이 분석됨 (none, minor_change, partial_change, full_transition)
- 해시 차이가 계산됨

**검증 항목**:
- [ ] screenshot_before_path가 설정됨
- [ ] screenshot_after_path가 설정됨
- [ ] screen_transition에 transition_type이 포함됨
- [ ] screen_transition에 hash_difference가 포함됨

**관련 Requirements**: 11.4

---

### 시나리오 10: 키보드 입력 의미론적 기록

**목적**: 키보드 입력이 의미론적 정보와 함께 기록되는지 확인

**테스트 단계**:
1. Python 인터프리터에서 다음 코드 실행:

```python
from src.config_manager import ConfigManager
from src.semantic_action_recorder import SemanticActionRecorder
from src.input_monitor import Action
from datetime import datetime

config = ConfigManager()
config.load_config()
recorder = SemanticActionRecorder(config)

# 키보드 입력 액션 생성
key_action = Action(
    timestamp=datetime.now().isoformat(),
    action_type='key_press',
    x=0,
    y=0,
    description='키 입력: a',
    key='a'
)

# 의미론적 액션 기록
semantic_action = recorder.record_semantic_action(key_action, capture_screenshots=False, analyze_ui=False)

print("=== 키보드 입력 의미론적 정보 ===")
print(f"의도: {semantic_action.semantic_info.get('intent', 'unknown')}")
print(f"타겟 요소 타입: {semantic_action.semantic_info.get('target_element', {}).get('type', 'unknown')}")
print(f"입력 키: {semantic_action.key}")
```

**예상 결과**:
- intent가 'text_input'으로 설정됨
- target_element.type이 'input_field'로 설정됨

**검증 항목**:
- [ ] semantic_info.intent가 'text_input'임
- [ ] semantic_info.target_element.type이 'input_field'임
- [ ] key 필드에 입력된 키가 저장됨

**관련 Requirements**: 11.5

---

### 시나리오 11: 스크롤 의미론적 기록

**목적**: 스크롤 이벤트가 의미론적 정보와 함께 기록되는지 확인

**테스트 단계**:
1. Python 인터프리터에서 다음 코드 실행:

```python
from src.config_manager import ConfigManager
from src.semantic_action_recorder import SemanticActionRecorder
from src.input_monitor import Action
from datetime import datetime

config = ConfigManager()
config.load_config()
recorder = SemanticActionRecorder(config)

# 스크롤 액션 생성
scroll_action = Action(
    timestamp=datetime.now().isoformat(),
    action_type='scroll',
    x=500,
    y=300,
    description='스크롤 (0, -3)',
    scroll_dx=0,
    scroll_dy=-3  # 아래로 스크롤
)

# 의미론적 액션 기록
semantic_action = recorder.record_semantic_action(scroll_action, capture_screenshots=False, analyze_ui=False)

print("=== 스크롤 의미론적 정보 ===")
print(f"의도: {semantic_action.semantic_info.get('intent', 'unknown')}")
print(f"타겟 요소 타입: {semantic_action.semantic_info.get('target_element', {}).get('type', 'unknown')}")
print(f"설명: {semantic_action.semantic_info.get('target_element', {}).get('description', '')}")
```

**예상 결과**:
- intent가 'scroll_content'로 설정됨
- target_element.type이 'scrollable_area'로 설정됨
- 스크롤 방향이 설명에 포함됨

**검증 항목**:
- [ ] semantic_info.intent가 'scroll_content'임
- [ ] semantic_info.target_element.type이 'scrollable_area'임
- [ ] 스크롤 방향(up/down)이 description에 포함됨

**관련 Requirements**: 11.5

---

### 시나리오 12: 의미론적 액션 직렬화/역직렬화

**목적**: 의미론적 액션이 JSON으로 직렬화 및 역직렬화되는지 확인

**테스트 단계**:
1. Python 인터프리터에서 다음 코드 실행:

```python
import json
from src.config_manager import ConfigManager
from src.semantic_action_recorder import SemanticActionRecorder
from src.input_monitor import Action
from datetime import datetime

config = ConfigManager()
config.load_config()
recorder = SemanticActionRecorder(config)

# 여러 액션 기록
actions = [
    Action(timestamp=datetime.now().isoformat(), action_type='click', x=100, y=100, description='클릭1', button='left'),
    Action(timestamp=datetime.now().isoformat(), action_type='key_press', x=0, y=0, description='키입력', key='a'),
    Action(timestamp=datetime.now().isoformat(), action_type='scroll', x=200, y=200, description='스크롤', scroll_dx=0, scroll_dy=-1),
]

for action in actions:
    recorder.record_semantic_action(action, capture_screenshots=False, analyze_ui=False)

# 딕셔너리 리스트로 변환
dict_list = recorder.to_dict_list()
print(f"직렬화된 액션 수: {len(dict_list)}")

# JSON 문자열로 변환
json_str = json.dumps(dict_list, ensure_ascii=False, indent=2)
print(f"JSON 길이: {len(json_str)} 문자")

# 역직렬화
restored_data = json.loads(json_str)
restored_recorder = SemanticActionRecorder.from_dict_list(restored_data, config)
print(f"복원된 액션 수: {len(restored_recorder.get_semantic_actions())}")

# 원본과 비교
original_actions = recorder.get_semantic_actions()
restored_actions = restored_recorder.get_semantic_actions()

for i, (orig, rest) in enumerate(zip(original_actions, restored_actions)):
    match = (orig.action_type == rest.action_type and 
             orig.x == rest.x and orig.y == rest.y)
    print(f"액션 {i+1}: {'일치' if match else '불일치'}")
```

**예상 결과**:
- 모든 액션이 JSON으로 직렬화됨
- 역직렬화 후 원본과 동일한 데이터가 복원됨

**검증 항목**:
- [ ] to_dict_list()가 딕셔너리 리스트를 반환함
- [ ] JSON 직렬화가 성공함
- [ ] from_dict_list()로 복원이 성공함
- [ ] 복원된 액션이 원본과 일치함

**관련 Requirements**: 11.6

---

## 통합 테스트 시나리오

### 전체 Phase 2 워크플로우 테스트

**목적**: UI 분석과 의미론적 액션 기록의 전체 워크플로우가 정상 동작하는지 확인

**테스트 단계**:
1. 테스트할 애플리케이션 실행 (예: 메모장)
2. Python 인터프리터에서 다음 코드 실행:

```python
import logging
import json
logging.basicConfig(level=logging.INFO)

from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer
from src.semantic_action_recorder import SemanticActionRecorder

config = ConfigManager()
config.load_config()
ui_analyzer = UIAnalyzer(config)
recorder = SemanticActionRecorder(config, ui_analyzer)

print("=== Phase 2 통합 테스트 ===")
print()

# 1. UI 분석
print("1. UI 분석 수행...")
ui_result = ui_analyzer.analyze(save_screenshot=True)
print(f"   분석 소스: {ui_result.get('source', 'unknown')}")
print(f"   발견된 요소: 버튼 {len(ui_result.get('buttons', []))}개, "
      f"아이콘 {len(ui_result.get('icons', []))}개, "
      f"텍스트 {len(ui_result.get('text_fields', []))}개")
print()

# 2. 의미론적 클릭 기록 (화면 중앙)
print("2. 의미론적 클릭 기록...")
import pyautogui
screen_width, screen_height = pyautogui.size()
center_x, center_y = screen_width // 2, screen_height // 2

semantic_action = recorder.record_click_with_before_after(center_x, center_y, analyze_ui=True)
print(f"   클릭 위치: ({center_x}, {center_y})")
print(f"   의도: {semantic_action.semantic_info.get('intent', 'unknown')}")
print(f"   화면 전환: {semantic_action.screen_transition.get('transition_type', 'none')}")
print()

# 3. 결과 저장
print("3. 결과 저장...")
result_data = {
    "ui_analysis": ui_result,
    "semantic_actions": recorder.to_dict_list()
}

with open("test_cases/phase2_test_result.json", "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)
print("   저장 완료: test_cases/phase2_test_result.json")
print()

print("=== 테스트 완료 ===")
```

**예상 결과**:
- UI 분석이 성공적으로 수행됨
- 의미론적 클릭이 기록됨
- 결과가 JSON 파일로 저장됨

**검증 항목**:
- [ ] UI 분석 결과가 반환됨
- [ ] 의미론적 액션이 기록됨
- [ ] 화면 전환 정보가 분석됨
- [ ] JSON 파일이 생성됨
- [ ] JSON 파일에 ui_analysis와 semantic_actions가 포함됨

---

## 알려진 제한사항

1. **AWS 자격 증명**: Bedrock 접근을 위해 유효한 AWS 자격 증명이 필요함
2. **모델 접근 권한**: Claude Sonnet 4.5 모델에 대한 접근 권한이 필요함
3. **PaddleOCR 초기화**: 첫 OCR 호출 시 모델 다운로드로 인해 시간이 걸릴 수 있음
4. **한국어 OCR**: PaddleOCR의 한국어 인식 정확도는 영어보다 낮을 수 있음
5. **Vision LLM 비용**: AWS Bedrock API 호출에 비용이 발생함
6. **화면 전환 분석**: 이미지 해시 기반 분석은 미세한 변화를 감지하지 못할 수 있음

---

## 문제 해결

### AWS 자격 증명 오류

```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**해결 방법**:
1. AWS CLI 설정 확인: `aws configure`
2. 환경 변수 설정:
   ```powershell
   $env:AWS_ACCESS_KEY_ID = "your_access_key"
   $env:AWS_SECRET_ACCESS_KEY = "your_secret_key"
   $env:AWS_DEFAULT_REGION = "ap-northeast-2"
   ```

### Bedrock 모델 접근 오류

```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException)
```

**해결 방법**:
1. AWS 콘솔에서 Bedrock 모델 접근 권한 요청
2. IAM 정책에 `bedrock:InvokeModel` 권한 추가

### PaddleOCR 설치 오류

```
ModuleNotFoundError: No module named 'paddleocr'
```

**해결 방법**:
```powershell
pip install paddleocr paddlepaddle
```

### Vision LLM 응답 파싱 오류

**해결 방법**:
1. 로그에서 원본 응답 확인
2. 프롬프트 수정이 필요할 수 있음
3. OCR 폴백이 자동으로 시도됨

---

## 테스트 결과 기록

| 시나리오 | 테스트 일자 | 결과 | 비고 |
|---------|-----------|------|------|
| 1. 스크린샷 캡처 | | ☐ Pass / ☐ Fail | |
| 2. Base64 인코딩/디코딩 | | ☐ Pass / ☐ Fail | |
| 3. Vision LLM UI 분석 | | ☐ Pass / ☐ Fail | |
| 4. 재시도 로직 (지수 백오프) | | ☐ Pass / ☐ Fail | |
| 5. OCR 폴백 | | ☐ Pass / ☐ Fail | |
| 6. 통합 UI 분석 | | ☐ Pass / ☐ Fail | |
| 7. 의미론적 클릭 기록 | | ☐ Pass / ☐ Fail | |
| 8. UI 요소 분석 | | ☐ Pass / ☐ Fail | |
| 9. 화면 전환 분석 | | ☐ Pass / ☐ Fail | |
| 10. 키보드 입력 기록 | | ☐ Pass / ☐ Fail | |
| 11. 스크롤 기록 | | ☐ Pass / ☐ Fail | |
| 12. 직렬화/역직렬화 | | ☐ Pass / ☐ Fail | |
| 전체 워크플로우 | | ☐ Pass / ☐ Fail | |

---

## 참조

- Requirements Document: `.kiro/specs/game-qa-automation/requirements.md`
- Design Document: `.kiro/specs/game-qa-automation/design.md`
- Implementation Plan: `.kiro/specs/game-qa-automation/tasks.md`
- Phase 1 Manual Test Guide: `docs/phase1_manual_test.md`
