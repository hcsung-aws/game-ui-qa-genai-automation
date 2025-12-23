# Implementation Plan (구현 계획)

본 구현 계획은 Phase 기반으로 점진적으로 개발하며, 각 Phase마다 동작하는 시스템을 만들어 테스트한다.

---

## Phase 1: 기본 기록 및 재실행 (MVP)

- [x] 1. 프로젝트 구조 및 환경 설정





  - 프로젝트 디렉토리 구조 생성
  - requirements.txt 작성 (Phase 1 필수 패키지만)
  - config.json 기본 템플릿 생성
  - _Requirements: 1.4, 10.1_

- [x] 1.1 ConfigManager 구현


  - config.json 로드 기능
  - 기본 설정 생성 기능
  - 중첩 키 접근 기능 (get 메서드)
  - _Requirements: 1.4, 1.5, 10.1_

- [x] 1.2 ConfigManager 테스트 작성






  - **Property 1: 설정 파일 round trip**
  - **Validates: Requirements 1.5**

- [x] 2. GameProcessManager 구현




  - subprocess로 게임 실행
  - 시작 지연 시간 대기
  - 프로세스 상태 확인
  - _Requirements: 1.1, 1.2_

- [x] 2.1 GameProcessManager 테스트 작성





  - 게임 실행 성공 케이스
  - 실행 파일 없음 에러 처리
  - _Requirements: 1.1, 9.1_

- [x] 3. InputMonitor 구현 (pynput)





  - mouse.Listener로 클릭 캡처
  - keyboard.Listener로 키 입력 캡처
  - 모니터링 시작/중지 기능
  - _Requirements: 3.1, 3.2, 3.3, 3.8_

- [x] 3.1 InputMonitor 테스트 작성





  - 클릭 이벤트 캡처 검증
  - 키보드 이벤트 캡처 검증
  - _Requirements: 3.2, 3.3_

- [x] 4. ActionRecorder 구현





  - Action 데이터 클래스 정의
  - 액션 기록 기능
  - 액션 간 시간 간격 계산 및 wait 액션 자동 삽입
  - _Requirements: 3.5, 3.6_

- [x] 4.1 ActionRecorder 테스트 작성



  - **Property 5: 액션 기록 완전성**
  - **Validates: Requirements 3.5**

- [x] 5. ScriptGenerator 구현





  - 기본 Replay Script 템플릿 생성
  - 액션을 Python 코드로 변환
  - UTF-8 인코딩으로 파일 저장
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 5.1 ScriptGenerator 테스트 작성




  - **Property 9: 스크립트 생성 완전성**
  - **Property 11: UTF-8 인코딩 보장**
  - **Validates: Requirements 5.1, 5.4**

- [x] 6. CLIInterface 구현 (Phase 1 명령만)





  - start, record, stop, save, replay, quit 명령
  - 명령어 파싱 및 처리
  - 도움말 표시
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.9, 4.10_

- [x] 6.1 CLIInterface 테스트 작성



  - 각 명령어 처리 검증
  - 유효하지 않은 명령 처리
  - _Requirements: 4.11_

- [x] 7. QAAutomationController 구현 (Phase 1 기능)




  - 모든 컴포넌트 초기화 및 조율
  - start_game, start_recording, stop_recording 메서드
  - save_test_case, replay_test_case 메서드
  - _Requirements: 1.1, 3.1, 3.8, 5.1, 6.1_

- [x] 7.1 Phase 1 통합 테스트 작성







  - 전체 워크플로우 테스트 (기록→저장→재실행)
  - _Requirements: 1.1, 3.1, 5.1, 6.1_

- [x] 8. Phase 1 Manual Test Guide 작성





  - docs/phase1_manual_test.md 작성
  - 테스트 시나리오 및 예상 결과 명시
  - _Requirements: All Phase 1_

- [x] 9. Phase 1 Checkpoint - 모든 테스트 통과 확인





  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 2: UI 분석 통합

- [x] 10. UIAnalyzer 구현





  - AWS Bedrock 클라이언트 초기화
  - 스크린샷 캡처 기능
  - base64 인코딩
  - Vision LLM API 호출
  - JSON 응답 파싱
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7_

- [x] 10.1 UIAnalyzer 테스트 작성






  - **Property 2: 이미지 인코딩 round trip**
  - **Property 3: UI 분석 결과 구조 완전성**
  - **Validates: Requirements 2.2, 2.7**

- [x] 11. UIAnalyzer 재시도 로직 구현





  - 지수 백오프 재시도 (최대 3회)
  - OCR 폴백 (PaddleOCR)
  - _Requirements: 2.5, 2.6_

- [x] 11.1 재시도 로직 테스트 작성






  - **Property 4: Vision LLM 재시도 지수 백오프**
  - **Validates: Requirements 2.5**

- [x] 12. SemanticActionRecorder 구현





  - SemanticAction 데이터 클래스 정의
  - 클릭 전후 스크린샷 캡처
  - UI 요소 분석 (Vision LLM)
  - 의미론적 정보 추출 및 저장
  - _Requirements: 11.1, 11.2, 11.3, 11.6_

- [x] 12.1 SemanticActionRecorder 테스트 작성



  - **Property 28: 의미론적 액션 완전성**
  - **Property 29: 화면 전환 기록**
  - **Validates: Requirements 11.1, 11.6**

- [x] 13. Phase 2 통합 테스트 작성







  - UI 분석 워크플로우 테스트
  - 의미론적 정보 저장 검증
  - _Requirements: 2.1-2.7, 11.1-11.6_

- [x] 14. Phase 2 Manual Test Guide 작성





  - docs/phase2_manual_test.md 작성
  - _Requirements: All Phase 2_

- [x] 15. Phase 2 Checkpoint - 모든 테스트 통과 확인





  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 3: 의미론적 재실행

- [x] 16. SemanticActionReplayer 구현





  - 원래 좌표로 먼저 시도
  - 의미론적 매칭 로직
  - Vision LLM으로 요소 찾기
  - 화면 전환 검증
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.6_

- [x] 16.1 SemanticActionReplayer 테스트 작성



  - **Property 30: 의미론적 매칭 폴백**
  - **Property 31: 화면 전환 검증**
  - **Validates: Requirements 12.1, 12.2, 12.6**

- [x] 17. Phase 3 통합 테스트 작성







  - UI 변경 시나리오 테스트
  - 의미론적 매칭 성공 검증
  - _Requirements: 12.1-12.7_





- [x] 17.1 Phase 3 Property-Based 테스트 작성















  - 버튼 위치 변경에도 찾기 성공
  - _Requirements: 12.2, 12.4_

- [x] 18. Phase 3 Manual Test Guide 작성




  - docs/phase3_manual_test.md 작성
  - UI 변경 후 재실행 시나리오
  - _Requirements: All Phase 3_

- [x] 19. Phase 3 Checkpoint - 모든 테스트 통과 확인





  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 4: 정확도 추적 기본

- [x] 20. AccuracyTracker 구현





  - ActionExecutionResult 데이터 클래스
  - 성공/실패 기록
  - 통계 계산 (성공률, 매칭 방법 비율)
  - 세션 데이터 저장
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_


- [x] 20.1 AccuracyTracker 테스트 작성



  - **Property 32: 정확도 통계 완전성**
  - **Property 33: 액션 실행 결과 기록**
  - **Validates: Requirements 13.2, 13.6**

- [x] 21. CLI에 stats 명령 추가
  - 실행 이력 표시
  - 통계 요약 출력
  - _Requirements: 15.1, 15.2_

- [x] 22. Phase 4 통합 테스트 작성





  - 여러 세션 실행 및 통계 검증
  - _Requirements: 13.1-13.6_

- [x] 23. Phase 4 Manual Test Guide 작성


  - docs/phase4_manual_test.md 작성
  - _Requirements: All Phase 4_

- [x] 24. Phase 4 Checkpoint - 모든 테스트 통과 확인




  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 5: 대화형 오류 표시

- [ ] 25. InteractiveReplayer 구현
  - pause, mark_error 명령 처리
  - 오류 타입 선택
  - Vision LLM으로 재분석
  - 테스트 케이스 업데이트
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

- [ ]* 25.1 InteractiveReplayer 테스트 작성
  - **Property 34: 오류 표시 및 재분석**
  - **Property 35: 테스트 케이스 업데이트**
  - **Validates: Requirements 14.5, 14.7**

- [ ] 26. Phase 5 Manual Test Guide 작성 확인

- [ ] 27. Phase 5 Checkpoint - 모든 테스트 통과 확인
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 6: 통계 시각화

- [ ] 28. AccuracyReporter 구현
  - HTML 템플릿 생성
  - Plotly 그래프 (정확도 추세, 오류 분포)
  - report 명령 추가
  - _Requirements: 15.3, 15.4_

- [ ]* 28.1 AccuracyReporter 테스트 작성
  - **Property 36: 실행 이력 표시**
  - **Property 37: HTML 리포트 생성**
  - **Validates: Requirements 15.1, 15.4**

- [ ] 29. Phase 6 Manual Test Guide 작성
  - docs/phase6_manual_test.md 작성
  - HTML 리포트 검증
  - _Requirements: All Phase 6_

- [ ] 30. Phase 6 Checkpoint - 모든 테스트 통과 확인
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 7: 자동 재학습

- [ ] 31. ActionRetrainer 구현
  - 재학습 후보 찾기 (실패율 30% 이상)
  - 패턴 분석
  - Vision LLM으로 개선된 정보 생성
  - 검증 실행 및 비교
  - retrain 명령 추가
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_

- [ ]* 31.1 ActionRetrainer 테스트 작성
  - **Property 38: 재학습 후보 식별**
  - **Property 39: 패턴 기반 재학습**
  - **Property 40: 재학습 효과 검증**
  - **Validates: Requirements 16.1, 16.4, 16.7**

- [ ] 32. Phase 7 Manual Test Guide 작성
  - docs/phase7_manual_test.md 작성
  - 재학습 시나리오
  - _Requirements: All Phase 7_

- [ ] 33. Phase 7 Checkpoint - 모든 테스트 통과 확인
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 8: 고급 기능 및 최적화

- [ ] 34. 에러 처리 강화
  - 모든 컴포넌트의 에러 처리 개선
  - 로깅 강화
  - _Requirements: 9.1-9.5_

- [ ] 35. 성능 최적화
  - 이미지 크기 최적화
  - Vision LLM 호출 캐싱
  - 메모리 관리
  - _Implementation Notes 참조_

- [ ] 36. End-to-End 테스트 작성
  - 전체 워크플로우 테스트
  - 성능 테스트
  - 스트레스 테스트

- [ ] 37. 문서화 완성
  - README.md 작성
  - API 문서 작성
  - 사용자 가이드 작성

- [ ] 38. Phase 8 Final Checkpoint - 전체 시스템 검증
  - Ensure all tests pass, ask the user if questions arise.
