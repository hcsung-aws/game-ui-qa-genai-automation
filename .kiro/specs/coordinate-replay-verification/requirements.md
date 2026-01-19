# 요구사항 문서

## 소개

본 기능은 좌표 기반 테스트 replay에서도 테스트 성공/실패 여부를 검증하여 반환하는 기능을 추가하는 것이다. 현재 시스템은 의미론적 테스트와 좌표 기반 테스트가 분리되어 있으며, 의미론적 테스트에서만 검증 로직이 활용되고 있다. 이 기능을 통해 좌표 기반 replay에서도 동일한 검증 방식(스크린샷 비교 + Vision LLM 재검증)을 적용하여 테스트 결과를 판단할 수 있도록 한다.

## 용어 정의

- **좌표 기반 Replay (Coordinate-based Replay)**: 기록된 마우스/키보드 이벤트의 좌표를 그대로 사용하여 재현하는 방식
- **의미론적 Replay (Semantic Replay)**: UI 요소의 의미론적 정보를 활용하여 현재 화면에서 대상 요소를 찾아 재현하는 방식
- **검증 (Verification)**: 액션 실행 후 화면 상태가 예상과 일치하는지 확인하는 과정
- **스크린샷 비교 (Screenshot Comparison)**: 기록 시점의 스크린샷과 재현 시점의 스크린샷을 비교하여 유사도를 측정하는 방식
- **Vision LLM 검증 (Vision LLM Verification)**: 스크린샷 비교 실패 시 Vision LLM을 사용하여 의미적 일치 여부를 판단하는 방식
- **테스트 결과 (Test Result)**: 테스트의 성공/실패/경고 상태와 상세 정보를 포함하는 데이터
- **ReplayVerifier**: 스크린샷 비교와 Vision LLM을 조합하여 replay 결과를 검증하는 컴포넌트

## 요구사항

### 요구사항 1: 좌표 기반 Replay에서 검증 기능 활성화

**사용자 스토리:** QA 엔지니어로서, 좌표 기반 replay 실행 시에도 각 액션의 성공/실패 여부를 확인하고 싶다. 이를 통해 테스트 결과를 자동으로 판단할 수 있다.

#### 인수 조건

1. WHEN 좌표 기반 replay가 `--verify` 옵션과 함께 실행되면 THEN Replay_Script는 각 클릭 액션 후 ReplayVerifier를 사용하여 검증을 수행해야 한다 (SHALL)
2. WHEN 검증이 활성화된 상태에서 클릭 액션이 실행되면 THEN Replay_Script는 액션 실행 후 현재 화면을 캡처해야 한다 (SHALL)
3. WHEN 현재 화면이 캡처되면 THEN ReplayVerifier는 기록 시점의 스크린샷과 비교하여 유사도를 계산해야 한다 (SHALL)
4. WHEN 스크린샷 유사도가 임계값 이상이면 THEN ReplayVerifier는 해당 액션을 "pass"로 판정해야 한다 (SHALL)
5. WHEN 스크린샷 유사도가 임계값 미만이면 THEN ReplayVerifier는 Vision LLM을 사용하여 의미적 일치 여부를 재검증해야 한다 (SHALL)

### 요구사항 2: 검증 결과 반환 및 보고

**사용자 스토리:** QA 엔지니어로서, replay 완료 후 전체 테스트 결과를 요약하여 확인하고 싶다. 이를 통해 어떤 액션이 실패했는지 빠르게 파악할 수 있다.

#### 인수 조건

1. WHEN replay 세션이 완료되면 THEN ReplayVerifier는 전체 액션의 pass/fail/warning 카운트를 포함하는 보고서를 생성해야 한다 (SHALL)
2. WHEN 보고서가 생성되면 THEN ReplayVerifier는 각 액션별 검증 결과(스크린샷 유사도, Vision LLM 결과)를 포함해야 한다 (SHALL)
3. WHEN 보고서가 생성되면 THEN ReplayVerifier는 전체 성공률을 계산하여 포함해야 한다 (SHALL)
4. WHEN replay가 완료되면 THEN Replay_Script는 테스트 성공/실패 여부를 반환값으로 제공해야 한다 (SHALL)
5. WHEN 보고서가 생성되면 THEN ReplayVerifier는 JSON 및 텍스트 형식으로 보고서를 저장해야 한다 (SHALL)

### 요구사항 3: 기존 테스트 케이스 호환성

**사용자 스토리:** QA 엔지니어로서, 기존에 기록한 좌표 기반 테스트 케이스에서도 검증 기능을 사용하고 싶다. 이를 통해 새로운 형식으로 변환하지 않아도 검증이 가능하다.

#### 인수 조건

1. WHEN 기존 테스트 케이스(semantic_info 없음)가 로드되면 THEN Replay_Script는 screenshot_path 필드를 사용하여 검증을 수행해야 한다 (SHALL)
2. WHEN 테스트 케이스에 screenshot_path가 없는 액션이 있으면 THEN ReplayVerifier는 해당 액션을 "warning"으로 처리하고 검증을 건너뛰어야 한다 (SHALL)
3. WHEN 기존 테스트 케이스와 의미론적 테스트 케이스가 혼재되면 THEN Replay_Script는 각 액션의 타입에 맞는 검증 방식을 적용해야 한다 (SHALL)

### 요구사항 4: 검증 실패 시 동작

**사용자 스토리:** QA 엔지니어로서, 검증이 실패해도 나머지 액션을 계속 실행하고 싶다. 이를 통해 전체 테스트 흐름을 파악할 수 있다.

#### 인수 조건

1. WHEN 검증이 실패하면 THEN Replay_Script는 실패를 기록하고 다음 액션을 계속 실행해야 한다 (SHALL)
2. WHEN Vision LLM 호출이 실패하면 THEN ReplayVerifier는 스크린샷 유사도만으로 결과를 판정해야 한다 (SHALL)
3. WHEN 모든 액션이 완료되면 THEN Replay_Script는 실패한 액션이 하나라도 있으면 전체 테스트를 "실패"로 판정해야 한다 (SHALL)
4. IF 스크린샷 유사도가 0.7 이상이고 Vision LLM이 실패하면 THEN ReplayVerifier는 해당 액션을 "warning"으로 처리해야 한다 (SHALL)

### 요구사항 5: CLI 인터페이스 통합

**사용자 스토리:** QA 엔지니어로서, CLI를 통해 좌표 기반 replay의 검증 기능을 쉽게 사용하고 싶다. 이를 통해 자동화 파이프라인에 통합할 수 있다.

#### 인수 조건

1. WHEN `replay` 명령어가 `--verify` 옵션과 함께 실행되면 THEN CLI_Interface는 검증 모드로 replay를 실행해야 한다 (SHALL)
2. WHEN replay가 완료되면 THEN CLI_Interface는 테스트 결과 요약을 콘솔에 출력해야 한다 (SHALL)
3. WHEN 테스트가 실패하면 THEN CLI_Interface는 종료 코드 1을 반환해야 한다 (SHALL)
4. WHEN 테스트가 성공하면 THEN CLI_Interface는 종료 코드 0을 반환해야 한다 (SHALL)
5. WHERE `--report-dir` 옵션이 지정되면 THEN CLI_Interface는 해당 디렉토리에 보고서를 저장해야 한다 (SHALL)

### 요구사항 6: 검증 결과 데이터 구조

**사용자 스토리:** 개발자로서, 검증 결과를 프로그래밍 방식으로 처리하고 싶다. 이를 통해 CI/CD 파이프라인이나 다른 도구와 통합할 수 있다.

#### 인수 조건

1. WHEN 검증이 완료되면 THEN ReplayVerifier는 VerificationResult 객체를 반환해야 한다 (SHALL)
2. WHEN VerificationResult가 생성되면 THEN 해당 객체는 action_index, final_result, screenshot_similarity, vision_match 필드를 포함해야 한다 (SHALL)
3. WHEN ReplayReport가 생성되면 THEN 해당 객체는 total_actions, passed_count, failed_count, warning_count, success_rate 필드를 포함해야 한다 (SHALL)
4. WHEN 검증 결과가 직렬화되면 THEN 모든 필드가 JSON 호환 형식으로 변환되어야 한다 (SHALL)

