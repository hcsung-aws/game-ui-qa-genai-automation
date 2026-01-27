# BVT-TC Enhancement Spec Tasks 생성

## 날짜
2026-01-25

## 요청 내용
Context Transfer에서 이어받은 작업으로, `bvt-tc-enhancement` spec의 `tasks.md` 파일 생성

## 배경
- `requirements.md`와 `design.md`는 이전 세션에서 이미 생성됨
- BVT No.4 "열쇠/골드/루비 수량 노출 확인" 같은 아이콘 기반 UI 매칭 문제 해결을 위한 스펙
- 단기/중기/장기 3단계 솔루션 포함

## 수행 작업

### 1. 기존 파일 분석
- `.kiro/specs/bvt-tc-enhancement/requirements.md` - 6개 요구사항 확인
- `.kiro/specs/bvt-tc-enhancement/design.md` - 아키텍처 및 컴포넌트 설계 확인
- `.kiro/specs/bvt-semantic-integration/tasks.md` - 기존 tasks.md 형식 참고

### 2. tasks.md 생성
`.kiro/specs/bvt-tc-enhancement/tasks.md` 파일 생성

#### Phase 1: 단기 구현 (템플릿 & 어노테이션)
- Task 1: 데이터 모델 확장 (BVTTemplate, VerificationHints, Annotation, Region)
- Task 2: BVT 템플릿 생성기 (KeywordExtractor, BVTTemplateGenerator)
- Task 3: Checkpoint - 템플릿 생성기 검증
- Task 4: 어노테이션 도구 (AnnotatableTestCase, AnnotationTool CLI)
- Task 5: Checkpoint - Phase 1 완료 검증

#### Phase 2: 중기 구현 (UI 사전)
- Task 6: UI 사전 데이터 모델 (UIEntry)
- Task 7: UI 사전 관리자 (UIDictionary)
- Task 8: UI 사전 매처 (UIDictionaryMatcher)
- Task 9: Checkpoint - Phase 2 완료 검증

#### Phase 3: 장기 구현 (하이브리드 매칭)
- Task 10: 하이브리드 매칭 데이터 모델 (HybridMatchResult)
- Task 11: 하이브리드 매칭 분석기 (HybridMatchingAnalyzer)
- Task 12: Checkpoint - 하이브리드 매칭 검증
- Task 13: 검증 스크립트 생성기 (VerificationScriptGenerator)
- Task 14: Checkpoint - 검증 스크립트 생성기 검증

#### Phase 4: 통합 워크플로우
- Task 15: 통합 워크플로우 (EnhancedWorkflow, CLI)
- Task 16: Final Checkpoint - 전체 시스템 검증

### Property-Based Tests 포함
- Property 1: 템플릿 생성 정확성
- Property 2: Annotation round-trip
- Property 3: UI 사전 키워드 매칭 정확성
- Property 4: 하이브리드 점수 범위
- Property 5: 하이브리드 점수 가중 합계
- Property 6: 검증 스크립트 실행 가능성

## 결과
- `.kiro/specs/bvt-tc-enhancement/tasks.md` 파일 생성 완료
- 총 16개 태스크, 4개 Phase로 구성
- 기존 bvt-semantic-integration 모듈과 호환성 유지 설계

## 다음 단계
사용자가 tasks.md를 검토한 후, Phase 1부터 순차적으로 구현 시작 가능
