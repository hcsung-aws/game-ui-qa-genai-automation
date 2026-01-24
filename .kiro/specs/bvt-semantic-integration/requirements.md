# Requirements Document

## Introduction

BVT(Build Verification Test) 테스트 데이터와 기존 의미론적 테스트 케이스를 연결하여 자동화된 QA 파이프라인을 구축하는 기능이다. 녹화된 테스트 케이스들을 분석하여 BVT 테스트 항목들과의 연관관계를 파악하고, 매칭된 데이터를 바탕으로 자동 플레이 테스트를 생성하며, 최종적으로 테스트 결과가 반영된 새로운 BVT 문서를 생성한다.

## Glossary

- **BVT_Parser**: BVT CSV 파일을 파싱하여 테스트 케이스 구조로 변환하는 컴포넌트
- **BVT_Test_Case**: BVT 문서의 개별 테스트 항목 (No., Category 1~3, Check, Test Result, BTS ID, Comment 포함)
- **Semantic_Test_Case**: 의미론적 정보가 포함된 녹화된 테스트 케이스 (JSON 형식)
- **Semantic_Summary**: 모든 테스트 케이스의 의미론적 정보를 종합한 요약 문서 (테스트 케이스별 intent, target_element, context 포함)
- **Matching_Analyzer**: Semantic_Summary와 BVT 테스트 케이스 간의 연관관계를 분석하는 컴포넌트
- **Match_Result**: 매칭 분석 결과 (BVT 항목, 매칭된 테스트 케이스, 액션 인덱스 범위, 신뢰도 점수 포함)
- **Auto_Play_Generator**: Match_Result를 바탕으로 자동 플레이 테스트를 생성하는 컴포넌트
- **Play_Test_Case**: 자동 플레이를 통해 생성된 테스트 케이스 (스크린샷, 의미론적 정보, BVT 참조 정보 포함)
- **BVT_Updater**: 테스트 결과를 BVT 문서에 반영하여 새로운 BVT 파일을 생성하는 컴포넌트
- **Confidence_Score**: 매칭 신뢰도 점수 (0.0 ~ 1.0)

## Requirements

### Requirement 1: BVT 데이터 파싱

**User Story:** QA 엔지니어로서, BVT CSV 파일을 구조화된 테스트 케이스 객체로 파싱하고 싶다. 이를 통해 녹화된 테스트 케이스와 프로그래밍 방식으로 분석하고 매칭할 수 있다.

#### Acceptance Criteria

1. 유효한 BVT CSV 파일 경로가 제공되면, BVT_Parser는 파싱하여 BVT_Test_Case 객체 리스트를 반환해야 한다
2. BVT CSV 파일을 파싱할 때, BVT_Parser는 No., Category 1, Category 2, Category 3, Check, Test Result, BTS ID, Comment 필드를 추출해야 한다
3. BVT CSV 파일에 헤더 행이나 요약 행이 포함되어 있으면, BVT_Parser는 이를 건너뛰고 테스트 케이스 행만 파싱해야 한다
4. BVT CSV 파일이 잘못된 형식이거나 필수 컬럼이 누락된 경우, BVT_Parser는 설명적인 오류를 반환해야 한다
5. BVT_Parser는 BVT_Test_Case 객체를 JSON으로 직렬화하고 다시 역직렬화하여 동등한 객체를 생성해야 한다 (round-trip 속성)

### Requirement 2: 의미론적 테스트 케이스 로딩 및 요약 문서 생성

**User Story:** QA 엔지니어로서, 테스트 케이스 디렉토리의 모든 의미론적 테스트를 로드하고 매칭 분석에 활용할 수 있는 요약 문서를 생성하고 싶다. 이를 통해 BVT 항목과의 연결 가능성을 판단할 수 있다.

#### Acceptance Criteria

1. 테스트 케이스 디렉토리 경로가 제공되면, Semantic_Test_Case 로더는 디렉토리 내 모든 JSON 파일을 파싱하여 Semantic_Test_Case 객체 리스트를 반환해야 한다
2. 테스트 케이스 JSON 파일에 액션에 대한 semantic_info가 포함되어 있으면, 로더는 intent, target_element, context를 포함한 모든 의미론적 정보를 보존해야 한다
3. 테스트 케이스 JSON 파일이 잘못된 형식인 경우, 로더는 오류를 로그에 기록하고 다른 파일 로딩을 계속해야 한다
4. 모든 테스트 케이스가 로드되면, 시스템은 각 테스트 케이스의 의미론적 정보를 종합한 Semantic_Summary 문서를 생성해야 한다
5. Semantic_Summary 문서는 테스트 케이스별로 수행하는 주요 동작(intent), 상호작용하는 UI 요소(target_element), 화면 상태(context)를 요약해야 한다
6. Semantic_Summary 문서는 BVT 매칭 분석의 입력으로 사용될 수 있는 구조화된 형식이어야 한다
7. 로더는 Semantic_Test_Case 객체를 JSON으로 직렬화하고 다시 역직렬화하여 동등한 객체를 생성해야 한다 (round-trip 속성)

### Requirement 3: BVT-테스트케이스 매칭 분석

**User Story:** QA 엔지니어로서, BVT 테스트 항목과 Semantic_Summary를 기반으로 연관관계를 분석하고 싶다. 이를 통해 어떤 녹화된 테스트 케이스(전체 또는 일부)가 어떤 BVT 요구사항을 검증할 수 있는지 식별할 수 있다.

#### Acceptance Criteria

1. BVT_Test_Case와 Semantic_Summary를 비교 분석할 때, Matching_Analyzer는 신뢰도 점수가 포함된 Match_Results를 반환해야 한다
2. 매칭 시, Matching_Analyzer는 BVT Check 설명과 Semantic_Summary의 intent, target_element 설명 간의 텍스트 유사도를 사용해야 한다
3. 매칭 시, Matching_Analyzer는 컨텍스트 매칭을 위해 Category 계층 구조(Category 1 > 2 > 3)를 고려해야 한다
4. 매칭 신뢰도 점수가 0.7 이상이면, Matching_Analyzer는 이를 고신뢰도 매칭으로 표시해야 한다
5. 여러 테스트 케이스가 단일 BVT 항목과 매칭되면, Matching_Analyzer는 신뢰도 점수 내림차순으로 정렬된 모든 매칭을 반환해야 한다
6. BVT 항목에 임계값 이상의 매칭 테스트 케이스가 없으면, Matching_Analyzer는 이를 미매칭으로 표시해야 한다
7. 매칭된 테스트 케이스에서 BVT Check에 해당하는 액션 시퀀스(전체 또는 일부)를 식별하여 Match_Result에 포함해야 한다
8. Match_Result는 매칭된 테스트 케이스 이름, 해당 액션 인덱스 범위, BVT 참조 정보를 포함해야 한다
9. Matching_Analyzer는 동일한 입력에 대해 일관된 결과를 생성해야 한다 (결정론적 속성)

### Requirement 4: 자동 플레이 테스트 생성

**User Story:** QA 엔지니어로서, Match_Result를 바탕으로 자동화된 플레이 테스트를 생성하고 싶다. 이를 통해 BVT 요구사항을 검증하는 재생 가능한 테스트 케이스를 만들 수 있다.

#### Acceptance Criteria

1. 고신뢰도 Match_Result가 제공되면, Auto_Play_Generator는 매칭된 액션 시퀀스로부터 Play_Test_Case를 생성해야 한다
2. Play_Test_Case를 생성할 때, Auto_Play_Generator는 Match_Result에 지정된 액션 인덱스 범위의 액션들만 추출해야 한다
3. Play_Test_Case를 생성할 때, Auto_Play_Generator는 BVT 참조 정보(No., Categories, Check 설명)를 포함해야 한다
4. Play_Test_Case를 실행할 때, Auto_Play_Generator는 각 액션 단계에서 스크린샷을 캡처해야 한다
5. Play_Test_Case를 실행할 때, Auto_Play_Generator는 액션 재생을 위해 의미론적 매칭을 사용해야 한다 (SemanticActionReplayer 활용)
6. 플레이 테스트 실행 중 액션이 실패하면, Auto_Play_Generator는 실패를 로그에 기록하고 나머지 액션을 계속 진행해야 한다
7. Play_Test_Case가 완료되면, Auto_Play_Generator는 전체 테스트 결과(PASS, FAIL, 또는 BLOCKED)를 기록해야 한다
8. 생성된 Play_Test_Case는 독립적으로 재실행 가능한 JSON 형식으로 저장되어야 한다

### Requirement 5: BVT 문서 업데이트

**User Story:** QA 엔지니어로서, 테스트 결과로 BVT 문서를 업데이트하고 싶다. 이를 통해 자동화된 테스트 커버리지가 반영된 새로운 BVT 파일을 생성할 수 있다.

#### Acceptance Criteria

1. Play_Test_Case 결과가 사용 가능하면, BVT_Updater는 해당 BVT_Test_Case의 Test Result 필드를 업데이트해야 한다
2. BVT_Test_Case를 업데이트할 때, BVT_Updater는 성공한 테스트에 대해 Test Result를 "PASS"로 설정해야 한다
3. BVT_Test_Case를 업데이트할 때, BVT_Updater는 실패한 테스트에 대해 Test Result를 "Fail"로 설정하고 Comment에 실패 세부 정보를 추가해야 한다
4. BVT_Test_Case를 업데이트할 때, BVT_Updater는 원본 BTS ID 값을 보존해야 한다
5. 새로운 BVT CSV 파일을 생성할 때, BVT_Updater는 원본 파일 구조와 포맷을 유지해야 한다
6. 새로운 BVT CSV 파일을 생성할 때, BVT_Updater는 파일명에 타임스탬프를 포함해야 한다
7. BVT_Updater는 BVT 파일을 파싱한 후 작성하고 다시 파싱하여 동등한 내용을 생성해야 한다 (round-trip 속성)

### Requirement 6: 매칭 리포트 생성

**User Story:** QA 엔지니어로서, 매칭 리포트를 생성하고 싶다. 이를 통해 분석 결과를 검토하고 테스트 커버리지의 갭을 식별할 수 있다.

#### Acceptance Criteria

1. 매칭 분석이 완료되면, 시스템은 총 BVT 항목 수, 매칭된 항목 수, 미매칭 항목 수가 포함된 요약 리포트를 생성해야 한다
2. 리포트를 생성할 때, 시스템은 BVT 항목 세부 정보와 매칭된 테스트 케이스 이름이 포함된 모든 고신뢰도 매칭을 나열해야 한다
3. 리포트를 생성할 때, 시스템은 수동 검토를 위해 모든 미매칭 BVT 항목을 나열해야 한다
4. 리포트를 생성할 때, 시스템은 전체 커버리지 백분율을 계산하고 표시해야 한다
5. 리포트 생성기는 JSON과 사람이 읽을 수 있는 Markdown 형식 모두로 리포트를 출력해야 한다

### Requirement 7: 통합 파이프라인

**User Story:** QA 엔지니어로서, 완전한 BVT-의미론적 통합 파이프라인을 실행하고 싶다. 이를 통해 분석부터 BVT 업데이트까지 전체 프로세스를 자동화할 수 있다.

#### Acceptance Criteria

1. BVT 파일 경로와 테스트 케이스 디렉토리로 파이프라인이 실행되면, 시스템은 모든 단계를 순서대로 실행해야 한다: 파싱, 로드, 매칭, 생성, 실행, 업데이트
2. 파이프라인을 실행할 때, 시스템은 각 단계에 대한 진행 콜백을 제공해야 한다
3. 파이프라인을 실행할 때, 시스템은 테스트를 실행하지 않고 분석만 수행하는 dry-run 모드를 지원해야 한다
4. 어떤 단계가 실패하면, 시스템은 오류를 로그에 기록하고 실패 지점까지의 부분 결과를 제공해야 한다
5. 파이프라인이 완료되면, 시스템은 업데이트된 BVT 파일과 매칭 리포트를 모두 생성해야 한다
