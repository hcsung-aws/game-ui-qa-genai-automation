# 🎮 Game QA Automation Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

AWS Bedrock Claude를 활용한 Vision 기반 게임 UI 분석 및 자동화 테스트 프레임워크

[English](#english) | 한국어

---

## 📋 개요

본 시스템은 게임 QA 자동화를 위한 프레임워크로, **사용자의 실제 플레이를 기록**하고 **Vision LLM을 통해 의미론적으로 재실행**하는 것이 핵심입니다.

### 주요 특징

- **🎯 실시간 입력 모니터링**: pynput을 사용하여 마우스/키보드 입력을 자동 캡처
- **🤖 Vision LLM 기반 UI 분석**: AWS Bedrock Claude를 통한 게임 화면 분석
- **🔄 의미론적 매칭**: UI 레이아웃이 변경되어도 동일한 의미의 요소를 찾아 클릭
- **📊 정확도 추적**: 테스트 실행 결과 추적 및 통계 분석
- **📝 테스트 케이스 자동 생성**: 기록된 액션을 재사용 가능한 테스트 케이스로 저장

### 작동 방식

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

This is a game QA automation framework that **records actual user gameplay** and **semantically replays it using Vision LLM**.

### Key Features

- **🎯 Real-time Input Monitoring**: Automatically captures mouse/keyboard inputs using pynput
- **🤖 Vision LLM-based UI Analysis**: Game screen analysis through AWS Bedrock Claude
- **🔄 Semantic Matching**: Finds and clicks elements with the same meaning even when UI layout changes
- **📊 Accuracy Tracking**: Test execution result tracking and statistical analysis
- **📝 Auto Test Case Generation**: Saves recorded actions as reusable test cases

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
