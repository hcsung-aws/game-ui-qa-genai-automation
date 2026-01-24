# Implementation Plan: BVT-Semantic Test Integration

## Overview

BVT 테스트 데이터와 의미론적 테스트 케이스를 연결하는 자동화 QA 파이프라인을 구현한다. Clean Architecture 원칙에 따라 계층별로 구현하며, 각 컴포넌트는 단일 책임을 가지고 느슨하게 결합된다.

## Tasks

- [x] 1. 데이터 모델 및 기본 구조 설정
  - [x] 1.1 데이터 모델 클래스 생성
    - `src/bvt_integration/models.py` 파일 생성
    - BVTTestCase, ActionSummary, SemanticSummary, ActionRange, MatchResult, BVTReference, PlayTestCase, PlayTestResult, TestStatus, MatchingReport, PipelineResult 데이터클래스 구현
    - 각 클래스에 to_dict(), from_dict() 메서드 구현
    - _Requirements: 1.1, 1.2, 2.4, 3.1, 4.1, 5.1, 6.1_

  - [x] 1.2 데이터 모델 round-trip 속성 테스트 작성
    - **Property 2: BVT_Test_Case round-trip**
    - **Property 4: Semantic_Test_Case round-trip**
    - **Property 11: Play_Test_Case round-trip**
    - **Validates: Requirements 1.5, 2.7, 4.8**

- [x] 2. BVT 파싱 계층 구현
  - [x] 2.1 BVTParser 클래스 구현
    - `src/bvt_integration/bvt_parser.py` 파일 생성
    - parse() 메서드: CSV 파일 파싱, 헤더/요약 행 건너뛰기
    - write() 메서드: BVT_Test_Case 리스트를 CSV로 저장
    - BVTParseError 예외 클래스 정의
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 2.2 BVT 파싱 속성 테스트 작성
    - **Property 1: BVT 파싱 정확성**
    - **Property 14: BVT 파일 round-trip**
    - **Validates: Requirements 1.1, 1.2, 5.5, 5.7**

- [x] 3. 테스트 케이스 로딩 및 요약 계층 구현
  - [x] 3.1 SemanticTestCaseLoader 클래스 구현
    - `src/bvt_integration/tc_loader.py` 파일 생성
    - load_file() 메서드: 단일 JSON 파일 로드
    - load_directory() 메서드: 디렉토리 내 모든 JSON 파일 로드
    - 잘못된 파일 건너뛰기 및 로깅
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.2 SemanticSummaryGenerator 클래스 구현
    - `src/bvt_integration/summary_generator.py` 파일 생성
    - generate() 메서드: 테스트 케이스 리스트로부터 SemanticSummary 생성
    - extract_action_summary() 메서드: 단일 테스트 케이스의 ActionSummary 추출
    - intent, target_element, context 정보 종합
    - _Requirements: 2.4, 2.5, 2.6_

  - [x] 3.3 요약 생성 속성 테스트 작성
    - **Property 3: Semantic_Summary 생성 정확성**
    - **Validates: Requirements 2.1, 2.4, 2.5, 2.6**

- [x] 4. Checkpoint - 파싱 및 요약 계층 검증
  - 모든 테스트 통과 확인
  - 사용자 질문 있으면 확인

- [ ] 5. 매칭 분석 계층 구현
  - [ ] 5.1 TextSimilarityCalculator 클래스 구현
    - `src/bvt_integration/text_similarity.py` 파일 생성
    - calculate() 메서드: 두 텍스트 간 유사도 계산 (Jaccard 유사도 + 부분 문자열 매칭)
    - calculate_with_context() 메서드: Category 계층 고려한 유사도 계산
    - _Requirements: 3.2, 3.3_

  - [ ] 5.2 텍스트 유사도 속성 테스트 작성
    - **Property 6: 텍스트 유사도 계산 정확성**
    - **Validates: Requirements 3.2, 3.3**

  - [ ] 5.3 MatchingAnalyzer 클래스 구현
    - `src/bvt_integration/matching_analyzer.py` 파일 생성
    - analyze() 메서드: BVT 케이스와 SemanticSummary 비교 분석
    - find_matching_actions() 메서드: BVT 항목에 해당하는 액션 범위 찾기
    - 신뢰도 점수 계산 및 고신뢰도 판정 (>= 0.7)
    - 결과 정렬 (신뢰도 내림차순)
    - _Requirements: 3.1, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

  - [ ] 5.4 매칭 분석 속성 테스트 작성
    - **Property 5: Match_Result 구조 정확성**
    - **Property 7: 고신뢰도 임계값 일관성**
    - **Property 8: 매칭 결과 정렬**
    - **Property 9: 매칭 분석 결정론성**
    - **Validates: Requirements 3.1, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**

- [ ] 6. Checkpoint - 매칭 분석 계층 검증
  - 모든 테스트 통과 확인
  - 사용자 질문 있으면 확인

- [ ] 7. 플레이 테스트 생성 계층 구현
  - [ ] 7.1 AutoPlayGenerator 클래스 구현
    - `src/bvt_integration/auto_play_generator.py` 파일 생성
    - generate() 메서드: MatchResult로부터 PlayTestCase 생성
    - execute() 메서드: PlayTestCase 실행 (SemanticActionReplayer 활용)
    - 액션 범위 추출 및 BVT 참조 정보 포함
    - 실행 중 실패 처리 및 로깅
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [ ] 7.2 플레이 테스트 생성 속성 테스트 작성
    - **Property 10: Play_Test_Case 생성 정확성**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.7**

- [ ] 8. BVT 업데이트 및 리포트 계층 구현
  - [ ] 8.1 BVTUpdater 클래스 구현
    - `src/bvt_integration/bvt_updater.py` 파일 생성
    - update() 메서드: 테스트 결과를 BVT 케이스에 반영
    - save() 메서드: 업데이트된 BVT를 타임스탬프 포함 파일로 저장
    - PASS/Fail 상태 설정 및 Comment 업데이트
    - BTS ID 보존
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ] 8.2 BVT 업데이트 속성 테스트 작성
    - **Property 12: BVT 업데이트 정확성**
    - **Property 13: BTS ID 보존**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

  - [ ] 8.3 ReportGenerator 클래스 구현
    - `src/bvt_integration/report_generator.py` 파일 생성
    - generate() 메서드: MatchResult 리스트로부터 MatchingReport 생성
    - to_json() 메서드: JSON 형식 출력
    - to_markdown() 메서드: Markdown 형식 출력
    - 통계 계산 (total, matched, unmatched, coverage)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ] 8.4 리포트 생성 속성 테스트 작성
    - **Property 15: 리포트 구조 정확성**
    - **Property 16: 커버리지 계산 정확성**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

- [ ] 9. Checkpoint - 업데이트 및 리포트 계층 검증
  - 모든 테스트 통과 확인
  - 사용자 질문 있으면 확인

- [ ] 10. 통합 파이프라인 구현
  - [ ] 10.1 IntegrationPipeline 클래스 구현
    - `src/bvt_integration/pipeline.py` 파일 생성
    - run() 메서드: 전체 파이프라인 실행 (파싱 → 로드 → 요약 → 매칭 → 생성 → 실행 → 업데이트)
    - dry_run 모드 지원 (분석만 수행)
    - progress_callback 지원
    - 단계별 실패 처리 및 부분 결과 반환
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ] 10.2 파이프라인 단위 테스트 작성
    - dry-run 모드 동작 테스트
    - 진행 콜백 호출 테스트
    - 단계별 실패 처리 테스트
    - _Requirements: 7.2, 7.3, 7.4_

- [ ] 11. 모듈 통합 및 패키지 구성
  - [ ] 11.1 패키지 초기화 파일 생성
    - `src/bvt_integration/__init__.py` 파일 생성
    - 주요 클래스 및 함수 export
    - 버전 정보 포함

  - [ ] 11.2 CLI 인터페이스 구현
    - `src/bvt_integration/cli.py` 파일 생성
    - argparse를 사용한 명령줄 인터페이스
    - 주요 옵션: --bvt-path, --test-cases-dir, --output-dir, --dry-run
    - _Requirements: 7.1, 7.3_

- [ ] 12. Final Checkpoint - 전체 시스템 검증
  - 모든 테스트 통과 확인
  - 실제 BVT 샘플 파일로 통합 테스트 수행
  - 사용자 질문 있으면 확인

## Notes

- 모든 태스크는 필수로 구현해야 함 (테스트 포함)
- 각 태스크는 특정 요구사항을 참조하여 추적 가능성 확보
- Checkpoint 태스크에서 증분 검증 수행
- Property 테스트는 hypothesis 라이브러리 사용, 최소 100회 반복 실행
