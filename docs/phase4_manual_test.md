# Phase 4 수동 테스트 가이드

## 목적

Phase 4에서는 테스트 재실행의 정확도를 추적하고 통계를 표시하는 기능을 검증한다.

### 핵심 기능
- 새 실행 세션 생성 (Requirements 13.1)
- 액션 성공/실패 기록 (Requirements 13.2)
- 의미론적 매칭 시 좌표 변경 기록 (Requirements 13.3)
- 화면 전환 검증 기록 (Requirements 13.4)
- 전체 정확도 통계 계산 (Requirements 13.5, 13.6)
- CLI stats 명령으로 실행 이력 표시 (Requirements 15.1, 15.2)

## 준비사항

- [ ] Python 3.8+ 설치
- [ ] 필요한 패키지 설치: `pip install -r requirements.txt`
- [ ] config.json 설정 확인
- [ ] accuracy_data 디렉토리 존재 확인

## 테스트 시나리오 1: 기본 정확도 추적

### 목적
AccuracyTracker가 액션 실행 결과를 올바르게 기록하는지 확인

### 단계
1. Python 인터프리터 실행

```python
from src.accuracy_tracker import AccuracyTracker

# 트래커 생성
tracker = AccuracyTracker("manual_test_case")
print(f"세션 ID: {tracker.get_session_id()}")
```

2. 성공 결과 기록
```python
# 직접 매칭 성공
result1 = tracker.record_success(
    action_id="action_001",
    method='direct',
    original_coords=(100, 200),
    actual_coords=(100, 200),
    execution_time=0.5
)
print(f"성공 기록: {result1.action_id}, method={result1.method}")

# 의미론적 매칭 성공 (좌표 변경)
result2 = tracker.record_success(
    action_id="action_002",
    method='semantic',
    original_coords=(100, 100),
    actual_coords=(300, 250),
    execution_time=1.5
)
print(f"좌표 변경: {result2.coordinate_change}")
```

3. 실패 결과 기록
```python
result3 = tracker.record_failure(
    action_id="action_003",
    reason='element_not_found',
    original_coords=(500, 500),
    execution_time=2.0
)
print(f"실패 기록: {result3.action_id}, reason={result3.failure_reason}")
```

4. 통계 확인
```python
stats = tracker.calculate_statistics()
print(f"총 액션: {stats.total_actions}")
print(f"성공률: {stats.success_rate * 100:.1f}%")
print(f"직접 매칭: {stats.direct_match_count}")
print(f"의미론적 매칭: {stats.semantic_match_count}")
print(f"평균 좌표 변경: {stats.avg_coordinate_change:.1f}")
```

### 예상 결과
- 총 액션: 3
- 성공률: 66.7%
- 직접 매칭: 1
- 의미론적 매칭: 1
- 평균 좌표 변경: > 0

---

## 테스트 시나리오 2: 세션 저장 및 로드

### 목적
세션 데이터가 올바르게 저장되고 로드되는지 확인

### 단계
1. 세션 저장
```python
saved_path = tracker.save_session()
print(f"저장 경로: {saved_path}")
```

2. 새 트래커로 세션 로드
```python
session_id = tracker.get_session_id()
tracker2 = AccuracyTracker("manual_test_case")
success = tracker2.load_session(session_id)
print(f"로드 성공: {success}")
print(f"로드된 결과 수: {len(tracker2.get_results())}")
```

### 예상 결과
- 저장 경로: accuracy_data/manual_test_case/{session_id}_results.json
- 로드 성공: True
- 로드된 결과 수: 3

---

## 테스트 시나리오 3: 여러 세션 실행 및 이력 조회

### 목적
여러 세션의 실행 이력이 올바르게 조회되는지 확인

### 단계
1. 추가 세션 생성 및 저장
```python
import time

# 두 번째 세션
tracker3 = AccuracyTracker("manual_test_case")
tracker3.start_session()

for i in range(5):
    tracker3.record_success(
        action_id=f"action_{i}",
        method='direct',
        original_coords=(100, 100),
        actual_coords=(100, 100),
        execution_time=0.3
    )

tracker3.save_session()
time.sleep(0.1)

# 세 번째 세션
tracker4 = AccuracyTracker("manual_test_case")
tracker4.start_session()

for i in range(3):
    tracker4.record_success(
        action_id=f"action_{i}",
        method='semantic',
        original_coords=(100, 100),
        actual_coords=(200, 200),
        execution_time=1.0
    )

for i in range(2):
    tracker4.record_failure(
        action_id=f"fail_{i}",
        reason='timeout',
        original_coords=(300, 300),
        execution_time=2.0
    )

tracker4.save_session()
```

2. 세션 목록 조회
```python
tracker5 = AccuracyTracker("manual_test_case")
sessions = tracker5.list_sessions()

print(f"\n총 {len(sessions)}개 세션:")
for s in sessions:
    print(f"  - {s['session_id']}: 성공률 {s['success_rate']*100:.1f}%, "
          f"오류 {s['failure_count']}개")
```

### 예상 결과
- 3개 이상의 세션이 표시됨
- 각 세션에 session_id, timestamp, success_rate, failure_count 포함

---

## 테스트 시나리오 4: CLI stats 명령

### 목적
CLI에서 stats 명령이 올바르게 동작하는지 확인

### 단계
1. 시스템 시작
```bash
python main.py
```

2. 테스트 케이스 로드 (기존 테스트 케이스가 있는 경우)
```
> load <테스트_케이스_이름>
```

3. stats 명령 실행
```
> stats
```

또는 특정 테스트 케이스 지정:
```
> stats manual_test_case
```

### 예상 결과
```
============================================================
  테스트 케이스: manual_test_case
============================================================

[실행 이력]
------------------------------------------------------------
날짜/시간               성공률    오류   의미론적 매칭
------------------------------------------------------------
2025-12-23 10:00:00      80.0%      1         20.0%
2025-12-23 09:30:00     100.0%      0          0.0%
2025-12-23 09:00:00      66.7%      1         33.3%
------------------------------------------------------------

[통계 요약]
  총 실행 횟수: 3회
  평균 성공률: 82.2%
  총 오류 수: 2개
  평균 의미론적 매칭률: 17.8%

[최근 실행]
  시간: 2025-12-23 10:00:00
  성공률: 80.0%
  성공: 4개 / 실패: 1개
```

---

## 테스트 시나리오 5: 액션별 실패율 분석

### 목적
특정 액션의 실패율을 분석하여 재학습 후보를 식별할 수 있는지 확인

### 단계
1. 실패율 조회
```python
tracker = AccuracyTracker("manual_test_case")
failure_rates = tracker.get_failure_rate_by_action()

print("\n액션별 실패율:")
for action_id, rate in sorted(failure_rates.items(), 
                               key=lambda x: x[1], reverse=True):
    print(f"  {action_id}: {rate*100:.1f}%")
    if rate >= 0.3:
        print(f"    ⚠ 재학습 후보 (실패율 30% 이상)")
```

### 예상 결과
- 각 액션의 실패율이 표시됨
- 실패율 30% 이상인 액션에 경고 표시

---

## 테스트 시나리오 6: 특정 액션 이력 조회

### 목적
특정 액션의 실행 이력을 조회하여 패턴을 분석할 수 있는지 확인

### 단계
```python
tracker = AccuracyTracker("manual_test_case")
history = tracker.get_action_history("action_001")

print(f"\naction_001 실행 이력 ({len(history)}회):")
for h in history:
    status = "성공" if h.success else "실패"
    print(f"  - {h.timestamp}: {status}, method={h.method}")
```

### 예상 결과
- 해당 액션의 모든 실행 이력이 표시됨
- 각 실행의 성공/실패, 매칭 방법 확인 가능

---

## 체크리스트

### 기능 검증
- [ ] 새 세션 생성 시 고유한 세션 ID 생성됨
- [ ] 성공 결과가 올바르게 기록됨
- [ ] 실패 결과가 올바르게 기록됨
- [ ] 좌표 변경이 올바르게 계산됨
- [ ] 화면 전환 일치/불일치가 기록됨
- [ ] 통계가 올바르게 계산됨
- [ ] 세션이 JSON 파일로 저장됨
- [ ] 저장된 세션이 올바르게 로드됨
- [ ] 세션 목록이 올바르게 조회됨
- [ ] CLI stats 명령이 정상 동작함

### 통계 검증
- [ ] 성공률이 0.0 ~ 1.0 범위 내
- [ ] 직접 매칭률 + 의미론적 매칭률 ≤ 1.0
- [ ] 평균 좌표 변경 거리 ≥ 0
- [ ] 실패 원인 분포가 올바름

### 엣지 케이스
- [ ] 빈 트래커의 통계가 0으로 반환됨
- [ ] 모두 성공 시 성공률 100%
- [ ] 모두 실패 시 성공률 0%
- [ ] 존재하지 않는 세션 로드 시 False 반환

---

## 문제 발생 시

### 세션 저장 실패
- accuracy_data 디렉토리 존재 확인
- 디렉토리 쓰기 권한 확인

### 통계 계산 오류
- 결과가 비어있지 않은지 확인
- 각 결과의 필수 필드 확인

### CLI stats 명령 오류
- 테스트 케이스가 로드되었는지 확인
- accuracy_data/{test_case_name}/ 디렉토리에 세션 파일 존재 확인

---

## 다음 단계

Phase 4 테스트가 완료되면:
1. Phase 5 (대화형 오류 표시) 진행
2. pause, mark_error 명령 구현
3. 오류 재분석 및 테스트 케이스 업데이트 기능 구현
