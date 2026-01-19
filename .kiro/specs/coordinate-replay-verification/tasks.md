# 구현 계획: 좌표 기반 Replay 검증 기능

## 개요

좌표 기반 테스트 replay에서 검증 기능을 활성화하여 테스트 성공/실패 여부를 판단하고 보고서를 생성하는 기능을 구현한다.

## Tasks

- [x] 1. ScriptGenerator에 검증 모드 추가
  - [x] 1.1 `replay_with_verification()` 메서드 구현
    - verify 파라미터로 검증 활성화 여부 제어
    - ReplayVerifier 인스턴스 생성 및 세션 시작
    - 각 액션 실행 후 검증 수행
    - 보고서 생성 및 저장
    - _Requirements: 1.1, 1.2, 2.1, 2.5_
  - [x] 1.2 `_execute_action_with_verification()` 메서드 구현
    - 액션 실행 후 현재 화면 캡처
    - ReplayVerifier.capture_and_verify() 호출
    - 검증 실패 시에도 다음 액션 계속 실행
    - _Requirements: 1.2, 4.1_
  - [x] 1.3 Property test: 실패 시 계속 실행
    - **Property 5: 실패 시 계속 실행**
    - **Validates: Requirements 4.1**

- [x] 2. ReplayVerifier 확장
  - [x] 2.1 `verify_coordinate_action()` 메서드 구현
    - semantic_info 없는 액션에 대해 screenshot_path만으로 검증
    - screenshot_path 없으면 warning 처리
    - _Requirements: 3.1, 3.2_
  - [x] 2.2 `determine_test_result()` 메서드 구현
    - 하나라도 fail이 있으면 False 반환
    - 모두 pass 또는 warning이면 True 반환
    - _Requirements: 4.3_
  - [x] 2.3 Property test: 검증 결과와 유사도 임계값의 일관성
    - **Property 1: 검증 결과와 유사도 임계값의 일관성**
    - **Validates: Requirements 1.4, 1.5, 4.4**
  - [x] 2.4 Property test: 전체 테스트 결과 판정
    - **Property 6: 전체 테스트 결과 판정**
    - **Validates: Requirements 4.3**

- [x] 3. Checkpoint - 핵심 검증 로직 완료
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. 보고서 생성 및 저장 기능 강화
  - [x] 4.1 보고서 카운트 계산 로직 검증
    - passed_count + failed_count + warning_count == total_actions 보장
    - success_rate 계산 정확성 확인
    - _Requirements: 2.1, 2.3_
  - [x] 4.2 JSON 및 TXT 형식 보고서 저장 확인
    - 두 형식 모두 저장되는지 확인
    - 지정된 디렉토리에 저장되는지 확인
    - _Requirements: 2.5_
  - [x] 4.3 Property test: 보고서 카운트 정확성
    - **Property 2: 보고서 카운트 정확성**
    - **Validates: Requirements 2.1, 2.3**
  - [x] 4.4 Property test: 검증 결과 직렬화 Round-trip
    - **Property 4: 검증 결과 직렬화 Round-trip**
    - **Validates: Requirements 2.5, 6.4**

- [x] 5. 데이터 구조 완전성 확인
  - [x] 5.1 VerificationResult 필수 필드 확인
    - action_index, final_result, screenshot_similarity, vision_match 필드 존재 확인
    - _Requirements: 6.2_
  - [x] 5.2 ReplayReport 필수 필드 확인
    - total_actions, passed_count, failed_count, warning_count, success_rate 필드 존재 확인
    - _Requirements: 6.3_
  - [x] 5.3 Property test: 데이터 구조 필수 필드 존재
    - **Property 9: 데이터 구조 필수 필드 존재**
    - **Validates: Requirements 6.2, 6.3**
  - [x] 5.4 Property test: 보고서 완전성
    - **Property 3: 보고서 완전성**
    - **Validates: Requirements 2.2, 6.2**

- [x] 6. Checkpoint - 보고서 기능 완료
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. CLI 인터페이스 확장
  - [x] 7.1 `--verify` 옵션 추가
    - replay 명령어에 --verify 옵션 파싱 추가
    - 검증 모드 활성화 로직 연결
    - _Requirements: 5.1_
  - [x] 7.2 `--report-dir` 옵션 추가
    - 보고서 저장 디렉토리 지정 옵션
    - 기본값은 "reports"
    - _Requirements: 5.5_
  - [x] 7.3 종료 코드 반환 로직 구현
    - 테스트 성공 시 종료 코드 0
    - 테스트 실패 시 종료 코드 1
    - _Requirements: 5.3, 5.4_
  - [x] 7.4 테스트 결과 요약 콘솔 출력
    - replay 완료 후 결과 요약 출력
    - _Requirements: 5.2_
  - [x] 7.5 Property test: 종료 코드와 테스트 결과의 일관성
    - **Property 7: 종료 코드와 테스트 결과의 일관성**
    - **Validates: Requirements 5.3, 5.4**

- [x] 8. 기존 테스트 케이스 호환성 처리
  - [x] 8.1 semantic_info 없는 액션 처리
    - screenshot_path 필드만으로 검증 수행
    - _Requirements: 3.1_
  - [x] 8.2 screenshot_path 없는 액션 warning 처리
    - 검증 건너뛰고 warning으로 기록
    - _Requirements: 3.2_
  - [x] 8.3 혼합 테스트 케이스 처리
    - 각 액션 타입에 맞는 검증 방식 적용
    - _Requirements: 3.3_
  - [x] 8.4 Property test: screenshot_path 없는 액션의 warning 처리
    - **Property 8: screenshot_path 없는 액션의 warning 처리**
    - **Validates: Requirements 3.2**

- [x] 9. Final Checkpoint - 전체 기능 완료
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- 모든 태스크는 필수이며, property test를 포함하여 철저한 검증을 수행
- 기존 `ReplayVerifier`의 `capture_and_verify()` 메서드를 최대한 활용
- Python의 Hypothesis 라이브러리를 사용하여 property-based testing 수행
- 각 property test는 최소 100회 반복 실행
