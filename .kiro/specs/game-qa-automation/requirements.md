# Requirements Document (요구사항 문서)

## Introduction (개요)

본 시스템은 Unreal 게임의 QA 자동화를 위한 프레임워크로서, AWS Bedrock Claude Sonnet 4.5를 활용한 Vision 기반 UI 분석과 PyAutoGUI를 통한 자동화 액션 실행, 그리고 반복 테스트를 위한 스크립트 생성 기능을 제공한다. 사용자는 대화형 세션을 통해 게임 UI를 분석하고 액션을 기록하며, 이를 재실행 가능한 테스트 케이스로 변환할 수 있다.

## Glossary (용어 정의)

- **QA System**: 게임 품질 보증 자동화 시스템
- **Vision LLM**: AWS Bedrock Claude Sonnet 4.5 모델을 사용한 이미지 분석 서비스
- **UI Analyzer**: Vision LLM을 통해 게임 화면의 UI 요소를 분석하는 컴포넌트
- **Action Recorder**: 사용자의 게임 조작 액션을 기록하는 컴포넌트
- **Replay Script**: 기록된 액션을 재실행하기 위한 Python 스크립트
- **Test Case**: 하나의 완전한 테스트 시나리오를 나타내는 액션 시퀀스
- **Interactive Session**: 사용자가 명령어를 입력하여 게임을 조작하고 분석하는 대화형 모드
- **PyAutoGUI**: Python 기반 GUI 자동화 라이브러리
- **OCR Engine**: PaddleOCR을 사용한 텍스트 인식 엔진 (Vision LLM 보조용)

## Requirements

### Requirement 1 (요구사항 1)

**User Story (사용자 스토리):** QA 엔지니어로서, 게임 실행 파일을 실행하고 자동화 환경을 준비하여, 게임 UI 테스트를 시작할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 사용자가 게임 실행 파일 경로를 제공하면 THEN QA System은 게임 프로세스를 실행해야 한다
2. WHEN 게임 프로세스가 시작되면 THEN QA System은 상호작용을 허용하기 전에 설정된 시작 지연 시간만큼 대기해야 한다
3. WHEN 게임 창이 준비되면 THEN QA System은 창이 활성화되어 접근 가능한지 확인해야 한다
4. WHEN 설정 파일이 없으면 THEN QA System은 기본값으로 채워진 기본 설정을 생성해야 한다
5. WHERE 사용자 정의 설정이 제공되면 THEN QA System은 지정된 JSON 파일에서 설정을 로드해야 한다

### Requirement 2 (요구사항 2)

**User Story (사용자 스토리):** QA 엔지니어로서, Vision LLM을 사용하여 현재 게임 화면을 캡처하고 분석하여, 상호작용 가능한 UI 요소를 식별할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 사용자가 UI 분석을 요청하면 THEN QA System은 현재 화면을 PNG 이미지로 캡처해야 한다
2. WHEN 스크린샷이 캡처되면 THEN UI Analyzer는 이미지를 base64 형식으로 인코딩해야 한다
3. WHEN 인코딩된 이미지가 준비되면 THEN UI Analyzer는 구조화된 프롬프트와 함께 AWS Bedrock Claude Sonnet 4.5로 전송해야 한다
4. WHEN Vision LLM이 응답하면 THEN UI Analyzer는 UI 요소를 포함한 JSON 응답을 파싱해야 한다
5. IF Vision LLM 요청이 실패하면 THEN UI Analyzer는 지수 백오프로 최대 3회까지 재시도해야 한다
6. IF 모든 Vision LLM 재시도가 실패하면 THEN UI Analyzer는 텍스트 추출을 위해 OCR Engine으로 폴백해야 한다
7. WHEN UI 요소가 식별되면 THEN UI Analyzer는 버튼, 아이콘, 텍스트 필드와 그 좌표를 포함한 구조화된 JSON을 반환해야 한다

### Requirement 3 (요구사항 3)

**User Story (사용자 스토리):** QA 엔지니어로서, 실제로 게임을 플레이하면서 모든 입력을 자동으로 기록하여, 자연스러운 테스트 시나리오를 구축할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 사용자가 기록 시작 명령을 내리면 THEN Input Monitor는 pynput을 사용하여 마우스와 키보드 입력 모니터링을 시작해야 한다
2. WHEN 사용자가 마우스를 클릭하면 THEN Input Monitor는 클릭 좌표와 버튼 정보를 자동으로 캡처해야 한다
3. WHEN 사용자가 키보드를 입력하면 THEN Input Monitor는 입력된 키 정보를 자동으로 캡처해야 한다
4. WHEN 사용자가 마우스 스크롤을 하면 THEN Input Monitor는 스크롤 방향과 양을 자동으로 캡처해야 한다
5. WHEN 입력이 캡처되면 THEN Action Recorder는 타임스탬프, 타입, 좌표, 설명과 함께 액션을 기록해야 한다
6. WHEN 액션 간 시간 간격이 0.5초를 초과하면 THEN Action Recorder는 자동으로 대기 액션을 삽입해야 한다
7. WHEN screenshot-on-action 설정이 활성화되면 THEN Action Recorder는 각 액션 후에 스크린샷을 캡처해야 한다
8. WHEN 사용자가 기록 중지 명령을 내리면 THEN Input Monitor는 입력 모니터링을 중지해야 한다

### Requirement 4 (요구사항 4)

**User Story (사용자 스토리):** QA 엔지니어로서, 커맨드라인 인터페이스를 통해 시스템과 상호작용하여, 자동화 흐름을 제어할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN Interactive Session이 시작되면 THEN QA System은 사용 가능한 명령어를 표시하고 사용자 입력을 대기해야 한다
2. WHEN 사용자가 "start" 명령을 입력하면 THEN QA System은 게임 프로세스를 실행해야 한다
3. WHEN 사용자가 "record" 명령을 입력하면 THEN QA System은 입력 모니터링을 시작해야 한다
4. WHEN 사용자가 "stop" 명령을 입력하면 THEN QA System은 입력 모니터링을 중지하고 기록된 액션 수를 표시해야 한다
5. WHEN 사용자가 "analyze" 명령을 입력하면 THEN QA System은 UI 분석을 트리거하고 결과를 표시해야 한다
6. WHEN 사용자가 이름과 함께 "save" 명령을 입력하면 THEN QA System은 기록된 액션으로부터 Replay Script를 생성하고 테스트 케이스로 저장해야 한다
7. WHEN 사용자가 "list" 명령을 입력하면 THEN QA System은 저장된 모든 테스트 케이스 목록을 표시해야 한다
8. WHEN 사용자가 이름과 함께 "load" 명령을 입력하면 THEN QA System은 해당 테스트 케이스를 로드해야 한다
9. WHEN 사용자가 "replay" 명령을 입력하면 THEN QA System은 로드된 테스트 케이스를 재실행해야 한다
10. WHEN 사용자가 "quit" 명령을 입력하면 THEN QA System은 Interactive Session을 종료해야 한다
11. IF 사용자가 유효하지 않은 명령을 입력하면 THEN QA System은 오류 메시지를 표시하고 사용 가능한 명령어를 보여줘야 한다

### Requirement 5 (요구사항 5)

**User Story (사용자 스토리):** QA 엔지니어로서, 기록된 액션을 재사용 가능한 테스트 스크립트로 저장하여, 테스트 시나리오를 자동으로 재실행할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 사용자가 액션 저장을 요청하면 THEN QA System은 모든 기록된 액션을 포함하는 Python 스크립트를 생성해야 한다
2. WHEN Replay Script가 생성되면 THEN QA System은 각 액션에 대해 타임스탬프, 액션 타입, 좌표, 설명을 포함해야 한다
3. WHEN Replay Script가 생성되면 THEN QA System은 액션을 순서대로 실행하는 replay 함수를 포함해야 한다
4. WHEN Replay Script가 저장되면 THEN QA System은 UTF-8 인코딩으로 파일에 작성해야 한다
5. WHEN Replay Script가 대기 액션을 포함하면 THEN QA System은 설명에서 지속 시간을 파싱하여 sleep 호출로 변환해야 한다
6. WHEN Replay Script가 실행되면 THEN 스크립트는 실행 전에 각 액션 설명을 출력해야 한다

### Requirement 6 (요구사항 6)

**User Story (사용자 스토리):** QA 엔지니어로서, 저장된 테스트 스크립트를 반복적으로 실행하여, 회귀 테스트를 수행할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN Replay Script가 실행되면 THEN 스크립트는 모든 기록된 액션을 순서대로 반복해야 한다
2. WHEN 클릭 액션이 재실행되면 THEN 스크립트는 기록된 좌표에서 PyAutoGUI 클릭을 실행해야 한다
3. WHEN 타이핑 액션이 재실행되면 THEN 스크립트는 기록된 텍스트로 PyAutoGUI write를 실행해야 한다
4. WHEN 대기 액션이 재실행되면 THEN 스크립트는 기록된 지속 시간 동안 sleep해야 한다
5. WHEN 각 액션이 재실행되면 THEN 스크립트는 다음 액션으로 진행하기 전에 설정된 액션 지연 시간만큼 대기해야 한다
6. WHEN 재실행이 완료되면 THEN 스크립트는 완료 메시지를 출력해야 한다

### Requirement 7 (요구사항 7)

**User Story (사용자 스토리):** QA 엔지니어로서, 재실행된 액션이 예상된 UI 상태를 생성하는지 검증하여, 회귀를 감지할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHERE 검증 모드가 활성화되면 THEN Replay Script는 각 액션 후에 스크린샷을 캡처해야 한다
2. WHEN 재실행 중에 스크린샷이 캡처되면 THEN 스크립트는 이미지 해시를 계산해야 한다
3. WHEN 예상 해시가 제공되면 THEN 스크립트는 현재 해시와 예상 해시를 비교해야 한다
4. IF 해시 차이가 임계값을 초과하면 THEN 스크립트는 검증 실패를 로그해야 한다
5. WHEN 검증이 실패하면 THEN 스크립트는 실행을 계속하고 마지막에 모든 실패를 보고해야 한다

### Requirement 8 (요구사항 8)

**User Story (사용자 스토리):** QA 엔지니어로서, 여러 테스트 케이스를 관리하여, 다양한 테스트 시나리오를 조직할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 사용자가 테스트 케이스를 저장하면 THEN QA System은 테스트 케이스 이름을 요청해야 한다
2. WHEN 테스트 케이스 이름이 제공되면 THEN QA System은 이름을 파일명으로 하여 Replay Script를 저장해야 한다
3. WHEN 테스트 케이스가 저장되면 THEN QA System은 액션을 JSON 파일로도 저장해야 한다
4. WHEN 사용자가 테스트 케이스 목록을 요청하면 THEN QA System은 생성 타임스탬프와 함께 저장된 모든 테스트 케이스 이름을 표시해야 한다
5. WHEN 사용자가 테스트 케이스를 로드하면 THEN QA System은 JSON 파일을 읽고 액션 목록을 채워야 한다

### Requirement 9 (요구사항 9)

**User Story (사용자 스토리):** QA 엔지니어로서, 시스템이 오류를 우아하게 처리하여, 일시적인 실패가 테스트 워크플로우를 중단하지 않기를 원한다.

#### Acceptance Criteria (수락 기준)

1. IF 게임 프로세스 시작이 실패하면 THEN QA System은 오류를 로그하고 명확한 메시지와 함께 종료해야 한다
2. IF AWS Bedrock에 접근할 수 없으면 THEN UI Analyzer는 OCR로 폴백하기 전에 지수 백오프로 재시도해야 한다
3. IF PyAutoGUI가 액션 실행에 실패하면 THEN Action Recorder는 오류를 로그하고 사용자에게 재시도 또는 건너뛰기를 요청해야 한다
4. IF 설정 파일이 잘못된 형식이면 THEN QA System은 검증 오류를 표시하고 기본값을 사용해야 한다
5. IF Replay Script가 실행 중 오류를 만나면 THEN 스크립트는 오류를 로그하고 나머지 액션을 계속 실행해야 한다

### Requirement 10 (요구사항 10)

**User Story (사용자 스토리):** QA 엔지니어로서, JSON 파일을 통해 시스템 동작을 설정하여, 다양한 게임에 맞게 자동화를 커스터마이즈할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN QA System이 시작되면 THEN 시스템은 config.json에서 설정을 로드해야 한다
2. WHEN 설정이 AWS region을 지정하면 THEN 시스템은 Bedrock 클라이언트에 해당 region을 사용해야 한다
3. WHEN 설정이 게임 실행 파일 경로를 지정하면 THEN 시스템은 해당 경로를 사용하여 게임을 실행해야 한다
4. WHEN 설정이 시작 대기 시간을 지정하면 THEN 시스템은 게임 실행 후 해당 시간만큼 대기해야 한다
5. WHEN 설정이 액션 지연 시간을 지정하면 THEN 시스템은 재실행된 액션 사이에 해당 시간만큼 대기해야 한다
6. WHEN 설정이 screenshot-on-action 설정을 지정하면 THEN 시스템은 그에 따라 스크린샷을 캡처해야 한다

### Requirement 11 (요구사항 11)

**User Story (사용자 스토리):** QA 엔지니어로서, 액션 기록 시 의미론적 맥락 정보를 함께 저장하여, UI 변경에도 강건한 테스트를 작성할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 사용자가 마우스를 클릭하면 THEN Semantic Action Recorder는 클릭 전후 스크린샷을 캡처해야 한다
2. WHEN 클릭 이벤트가 발생하면 THEN Semantic Action Recorder는 Vision LLM을 사용하여 클릭한 UI 요소의 타입, 텍스트, 시각적 특징을 분석해야 한다
3. WHEN UI 요소가 분석되면 THEN Semantic Action Recorder는 요소의 의미론적 정보(기능, 의도, 주변 컨텍스트)를 추출해야 한다
4. WHEN 액션 후 화면이 변경되면 THEN Semantic Action Recorder는 화면 전환 정보(이전 상태, 이후 상태, 전환 타입)를 기록해야 한다
5. WHEN 키보드 입력이 발생하면 THEN Semantic Action Recorder는 입력 필드의 타입과 목적을 분석해야 한다
6. WHEN 의미론적 액션이 기록되면 THEN 액션은 물리적 정보(좌표)와 의미론적 정보(의도, 맥락)를 모두 포함해야 한다

### Requirement 12 (요구사항 12)

**User Story (사용자 스토리):** QA 엔지니어로서, 테스트 재실행 시 의미론적 매칭을 통해 UI 요소를 찾아, UI 변경에도 테스트가 실패하지 않기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 의미론적 액션을 재실행하면 THEN Semantic Action Replayer는 먼저 저장된 좌표로 시도해야 한다
2. IF 저장된 좌표에서 예상한 UI 요소를 찾지 못하면 THEN Semantic Action Replayer는 의미론적 매칭을 시도해야 한다
3. WHEN 의미론적 매칭을 수행하면 THEN Semantic Action Replayer는 Vision LLM에게 요소의 기능과 텍스트를 기반으로 현재 위치를 질의해야 한다
4. WHEN Vision LLM이 요소를 찾으면 THEN Semantic Action Replayer는 찾은 좌표로 액션을 실행해야 한다
5. IF Vision LLM이 요소를 찾지 못하면 THEN Semantic Action Replayer는 가장 유사한 요소를 제안하고 사용자 확인을 요청해야 한다
6. WHEN 액션 실행 후 THEN Semantic Action Replayer는 예상한 화면 전환이 발생했는지 검증해야 한다
7. IF 예상과 다른 화면 전환이 발생하면 THEN Semantic Action Replayer는 경고를 로그하고 오차율 통계에 기록해야 한다

### Requirement 13 (요구사항 13)

**User Story (사용자 스토리):** QA 엔지니어로서, 테스트 재실행 중 오동작을 실시간으로 측정하여, 시스템의 정확도를 파악할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 테스트 재실행이 시작되면 THEN Accuracy Tracker는 새로운 실행 세션을 생성해야 한다
2. WHEN 각 액션이 재실행되면 THEN Accuracy Tracker는 액션의 성공/실패 상태를 기록해야 한다
3. WHEN 의미론적 매칭이 발생하면 THEN Accuracy Tracker는 좌표 변경 여부와 변경 거리를 기록해야 한다
4. WHEN 화면 전환 검증이 수행되면 THEN Accuracy Tracker는 예상 결과와 실제 결과의 일치 여부를 기록해야 한다
5. WHEN 테스트 재실행이 완료되면 THEN Accuracy Tracker는 전체 정확도 통계를 계산해야 한다
6. WHEN 정확도 통계가 계산되면 THEN 통계는 성공률, 의미론적 매칭 사용률, 평균 좌표 변경 거리를 포함해야 한다

### Requirement 14 (요구사항 14)

**User Story (사용자 스토리):** QA 엔지니어로서, 재실행 중 특정 액션의 오동작을 수동으로 표시하여, 시스템이 해당 액션을 재평가하고 개선할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 테스트 재실행 중 사용자가 일시정지 명령을 내리면 THEN QA System은 현재 액션에서 실행을 중지해야 한다
2. WHEN 실행이 일시정지되면 THEN QA System은 현재 액션 정보와 화면 상태를 표시해야 한다
3. WHEN 사용자가 "mark_error" 명령을 입력하면 THEN QA System은 현재 액션을 오동작으로 표시해야 한다
4. WHEN 액션이 오동작으로 표시되면 THEN QA System은 사용자에게 오류 타입을 선택하도록 요청해야 한다
5. WHEN 오류 타입이 선택되면 THEN QA System은 해당 액션의 의미론적 정보를 재분석하고 개선된 버전을 제안해야 한다
6. WHEN 개선된 액션이 제안되면 THEN 사용자는 제안을 수락하거나 수동으로 수정할 수 있어야 한다
7. WHEN 액션이 수정되면 THEN QA System은 테스트 케이스를 업데이트하고 재실행을 계속해야 한다

### Requirement 15 (요구사항 15)

**User Story (사용자 스토리):** QA 엔지니어로서, 여러 테스트 실행의 정확도 통계를 시각화하여, 시스템 성능의 추세를 파악할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 사용자가 "stats" 명령을 입력하면 THEN QA System은 현재 테스트 케이스의 실행 이력을 표시해야 한다
2. WHEN 실행 이력이 표시되면 THEN 각 실행의 날짜, 성공률, 오류 수, 의미론적 매칭 사용률을 포함해야 한다
3. WHEN 사용자가 "report" 명령을 입력하면 THEN QA System은 HTML 형식의 상세 리포트를 생성해야 한다
4. WHEN HTML 리포트가 생성되면 THEN 리포트는 정확도 추세 그래프, 오류 타입별 분포, 가장 문제가 많은 액션 목록을 포함해야 한다
5. WHEN 사용자가 특정 액션을 선택하면 THEN QA System은 해당 액션의 상세 분석(성공률, 평균 매칭 시간, 오류 이력)을 표시해야 한다
6. WHEN 정확도가 설정된 임계값 이하로 떨어지면 THEN QA System은 경고를 표시하고 재학습을 제안해야 한다

### Requirement 16 (요구사항 16)

**User Story (사용자 스토리):** QA 엔지니어로서, 오동작이 많은 액션을 자동으로 재학습하여, 시스템의 정확도를 지속적으로 개선할 수 있기를 원한다.

#### Acceptance Criteria (수락 기준)

1. WHEN 특정 액션의 실패율이 30%를 초과하면 THEN QA System은 해당 액션을 재학습 후보로 표시해야 한다
2. WHEN 사용자가 "retrain" 명령을 입력하면 THEN QA System은 재학습 후보 액션 목록을 표시해야 한다
3. WHEN 사용자가 재학습할 액션을 선택하면 THEN QA System은 해당 액션의 모든 실행 이력을 분석해야 한다
4. WHEN 실행 이력이 분석되면 THEN QA System은 성공한 경우와 실패한 경우의 패턴을 추출해야 한다
5. WHEN 패턴이 추출되면 THEN QA System은 Vision LLM을 사용하여 더 강건한 의미론적 정보를 생성해야 한다
6. WHEN 개선된 의미론적 정보가 생성되면 THEN QA System은 테스트 케이스를 업데이트하고 검증 실행을 수행해야 한다
7. WHEN 검증 실행이 완료되면 THEN QA System은 개선 전후의 정확도를 비교하여 표시해야 한다
