# 🎮 Game QA Automation Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

AWS Bedrock Claude를 활용한 Vision 기반 게임 UI 분석 및 자동화 테스트 프레임워크

[English](#english) | 한국어

---

## 📋 개요

본 시스템은 게임 QA 자동화를 위한 프레임워크로, **사용자의 실제 플레이를 기록**하고 **재실행**하는 것이 핵심입니다.

### 주요 특징

- **🎯 실시간 입력 모니터링**: pynput을 사용하여 마우스/키보드 입력을 자동 캡처
- **🤖 Vision LLM 기반 UI 분석**: AWS Bedrock Claude를 통한 게임 화면 분석 (의미론적 테스트)
- **🔄 의미론적 매칭**: UI 레이아웃이 변경되어도 동일한 의미의 요소를 찾아 클릭 (의미론적 테스트)
- **📊 정확도 추적**: 테스트 실행 결과 추적 및 통계 분석
- **📝 테스트 케이스 자동 생성**: 기록된 액션을 재사용 가능한 테스트 케이스로 저장

### 두 가지 테스트 모드

본 프레임워크는 두 가지 테스트 모드를 제공합니다:

| 모드 | 실행 방법 | 특징 |
|------|----------|------|
| **기본 테스트** | `python main.py` | 좌표 기반 녹화/재현, 빠른 실행 |
| **의미론적 테스트** | `python test_semantic_replay_manual.py` | Vision LLM 분석, UI 변경 대응 가능 |

### 작동 방식

**기본 테스트 (좌표 기반)**
```
[사용자 플레이 기록] → [좌표 저장] → [동일 좌표로 재실행]
```

**의미론적 테스트 (Vision LLM 기반)**
```
[사용자 플레이 기록] → [Vision LLM 분석] → [의미론적 테스트 케이스 생성]
                                ↓
[테스트 재실행] ← [UI 요소 의미 매칭] ← [화면 캡처 및 분석]
```

## 🚀 설치

### 1. Python 환경 설정

Python 3.8 이상이 필요합니다.

```bash
# 가상환경 생성 (권장)
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. AWS 자격증명 설정

AWS Bedrock을 사용하기 위해 자격증명을 설정합니다:

```bash
# 환경 변수 설정 (Windows)
set AWS_ACCESS_KEY_ID=your_access_key
set AWS_SECRET_ACCESS_KEY=your_secret_key
set AWS_REGION=ap-northeast-2

# 또는 AWS CLI 프로파일 사용
aws configure
```

### 4. 설정 파일 생성

`config.example.json`을 복사하여 `config.json`을 생성하고, 게임 경로를 수정합니다:

```bash
# Windows
copy config.example.json config.json

# Linux/Mac
cp config.example.json config.json
```

그 후 `config.json`을 열어 게임 실행 파일 경로를 설정합니다:

```json
{
  "game": {
    "exe_path": "C:/path/to/your/game.exe",
    "window_title": "Your Game Window",
    "startup_wait": 10
  }
}
```

> ⚠️ **주의**: `config.json`은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다. 개인 경로 정보 보호를 위함입니다.

## 📁 프로젝트 구조

```
game-qa-automation/
├── src/                      # 소스 코드
│   ├── config_manager.py     # 설정 관리
│   ├── input_monitor.py      # 입력 모니터링
│   ├── vision_llm_analyzer.py # Vision LLM 분석
│   ├── action_replayer.py    # 액션 재실행
│   └── ...
├── tests/                    # 테스트
├── test_cases/               # 저장된 테스트 케이스
├── screenshots/              # 캡처된 스크린샷
├── reports/                  # 테스트 리포트
├── config.json               # 설정 파일
├── requirements.txt          # Python 의존성
└── main.py                   # 메인 진입점
```

## 💻 사용법

### 기본 실행

```bash
python main.py
```

### CLI 명령어

| 명령어 | 설명 |
|--------|------|
| `record` | 새로운 테스트 케이스 기록 시작 |
| `stop` | 기록 중지 |
| `replay <name>` | 저장된 테스트 케이스 재실행 |
| `list` | 저장된 테스트 케이스 목록 |
| `exit` | 프로그램 종료 |

### 테스트 케이스 기록 예시

1. `record` 명령으로 기록 시작
2. 게임에서 원하는 동작 수행 (클릭, 키 입력 등)
3. `stop` 명령으로 기록 종료
4. 테스트 케이스 이름 입력하여 저장

### 테스트 케이스 재실행

```bash
# CLI에서
replay my_test_case

# 또는 직접 실행
python -m src.action_replayer test_cases/my_test_case.json
```

## 🧠 의미론적 테스트 (Semantic Test)

기본 좌표 기반 녹화/재현 외에, **Vision LLM을 활용한 의미론적 테스트** 기능이 별도로 구현되어 있습니다.

### 의미론적 테스트란?

- **녹화 시**: 클릭한 UI 요소를 Vision LLM이 분석하여 "시작 버튼", "설정 아이콘" 등 의미론적 정보를 함께 저장
- **재현 시**: 저장된 의미론적 정보를 기반으로 현재 화면에서 동일한 의미의 UI 요소를 찾아 클릭
- **장점**: UI 레이아웃이 변경되어도 동일한 의미의 요소를 찾아 테스트 가능

### 사용법

`test_semantic_replay_manual.py` 스크립트를 사용합니다:

```bash
# 의미론적 테스트 케이스 녹화 (기본 60초, 최대 시간 지정 가능)
python test_semantic_replay_manual.py record <테스트이름> [녹화시간(초)]

# 예시: 120초 동안 녹화
python test_semantic_replay_manual.py record my_game_test 120

# 의미론적 매칭으로 재현
python test_semantic_replay_manual.py replay <테스트이름>

# JSON 파일 직접 지정도 가능
python test_semantic_replay_manual.py replay test_cases/my_test_semantic.json

# 대기 시간 포함 전체 재현 (기본은 대기 건너뜀)
python test_semantic_replay_manual.py replay my_game_test --full-replay

# 재현 결과 분석
python test_semantic_replay_manual.py compare <테스트이름>
```

### 의미론적 테스트 작동 원리

```
[녹화]
클릭 → 스크린샷 캡처 → Vision LLM 분석 → 의미론적 정보 저장
       (버튼 텍스트, 타입, 위치, 신뢰도 등)

[재현]
현재 화면 캡처 → Vision LLM 분석 → 저장된 의미론적 정보와 매칭
→ 신뢰도 0.7 이상: 매칭된 좌표로 클릭
→ 신뢰도 0.7 미만: 원래 좌표로 폴백
```

### 기본 테스트 vs 의미론적 테스트

| 구분 | 기본 테스트 (main.py) | 의미론적 테스트 |
|------|----------------------|----------------|
| 녹화 방식 | 좌표 기반 | 좌표 + Vision LLM 분석 |
| 재현 방식 | 고정 좌표 클릭 | 의미론적 매칭 후 클릭 |
| UI 변경 대응 | 불가 | 가능 |
| 실행 속도 | 빠름 | LLM 호출로 느림 |
| 사용 시나리오 | 단순 반복 테스트 | UI 변경이 잦은 테스트 |

## 🧪 테스트 실행

```bash
# 모든 테스트 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ -v --cov=src --cov-report=html
```

## ⚙️ 설정 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `aws.region` | AWS 리전 | `ap-northeast-2` |
| `aws.model_id` | Bedrock 모델 ID | Claude Sonnet |
| `automation.action_delay` | 액션 간 딜레이 (초) | `0.5` |
| `automation.capture_delay` | 화면 캡처 대기 시간 (초) | `2.0` |
| `automation.hash_threshold` | 이미지 해시 유사도 임계값 | `10` |

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여

이슈 및 풀 리퀘스트를 환영합니다!

---

<a name="english"></a>
# English

## 📋 Overview

This is a game QA automation framework that **records actual user gameplay** and **replays it**.

### Key Features

- **🎯 Real-time Input Monitoring**: Automatically captures mouse/keyboard inputs using pynput
- **🤖 Vision LLM-based UI Analysis**: Game screen analysis through AWS Bedrock Claude (Semantic Test)
- **🔄 Semantic Matching**: Finds and clicks elements with the same meaning even when UI layout changes (Semantic Test)
- **📊 Accuracy Tracking**: Test execution result tracking and statistical analysis
- **📝 Auto Test Case Generation**: Saves recorded actions as reusable test cases

### Two Test Modes

This framework provides two test modes:

| Mode | Execution | Features |
|------|-----------|----------|
| **Basic Test** | `python main.py` | Coordinate-based recording/replay, fast execution |
| **Semantic Test** | `python test_semantic_replay_manual.py` | Vision LLM analysis, handles UI changes |

## 🚀 Installation

### 1. Python Environment Setup

Python 3.8 or higher is required.

```bash
# Create virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. AWS Credentials Setup

Configure AWS credentials for Bedrock:

```bash
# Environment variables (Windows)
set AWS_ACCESS_KEY_ID=your_access_key
set AWS_SECRET_ACCESS_KEY=your_secret_key
set AWS_REGION=ap-northeast-2

# Or use AWS CLI profile
aws configure
```

### 4. Configuration

Copy `config.example.json` to `config.json` and edit your game path:

```bash
# Windows
copy config.example.json config.json

# Linux/Mac
cp config.example.json config.json
```

Then edit `config.json` to set your game executable path:

```json
{
  "game": {
    "exe_path": "C:/path/to/your/game.exe",
    "window_title": "Your Game Window",
    "startup_wait": 10
  }
}
```

> ⚠️ **Note**: `config.json` is included in `.gitignore` and will not be committed to protect personal path information.

## 💻 Usage

### Basic Execution

```bash
python main.py
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `record` | Start recording a new test case |
| `stop` | Stop recording |
| `replay <name>` | Replay a saved test case |
| `list` | List saved test cases |
| `exit` | Exit the program |

## 🧠 Semantic Testing

In addition to basic coordinate-based recording/replay, **semantic testing using Vision LLM** is implemented separately.

### What is Semantic Testing?

- **During Recording**: Vision LLM analyzes clicked UI elements and stores semantic information like "Start Button", "Settings Icon"
- **During Replay**: Finds UI elements with the same meaning on the current screen based on stored semantic information
- **Advantage**: Can test even when UI layout changes by finding elements with the same meaning

### Usage

Use the `test_semantic_replay_manual.py` script:

```bash
# Record semantic test case (default 60 seconds, can specify max time)
python test_semantic_replay_manual.py record <test_name> [duration_seconds]

# Example: Record for 120 seconds
python test_semantic_replay_manual.py record my_game_test 120

# Replay with semantic matching
python test_semantic_replay_manual.py replay <test_name>

# Can also specify JSON file directly
python test_semantic_replay_manual.py replay test_cases/my_test_semantic.json

# Full replay including wait times (default skips waits)
python test_semantic_replay_manual.py replay my_game_test --full-replay

# Analyze replay results
python test_semantic_replay_manual.py compare <test_name>
```

### How Semantic Testing Works

```
[Recording]
Click → Screenshot Capture → Vision LLM Analysis → Store Semantic Info
        (button text, type, position, confidence, etc.)

[Replay]
Capture Current Screen → Vision LLM Analysis → Match with Stored Semantic Info
→ Confidence ≥ 0.7: Click at matched coordinates
→ Confidence < 0.7: Fallback to original coordinates
```

### Basic Test vs Semantic Test

| Aspect | Basic Test (main.py) | Semantic Test |
|--------|---------------------|---------------|
| Recording | Coordinate-based | Coordinate + Vision LLM |
| Replay | Fixed coordinate click | Semantic matching then click |
| UI Change Handling | Not possible | Possible |
| Execution Speed | Fast | Slower due to LLM calls |
| Use Case | Simple repetitive tests | Tests with frequent UI changes |

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html
```

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Issues and pull requests are welcome!
