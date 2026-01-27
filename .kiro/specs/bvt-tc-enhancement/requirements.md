# Requirements Document: BVT-TC 연결 강화

## Introduction

BVT 테스트 항목과 테스트 케이스(TC) 간의 매칭 정확도를 향상시키는 기능이다. 현재 시스템은 텍스트 유사도 기반 매칭만 지원하여, 아이콘 기반 UI나 맥락 정보가 부족한 경우 매칭률이 낮다. 이 기능은 BVT 기반 TC 템플릿 생성, 수동 어노테이션, 게임별 UI 사전, 하이브리드 매칭 전략을 통해 매칭 정확도를 크게 향상시킨다.

## Problem Statement

**현재 문제:**
1. 아이콘 기반 UI에서 텍스트가 없어 Vision LLM이 의미를 추출하기 어려움
2. 숫자가 무엇을 의미하는지 맥락 정보 부재
3. BVT 항목에서 TC로의 역방향 연결 방법 부재
4. 게임별 특화된 UI 패턴 인식 불가

**예시 (BVT No.4):**
> "열쇠/골드/루비 수량 노출 확인"
- 화면 상단에 아이콘으로만 표시됨
- 텍스트 없이 아이콘만 있어 자동 매칭 불가

## Glossary

- **BVT_TC_Template**: BVT 항목 정보가 미리 주입된 테스트 케이스 템플릿
- **UI_Dictionary**: 게임별 아이콘-의미 매핑 사전
- **Annotation**: 스크린샷에 수동으로 추가하는 의미론적 라벨
- **Hybrid_Matching**: 텍스트 유사도 + 화면 위치 + 시각적 패턴을 종합한 매칭 전략
- **Verification_Hint**: BVT 항목에서 추출한 검증 힌트 정보
- **Visual_Pattern**: 아이콘이나 UI 요소의 시각적 특징 패턴

## Requirements

### Requirement 1: BVT 기반 TC 템플릿 생성 (단기)

**User Story:** QA 엔지니어로서, 특정 BVT 항목을 선택하면 해당 항목에 맞는 테스트 케이스 템플릿을 자동으로 생성하고 싶다. 이를 통해 BVT 맥락 정보가 미리 주입된 TC를 쉽게 만들 수 있다.

#### Acceptance Criteria

1. BVT 번호를 지정하면, BVTTemplateGenerator는 해당 BVT 항목 정보가 포함된 TC 템플릿 JSON 파일을 생성해야 한다
2. 생성된 템플릿은 bvt_reference (no, categories, check), verification_hints (target_elements, expected_values, screen_location), actions (빈 배열) 필드를 포함해야 한다
3. verification_hints는 BVT check 설명에서 키워드를 추출하여 자동으로 생성해야 한다
4. 템플릿 파일명은 `bvt_{번호}_{간략한_설명}.json` 형식이어야 한다
5. 여러 BVT 번호를 한 번에 지정하여 배치 생성이 가능해야 한다
6. 생성된 템플릿은 기존 SemanticTestCase 로더와 호환되어야 한다

### Requirement 2: 수동 어노테이션 도구 (단기)

**User Story:** QA 엔지니어로서, 녹화된 테스트 케이스의 스크린샷에 수동으로 의미론적 정보를 추가하고 싶다. 이를 통해 아이콘 기반 UI도 정확하게 라벨링할 수 있다.

#### Acceptance Criteria

1. AnnotationTool은 테스트 케이스 JSON 파일을 로드하여 각 액션의 스크린샷을 표시해야 한다
2. 사용자는 스크린샷 위에 사각형 영역을 지정하고 의미론적 라벨을 부여할 수 있어야 한다
3. 어노테이션 정보는 해당 액션의 semantic_info.annotations 필드에 저장되어야 한다
4. 어노테이션은 label (텍스트), region (x, y, width, height), element_type (icon, text, button 등) 필드를 포함해야 한다
5. BVT 항목과 어노테이션을 연결하는 bvt_link 필드를 지원해야 한다
6. 어노테이션된 TC는 원본 TC와 별도 파일로 저장하거나 원본을 업데이트할 수 있어야 한다
7. CLI 모드와 GUI 모드 모두 지원해야 한다 (GUI는 선택적)

### Requirement 3: 게임별 UI 사전 (중기)

**User Story:** QA 엔지니어로서, 게임별로 자주 사용되는 아이콘과 UI 요소의 의미를 사전에 등록하고 싶다. 이를 통해 Vision LLM 분석 결과를 보강하여 자동 인식률을 향상시킬 수 있다.

#### Acceptance Criteria

1. UIDictionary는 게임별로 아이콘-의미 매핑 정보를 JSON 파일로 관리해야 한다
2. 각 아이콘 항목은 visual_pattern (시각적 설명), semantic_meaning (의미), typical_location (일반적 위치), bvt_keywords (관련 BVT 키워드) 필드를 포함해야 한다
3. 템플릿 이미지 경로를 지정하여 시각적 매칭에 활용할 수 있어야 한다
4. UIDictionaryMatcher는 Vision LLM 분석 결과와 사전을 매칭하여 의미를 보강해야 한다
5. 사전에 없는 새로운 아이콘을 쉽게 추가할 수 있는 인터페이스를 제공해야 한다
6. 여러 게임의 사전을 관리하고 게임별로 전환할 수 있어야 한다
7. 사전 항목은 신뢰도 점수를 가지며, 매칭 시 신뢰도가 반영되어야 한다

### Requirement 4: 하이브리드 매칭 전략 (장기)

**User Story:** QA 엔지니어로서, 텍스트 유사도뿐만 아니라 화면 위치, 시각적 패턴 등 다양한 신호를 종합하여 BVT-TC 매칭 정확도를 높이고 싶다.

#### Acceptance Criteria

1. HybridMatchingAnalyzer는 텍스트 유사도, 화면 위치 매칭, 시각적 패턴 매칭을 종합하여 신뢰도 점수를 계산해야 한다
2. 각 매칭 전략의 가중치를 설정 파일에서 조정할 수 있어야 한다
3. 화면 위치 매칭은 BVT category 정보와 TC의 클릭 좌표 영역을 비교해야 한다
4. 시각적 패턴 매칭은 UI 사전의 템플릿 이미지와 스크린샷을 비교해야 한다
5. 어노테이션 정보가 있으면 우선적으로 활용하여 매칭 정확도를 높여야 한다
6. 매칭 결과에 각 전략별 점수와 종합 점수를 포함해야 한다
7. 기존 MatchingAnalyzer와 호환되며, 설정으로 전환 가능해야 한다

### Requirement 5: BVT 검증 스크립트 자동 생성 (장기)

**User Story:** QA 엔지니어로서, BVT 항목의 check 설명에서 검증 로직을 자동으로 추출하여 실행 가능한 검증 스크립트를 생성하고 싶다.

#### Acceptance Criteria

1. VerificationScriptGenerator는 BVT check 설명을 분석하여 검증 로직을 추출해야 한다
2. "노출 확인" 패턴은 해당 요소의 존재 여부를 검증하는 코드를 생성해야 한다
3. "터치 시 메뉴 이동" 패턴은 클릭 후 화면 전환을 검증하는 코드를 생성해야 한다
4. UI 사전의 템플릿 이미지를 활용하여 시각적 검증 코드를 생성해야 한다
5. 생성된 스크립트는 Python 함수 형태로, PlayTestCase 실행 시 호출 가능해야 한다
6. 검증 실패 시 상세한 오류 메시지와 스크린샷을 포함한 리포트를 생성해야 한다
7. 수동으로 검증 로직을 추가하거나 수정할 수 있어야 한다

### Requirement 6: 통합 워크플로우

**User Story:** QA 엔지니어로서, BVT 항목 선택부터 TC 생성, 녹화, 어노테이션, 매칭, 검증까지 일관된 워크플로우로 진행하고 싶다.

#### Acceptance Criteria

1. 워크플로우는 다음 단계를 지원해야 한다: BVT 선택 → 템플릿 생성 → 녹화 → 어노테이션 → 매칭 → 검증
2. 각 단계는 독립적으로 실행 가능하며, 이전 단계의 결과를 자동으로 로드해야 한다
3. 진행 상황을 추적하고 중단된 지점에서 재개할 수 있어야 한다
4. CLI 인터페이스로 전체 워크플로우를 제어할 수 있어야 한다
5. 워크플로우 설정을 프로젝트별로 저장하고 재사용할 수 있어야 한다

