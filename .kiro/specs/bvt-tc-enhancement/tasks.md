# Implementation Plan: BVT-TC 연결 강화

## Overview

BVT 테스트 항목과 테스트 케이스(TC) 간의 매칭 정확도를 향상시키는 시스템을 구현한다. 단기(템플릿 & 어노테이션), 중기(UI 사전), 장기(하이브리드 매칭) 3단계로 나누어 점진적으로 구현하며, Clean Architecture 원칙에 따라 각 컴포넌트는 단일 책임을 가지고 느슨하게 결합된다.

## Tasks

### Phase 1: 단기 구현 (템플릿 & 어노테이션)

- [ ] 1. 데이터 모델 확장
  - [ ] 1.1 BVT-TC 연결 강화용 데이터 모델 추가
    - `src/bvt_integration/tc_enhancement_models.py` 파일 생성
    - BVTTemplate, VerificationHints, Annotation, Region, BVTReference 데이터클래스 구현
    - 각 클래스에 to_dict(), from_dict() 메서드 구현
    - _Requirements: 1.1, 1.2, 2.3, 2.4_

  - [ ] 1.2 데이터 모델 round-trip 속성 테스트 작성
    - **Property 2: Annotation round-trip**
    - `tests/property/test_tc_enhancement_models_properties.py` 파일 생성
    - hypothesis 라이브러리 사용, 최소 100회 반복
    - **Validates: Requirements 2.3, 2.4**

- [ ] 2. BVT 템플릿 생성기 구현
  - [ ] 2.1 KeywordExtractor 클래스 구현
    - `src/bvt_integration/keyword_extractor.py` 파일 생성
    - extract() 메서드: BVT check 설명에서 키워드 추출
    - 한글 형태소 분석 또는 규칙 기반 추출
    - _Requirements: 1.3_

  - [ ] 2.2 BVTTemplateGenerator 클래스 구현
    - `src/bvt_integration/bvt_template_generator.py` 파일 생성
    - generate() 메서드: 단일 BVT 항목에서 TC 템플릿 생성
    - generate_batch() 메서드: 여러 BVT 항목 배치 생성
    - extract_verification_hints() 메서드: 검증 힌트 추출
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 2.3 템플릿 생성 속성 테스트 작성
    - **Property 1: 템플릿 생성 정확성**
    - 생성된 템플릿이 BVT 정보를 모두 포함하는지 검증
    - **Validates: Requirements 1.1, 1.2, 1.3**

- [ ] 3. Checkpoint - 템플릿 생성기 검증
  - 모든 테스트 통과 확인
  - 실제 BVT 샘플로 템플릿 생성 테스트
  - 사용자 질문 있으면 확인

- [ ] 4. 어노테이션 도구 구현
  - [ ] 4.1 AnnotatableTestCase 클래스 구현
    - `src/bvt_integration/annotatable_tc.py` 파일 생성
    - 기존 SemanticTestCase를 래핑하여 어노테이션 기능 추가
    - add_annotation(), remove_annotation() 메서드
    - _Requirements: 2.1, 2.2_

  - [ ] 4.2 AnnotationTool CLI 모드 구현
    - `src/bvt_integration/annotation_tool.py` 파일 생성
    - load_test_case() 메서드: TC JSON 로드
    - add_annotation() 메서드: 어노테이션 추가
    - save() 메서드: 저장 (원본 업데이트 또는 별도 파일)
    - annotate_cli() 메서드: CLI 인터페이스
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [ ] 4.3 어노테이션 도구 단위 테스트 작성
    - 어노테이션 추가/삭제 테스트
    - 저장/로드 round-trip 테스트
    - BVT 링크 연결 테스트
    - _Requirements: 2.3, 2.5, 2.6_

- [ ] 5. Checkpoint - Phase 1 완료 검증
  - 모든 테스트 통과 확인
  - 템플릿 생성 → 어노테이션 워크플로우 테스트
  - 사용자 질문 있으면 확인

### Phase 2: 중기 구현 (UI 사전)

- [ ] 6. UI 사전 데이터 모델 추가
  - [ ] 6.1 UIEntry 데이터 모델 구현
    - `src/bvt_integration/tc_enhancement_models.py`에 추가
    - UIEntry 데이터클래스 (id, visual_pattern, semantic_meaning, typical_location, bvt_keywords, template_image_path, confidence)
    - to_dict(), from_dict() 메서드
    - _Requirements: 3.2, 3.3, 3.7_

  - [ ] 6.2 UIEntry round-trip 속성 테스트 작성
    - **Property 3: UI 사전 키워드 매칭 정확성**
    - **Validates: Requirements 3.4**

- [ ] 7. UI 사전 관리자 구현
  - [ ] 7.1 UIDictionary 클래스 구현
    - `src/bvt_integration/ui_dictionary.py` 파일 생성
    - load() 메서드: 게임별 사전 로드
    - add_entry() 메서드: 항목 추가
    - find_by_keywords() 메서드: 키워드 검색
    - find_by_location() 메서드: 위치 검색
    - save() 메서드: 사전 저장
    - _Requirements: 3.1, 3.2, 3.5, 3.6_

  - [ ] 7.2 UI 사전 단위 테스트 작성
    - 사전 로드/저장 테스트
    - 키워드 검색 테스트
    - 위치 검색 테스트
    - _Requirements: 3.1, 3.5, 3.6_

- [ ] 8. UI 사전 매처 구현
  - [ ] 8.1 UIDictionaryMatcher 클래스 구현
    - `src/bvt_integration/ui_dictionary_matcher.py` 파일 생성
    - enhance_semantic_info() 메서드: Vision LLM 결과 보강
    - match_template() 메서드: 템플릿 이미지 매칭 (OpenCV 활용)
    - _Requirements: 3.4, 3.7_

  - [ ] 8.2 UI 사전 매처 단위 테스트 작성
    - 의미론적 정보 보강 테스트
    - 템플릿 매칭 테스트 (모의 이미지 사용)
    - _Requirements: 3.4, 3.7_

- [ ] 9. Checkpoint - Phase 2 완료 검증
  - 모든 테스트 통과 확인
  - 샘플 UI 사전 생성 및 매칭 테스트
  - 사용자 질문 있으면 확인

### Phase 3: 장기 구현 (하이브리드 매칭)

- [ ] 10. 하이브리드 매칭 데이터 모델 추가
  - [ ] 10.1 HybridMatchResult 데이터 모델 구현
    - `src/bvt_integration/tc_enhancement_models.py`에 추가
    - HybridMatchResult 데이터클래스 (total_score, text_similarity_score, location_matching_score, visual_pattern_score, annotation_bonus_score)
    - to_dict(), from_dict() 메서드
    - _Requirements: 4.6_

  - [ ] 10.2 HybridMatchResult 속성 테스트 작성
    - **Property 4: 하이브리드 점수 범위**
    - **Property 5: 하이브리드 점수 가중 합계**
    - **Validates: Requirements 4.1, 4.2, 4.6**

- [ ] 11. 하이브리드 매칭 분석기 구현
  - [ ] 11.1 HybridMatchingAnalyzer 클래스 구현
    - `src/bvt_integration/hybrid_matching_analyzer.py` 파일 생성
    - analyze() 메서드: 종합 매칭 분석
    - _calculate_location_score() 메서드: 화면 위치 매칭
    - _calculate_visual_score() 메서드: 시각적 패턴 매칭
    - _calculate_annotation_bonus() 메서드: 어노테이션 보너스
    - 가중치 설정 파일 지원
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [ ] 11.2 하이브리드 매칭 분석기 단위 테스트 작성
    - 개별 점수 계산 테스트
    - 가중 합계 계산 테스트
    - 기존 MatchingAnalyzer와 호환성 테스트
    - _Requirements: 4.1, 4.2, 4.7_

- [ ] 12. Checkpoint - 하이브리드 매칭 검증
  - 모든 테스트 통과 확인
  - 기존 매칭 결과와 비교 테스트
  - 사용자 질문 있으면 확인

- [ ] 13. 검증 스크립트 생성기 구현
  - [ ] 13.1 VerificationScript 데이터 모델 구현
    - `src/bvt_integration/tc_enhancement_models.py`에 추가
    - VerificationScript 데이터클래스 (bvt_no, function_name, code, required_templates, manual_additions)
    - to_dict(), from_dict() 메서드
    - _Requirements: 5.5, 5.7_

  - [ ] 13.2 VerificationScriptGenerator 클래스 구현
    - `src/bvt_integration/verification_script_generator.py` 파일 생성
    - generate() 메서드: BVT check에서 검증 스크립트 생성
    - _generate_visibility_check() 메서드: 요소 존재 확인 코드
    - _generate_touch_transition_check() 메서드: 터치 후 화면 전환 확인 코드
    - _generate_navigation_check() 메서드: 메뉴 이동 확인 코드
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ] 13.3 검증 스크립트 생성기 속성 테스트 작성
    - **Property 6: 검증 스크립트 실행 가능성**
    - 생성된 코드가 유효한 Python 함수인지 검증
    - **Validates: Requirements 5.5**

- [ ] 14. Checkpoint - 검증 스크립트 생성기 검증
  - 모든 테스트 통과 확인
  - 샘플 BVT로 검증 스크립트 생성 테스트
  - 사용자 질문 있으면 확인

### Phase 4: 통합 워크플로우

- [ ] 15. 통합 워크플로우 구현
  - [ ] 15.1 EnhancedWorkflow 클래스 구현
    - `src/bvt_integration/enhanced_workflow.py` 파일 생성
    - run() 메서드: 전체 워크플로우 실행 (BVT 선택 → 템플릿 생성 → 녹화 → 어노테이션 → 매칭 → 검증)
    - resume() 메서드: 중단된 지점에서 재개
    - 진행 상황 추적 및 저장
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 15.2 워크플로우 CLI 인터페이스 구현
    - `src/bvt_integration/enhanced_cli.py` 파일 생성
    - argparse를 사용한 명령줄 인터페이스
    - 주요 명령: generate-template, annotate, match, verify, run-workflow
    - _Requirements: 6.4_

  - [ ] 15.3 워크플로우 설정 관리 구현
    - 프로젝트별 설정 파일 저장/로드
    - 기본 설정 템플릿 제공
    - _Requirements: 6.5_

- [ ] 16. Final Checkpoint - 전체 시스템 검증
  - 모든 테스트 통과 확인
  - 실제 BVT 샘플로 전체 워크플로우 테스트
  - 기존 bvt-semantic-integration과 통합 테스트
  - 사용자 질문 있으면 확인

## Notes

- Phase 1은 즉시 활용 가능한 단기 솔루션으로, 우선 구현
- Phase 2, 3은 Phase 1 완료 후 순차적으로 진행
- 각 Phase는 독립적으로 동작 가능하며, 이전 Phase 결과를 활용
- Property 테스트는 hypothesis 라이브러리 사용, 최소 100회 반복 실행
- 기존 bvt-semantic-integration 모듈과 호환성 유지

