# Phase 1 Manual Test Guide (수동 테스트 가이드)

## 개요

이 문서는 Game QA Automation System의 Phase 1 기능에 대한 수동 테스트 가이드입니다.
Phase 1은 기본적인 기록 및 재실행 기능(MVP)을 포함합니다.

### 테스트 대상 컴포넌트
- ConfigManager (설정 관리)
- GameProcessManager (게임 프로세스 관리)
- InputMonitor & ActionRecorder (입력 모니터링 및 액션 기록)
- ScriptGenerator (스크립트 생성)
- CLIInterface (CLI 인터페이스)
- QAAutomationController (전체 시스템 조율)

### 사전 요구사항
- Python 3.8 이상
- 필수 패키지 설치: `pip install -r requirements.txt`
- Windows 운영체제 (pynput 및 pyautogui 호환)

---

## 테스트 환경 설정

### 1. 프로젝트 설치

```powershell
# 프로젝트 디렉토리로 이동
cd <project_root>

# 가상환경 생성 (권장)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt
```

### 2. 설정 파일 확인

`config.json` 파일이 프로젝트 루트에 존재하는지 확인합니다.
없으면 시스템이 자동으로 기본 설정을 생성합니다.

```json
{
  "aws": {
    "region": "ap-northeast-2",
    "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0"
  },
  "game": {
    "exe_path": "C:/path/to/game.exe",
    "window_title": "Game Window",
    "startup_wait": 5
  },
  "automation": {
    "action_delay": 0.5,
    "screenshot_on_action": true,
    "screenshot_dir": "screenshots"
  },
  "test_cases": {
    "directory": "test_cases"
  }
}
```

---

## 테스트 시나리오

### 시나리오 1: 시스템 시작 및 초기화

**목적**: 시스템이 정상적으로 시작되고 초기화되는지 확인

**테스트 단계**:
1. 터미널에서 `python main.py` 실행
2. 시스템 시작 메시지 확인

**예상 결과**:
```
==================================================
       게임 QA 자동화 시스템
==================================================

사용 가능한 명령어:
  start              - 게임 실행
  record             - 입력 기록 시작 (사용자가 직접 게임 플레이)
  stop               - 입력 기록 중지
  save <name>        - 기록된 액션을 테스트 케이스로 저장
  replay             - 로드된 테스트 케이스 재실행
  help               - 도움말 표시
  quit               - 종료

>
```

**검증 항목**:
- [ ] 시스템이 오류 없이 시작됨
- [ ] 도움말 메시지가 표시됨
- [ ] 명령 프롬프트(>)가 표시됨
- [ ] `screenshots` 디렉토리가 생성됨
- [ ] `test_cases` 디렉토리가 생성됨

**관련 Requirements**: 1.4, 4.1, 10.1

---

### 시나리오 2: 설정 파일 자동 생성

**목적**: 설정 파일이 없을 때 기본 설정이 자동 생성되는지 확인

**테스트 단계**:
1. `config.json` 파일을 백업 후 삭제
2. `python main.py` 실행
3. 생성된 `config.json` 파일 확인

**예상 결과**:
- 시스템이 "설정 파일이 없습니다. 기본 설정을 생성합니다" 메시지 출력
- `config.json` 파일이 기본값으로 생성됨

**검증 항목**:
- [ ] 기본 설정 파일이 생성됨
- [ ] 설정 파일에 aws, game, automation, test_cases 섹션이 포함됨
- [ ] UTF-8 인코딩으로 저장됨

**관련 Requirements**: 1.4

---

### 시나리오 3: 입력 기록 시작/중지

**목적**: 마우스와 키보드 입력이 정상적으로 기록되는지 확인

**테스트 단계**:
1. 시스템 시작 (`python main.py`)
2. `record` 명령 입력
3. 마우스 클릭 3-5회 수행 (화면 여러 위치)
4. 키보드 입력 수행 (예: "test123")
5. 마우스 스크롤 수행
6. `stop` 명령 입력

**예상 결과**:
```
> record
✓ 입력 기록을 시작합니다.
  게임을 플레이하세요. 모든 마우스/키보드 입력이 기록됩니다.
  'stop' 명령으로 기록을 중지하세요.

> stop
✓ 입력 기록을 중지했습니다. N개의 액션이 기록되었습니다.
  'save <이름>' 명령으로 테스트 케이스를 저장하세요.
```

**검증 항목**:
- [ ] `record` 명령 후 기록 시작 메시지 표시
- [ ] 마우스 클릭이 기록됨 (좌표 포함)
- [ ] 키보드 입력이 기록됨
- [ ] 마우스 스크롤이 기록됨
- [ ] `stop` 명령 후 기록된 액션 수가 표시됨
- [ ] 액션 간 0.5초 이상 간격이 있으면 wait 액션이 자동 삽입됨

**관련 Requirements**: 3.1, 3.2, 3.3, 3.4, 3.6, 3.8

---

### 시나리오 4: 테스트 케이스 저장

**목적**: 기록된 액션이 테스트 케이스로 정상 저장되는지 확인

**테스트 단계**:
1. 시나리오 3 수행 (입력 기록)
2. `save my_test` 명령 입력
3. `test_cases` 디렉토리 확인

**예상 결과**:
```
> save my_test
✓ 테스트 케이스 'my_test'이(가) 저장되었습니다.
  스크립트: test_cases/my_test.py
  데이터: test_cases/my_test.json
```

**검증 항목**:
- [ ] `test_cases/my_test.py` 파일 생성됨
- [ ] `test_cases/my_test.json` 파일 생성됨
- [ ] Python 스크립트가 UTF-8 인코딩으로 저장됨
- [ ] JSON 파일에 모든 액션 정보가 포함됨
- [ ] JSON 파일에 timestamp, action_type, x, y, description 필드 포함

**관련 Requirements**: 5.1, 5.2, 5.3, 5.4

---

### 시나리오 5: 생성된 스크립트 구조 확인

**목적**: 생성된 Replay Script의 구조가 올바른지 확인

**테스트 단계**:
1. 시나리오 4에서 생성된 `test_cases/my_test.py` 파일 열기
2. 스크립트 구조 확인

**예상 결과**:
스크립트에 다음 요소가 포함되어야 함:
- UTF-8 인코딩 선언
- pyautogui, time, sys import
- ACTIONS 리스트 (기록된 액션 데이터)
- replay_actions() 함수
- if __name__ == '__main__' 블록

**검증 항목**:
- [ ] 스크립트 상단에 `# -*- coding: utf-8 -*-` 포함
- [ ] 각 액션에 대한 설명 출력 코드 포함
- [ ] click 액션은 `pyautogui.click()` 호출
- [ ] key_press 액션은 `pyautogui.write()` 또는 `pyautogui.press()` 호출
- [ ] wait 액션은 `time.sleep()` 호출
- [ ] 액션 간 지연 시간 적용 코드 포함

**관련 Requirements**: 5.1, 5.2, 5.3, 5.5, 5.6

---

### 시나리오 6: 테스트 케이스 재실행

**목적**: 저장된 테스트 케이스가 정상적으로 재실행되는지 확인

**테스트 단계**:
1. 시나리오 4 완료 후
2. 시스템 재시작 또는 계속 진행
3. 생성된 스크립트 직접 실행: `python test_cases/my_test.py`

**예상 결과**:
```
총 N개의 액션을 재실행합니다...

[1/N] 클릭 (640, 400)
[2/N] 키 입력: t
[3/N] 2.0초 대기
...

✓ 재실행 완료
```

**검증 항목**:
- [ ] 각 액션 실행 전 설명이 출력됨
- [ ] 마우스 클릭이 기록된 좌표에서 실행됨
- [ ] 키보드 입력이 재현됨
- [ ] 대기 시간이 적용됨
- [ ] 재실행 완료 메시지 표시

**관련 Requirements**: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6

---

### 시나리오 7: 스크린샷 자동 캡처

**목적**: screenshot_on_action 설정이 활성화되었을 때 스크린샷이 캡처되는지 확인

**테스트 단계**:
1. `config.json`에서 `automation.screenshot_on_action`을 `true`로 설정
2. 시스템 시작
3. `record` 명령으로 기록 시작
4. 마우스 클릭 2-3회 수행
5. `stop` 명령으로 기록 중지
6. `screenshots` 디렉토리 확인

**예상 결과**:
- `screenshots` 디렉토리에 `action_0000.png`, `action_0001.png` 등의 파일 생성

**검증 항목**:
- [ ] 각 액션마다 스크린샷 파일이 생성됨
- [ ] 스크린샷 파일명이 순차적으로 증가
- [ ] PNG 형식으로 저장됨

**관련 Requirements**: 3.7

---

### 시나리오 8: 도움말 명령

**목적**: help 명령이 정상 동작하는지 확인

**테스트 단계**:
1. 시스템 시작
2. `help` 명령 입력

**예상 결과**:
사용 가능한 모든 명령어와 설명이 표시됨

**검증 항목**:
- [ ] start, record, stop, save, replay, help, quit 명령어 설명 표시

**관련 Requirements**: 4.1

---

### 시나리오 9: 잘못된 명령어 처리

**목적**: 유효하지 않은 명령어 입력 시 적절한 오류 메시지가 표시되는지 확인

**테스트 단계**:
1. 시스템 시작
2. `invalid_command` 입력

**예상 결과**:
```
> invalid_command
❌ 알 수 없는 명령어: invalid_command
'help' 명령어로 사용 가능한 명령어를 확인하세요.
```

**검증 항목**:
- [ ] 오류 메시지가 표시됨
- [ ] 도움말 안내 메시지가 표시됨
- [ ] 시스템이 종료되지 않고 계속 실행됨

**관련 Requirements**: 4.11

---

### 시나리오 10: 시스템 종료

**목적**: quit 명령으로 시스템이 정상 종료되는지 확인

**테스트 단계**:
1. 시스템 시작
2. `quit` 명령 입력

**예상 결과**:
```
> quit
✓ 게임 QA 자동화 시스템을 종료합니다.
```

**검증 항목**:
- [ ] 종료 메시지가 표시됨
- [ ] 프로그램이 정상 종료됨
- [ ] 리소스가 정리됨 (입력 모니터링 중지 등)

**관련 Requirements**: 4.10

---

### 시나리오 11: 게임 실행 (선택적)

**목적**: start 명령으로 게임이 실행되는지 확인

**사전 조건**: 
- `config.json`의 `game.exe_path`에 유효한 실행 파일 경로 설정
- 테스트용으로 메모장(notepad.exe) 사용 가능

**테스트 단계**:
1. `config.json` 수정:
   ```json
   "game": {
     "exe_path": "C:/Windows/System32/notepad.exe",
     "startup_wait": 2
   }
   ```
2. 시스템 시작
3. `start` 명령 입력

**예상 결과**:
```
> start
게임을 시작합니다...
게임 시작 중... 2초 대기
✓ 게임 실행 완료 (PID: XXXXX)
✓ 게임이 성공적으로 시작되었습니다.
```

**검증 항목**:
- [ ] 지정된 프로그램이 실행됨
- [ ] 시작 대기 시간이 적용됨
- [ ] 프로세스 ID가 표시됨

**관련 Requirements**: 1.1, 1.2, 4.2

---

### 시나리오 12: 게임 실행 파일 없음 오류

**목적**: 존재하지 않는 실행 파일 경로 지정 시 적절한 오류 처리 확인

**테스트 단계**:
1. `config.json`의 `game.exe_path`를 존재하지 않는 경로로 설정
2. 시스템 시작
3. `start` 명령 입력

**예상 결과**:
```
> start
게임을 시작합니다...
❌ 오류: 게임 실행 파일을 찾을 수 없습니다: <경로>
config.json에서 game.exe_path 설정을 확인하세요.
```

**검증 항목**:
- [ ] 명확한 오류 메시지가 표시됨
- [ ] 설정 확인 안내가 표시됨
- [ ] 시스템이 종료되지 않고 계속 실행됨

**관련 Requirements**: 9.1

---

## 통합 테스트 시나리오

### 전체 워크플로우 테스트

**목적**: 기록 → 저장 → 재실행의 전체 워크플로우가 정상 동작하는지 확인

**테스트 단계**:
1. 시스템 시작: `python main.py`
2. (선택) 게임 시작: `start`
3. 기록 시작: `record`
4. 다음 액션 수행:
   - 화면 중앙 클릭
   - 2초 대기
   - "Hello" 타이핑
   - 화면 우측 클릭
5. 기록 중지: `stop`
6. 저장: `save workflow_test`
7. 시스템 종료: `quit`
8. 생성된 스크립트 실행: `python test_cases/workflow_test.py`

**예상 결과**:
- 모든 단계가 오류 없이 완료됨
- 재실행 시 기록된 액션이 순서대로 재현됨

**검증 항목**:
- [ ] 전체 워크플로우가 오류 없이 완료됨
- [ ] 기록된 액션 수와 재실행된 액션 수가 일치
- [ ] 재실행 시 마우스 이동과 클릭이 정확히 재현됨

---

## 알려진 제한사항

1. **관리자 권한**: 일부 애플리케이션에서 입력을 캡처하려면 관리자 권한이 필요할 수 있음
2. **다중 모니터**: 다중 모니터 환경에서 좌표가 예상과 다를 수 있음
3. **고DPI 디스플레이**: 고DPI 설정에서 좌표 스케일링 문제가 발생할 수 있음
4. **특수 키**: 일부 특수 키 조합은 캡처되지 않을 수 있음

---

## 문제 해결

### 입력이 캡처되지 않는 경우
1. 관리자 권한으로 실행 시도
2. 안티바이러스 소프트웨어가 pynput을 차단하는지 확인

### 재실행 시 클릭 위치가 다른 경우
1. 화면 해상도가 기록 시와 동일한지 확인
2. DPI 스케일링 설정 확인

### 스크립트 실행 오류
1. pyautogui 패키지가 설치되어 있는지 확인
2. Python 경로가 올바른지 확인

---

## 테스트 결과 기록

| 시나리오 | 테스트 일자 | 결과 | 비고 |
|---------|-----------|------|------|
| 1. 시스템 시작 | | ☐ Pass / ☐ Fail | |
| 2. 설정 파일 자동 생성 | | ☐ Pass / ☐ Fail | |
| 3. 입력 기록 시작/중지 | | ☐ Pass / ☐ Fail | |
| 4. 테스트 케이스 저장 | | ☐ Pass / ☐ Fail | |
| 5. 스크립트 구조 확인 | | ☐ Pass / ☐ Fail | |
| 6. 테스트 케이스 재실행 | | ☐ Pass / ☐ Fail | |
| 7. 스크린샷 자동 캡처 | | ☐ Pass / ☐ Fail | |
| 8. 도움말 명령 | | ☐ Pass / ☐ Fail | |
| 9. 잘못된 명령어 처리 | | ☐ Pass / ☐ Fail | |
| 10. 시스템 종료 | | ☐ Pass / ☐ Fail | |
| 11. 게임 실행 | | ☐ Pass / ☐ Fail | |
| 12. 게임 실행 오류 처리 | | ☐ Pass / ☐ Fail | |
| 전체 워크플로우 | | ☐ Pass / ☐ Fail | |

---

## 참조

- Requirements Document: `.kiro/specs/game-qa-automation/requirements.md`
- Design Document: `.kiro/specs/game-qa-automation/design.md`
- Implementation Plan: `.kiro/specs/game-qa-automation/tasks.md`
