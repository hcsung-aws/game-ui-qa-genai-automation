# 오차율 측정 및 개선 설계 (Accuracy Tracking & Improvement)

이 문서는 game-qa-automation의 design.md에 추가될 내용입니다.

---

## Accuracy Tracking System (오차율 추적 시스템)

### 개요

테스트 재실행 중 발생하는 모든 성공/실패를 추적하고, 통계를 수집하여 시스템의 정확도를 측정한다.

### AccuracyTracker 컴포넌트

```python
@dataclass
class ActionExecutionResult:
    """액션 실행 결과"""
    action_id: str
    timestamp: str
    success: bool
    method: str  # 'direct', 'semantic', 'manual'
    coordinate_change: tuple = None  # (dx, dy)
    execution_time: float = 0.0
    failure_reason: str = None
    screenshot_path: str = None


class AccuracyTracker:
    """정확도 추적기"""
    
    def __init__(self, test_case_name: str):
        self.test_case_name = test_case_name
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results: List[ActionExecutionResult] = []
        self.start_time = None
        self.end_time = None
    
    def start_session(self):
        """실행 세션 시작"""
        self.start_time = datetime.now()
        logger.info(f"정확도 추적 시작: {self.session_id}")
    
    def record_success(self, action: SemanticAction, method: str, 
                      coordinate_change: tuple = None):
        """성공 기록"""
        result = ActionExecutionResult(
            action_id=action.timestamp,
            timestamp=datetime.now().isoformat(),
            success=True,
            method=method,
            coordinate_change=coordinate_change,
            execution_time=time.time()
        )
        self.results.append(result)
        
        if method == "semantic":
            logger.info(f"✓ 의미론적 매칭 성공 (좌표 변경: {coordinate_change})")
        else:
            logger.info(f"✓ 직접 실행 성공")
    
    def record_failure(self, action: SemanticAction, reason: str):
        """실패 기록"""
        # 스크린샷 저장
        screenshot = pyautogui.screenshot()
        screenshot_path = f"failures/{self.session_id}_{action.timestamp}.png"
        screenshot.save(screenshot_path)
        
        result = ActionExecutionResult(
            action_id=action.timestamp,
            timestamp=datetime.now().isoformat(),
            success=False,
            method="failed",
            failure_reason=reason,
            screenshot_path=screenshot_path
        )
        self.results.append(result)
        logger.error(f"✗ 액션 실패: {reason}")
    
    def end_session(self):
        """실행 세션 종료 및 통계 계산"""
        self.end_time = datetime.now()
        stats = self.calculate_statistics()
        self._save_session_data(stats)
        return stats
    
    def calculate_statistics(self) -> dict:
        """통계 계산"""
        total = len(self.results)
        if total == 0:
            return {}
        
        successes = [r for r in self.results if r.success]
        failures = [r for r in self.results if not r.success]
        
        semantic_matches = [r for r in successes if r.method == "semantic"]
        direct_matches = [r for r in successes if r.method == "direct"]
        
        # 좌표 변경 통계
        coord_changes = [r.coordinate_change for r in semantic_matches 
                        if r.coordinate_change]
        avg_coord_change = 0
        if coord_changes:
            distances = [math.sqrt(dx**2 + dy**2) for dx, dy in coord_changes]
            avg_coord_change = sum(distances) / len(distances)
        
        # 실패 원인 분석
        failure_reasons = {}
        for f in failures:
            reason = f.failure_reason
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        stats = {
            "session_id": self.session_id,
            "test_case": self.test_case_name,
            "total_actions": total,
            "successful_actions": len(successes),
            "failed_actions": len(failures),
            "success_rate": len(successes) / total * 100,
            "direct_match_rate": len(direct_matches) / total * 100,
            "semantic_match_rate": len(semantic_matches) / total * 100,
            "avg_coordinate_change": avg_coord_change,
            "failure_reasons": failure_reasons,
            "duration": (self.end_time - self.start_time).total_seconds()
        }
        
        return stats
    
    def _save_session_data(self, stats: dict):
        """세션 데이터 저장"""
        session_dir = f"accuracy_data/{self.test_case_name}"
        os.makedirs(session_dir, exist_ok=True)
        
        # 통계 저장
        stats_path = f"{session_dir}/{self.session_id}_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        # 상세 결과 저장
        results_path = f"{session_dir}/{self.session_id}_results.json"
        results_data = [asdict(r) for r in self.results]
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
```

---

## Interactive Error Marking (대화형 오류 표시)

### 사용자가 재실행 중 오동작을 표시하는 기능

```python
class InteractiveReplayer:
    """대화형 재실행기"""
    
    def __init__(self, replayer: SemanticActionReplayer, 
                 accuracy_tracker: AccuracyTracker):
        self.replayer = replayer
        self.accuracy_tracker = accuracy_tracker
        self.paused = False
        self.current_action = None
    
    def replay_with_interaction(self, actions: List[SemanticAction]):
        """대화형 재실행"""
        
        for i, action in enumerate(actions):
            self.current_action = action
            
            # 액션 실행
            success = self.replayer.replay_action(action)
            
            # 일시정지 체크
            if self.paused:
                self._handle_pause(action, i, len(actions))
            
            # 실패 시 사용자에게 알림
            if not success:
                choice = self._prompt_on_failure(action)
                if choice == "mark_error":
                    self._mark_and_improve(action)
                elif choice == "skip":
                    continue
                elif choice == "abort":
                    break
    
    def _handle_pause(self, action: SemanticAction, index: int, total: int):
        """일시정지 처리"""
        print(f"\n=== 일시정지 ({index + 1}/{total}) ===")
        print(f"액션: {action.semantic_info['intent']}")
        print(f"좌표: ({action.x}, {action.y})")
        print(f"설명: {action.semantic_info['target_element']['description']}")
        
        while self.paused:
            cmd = input("\n명령 (continue/mark_error/screenshot/quit)> ").strip()
            
            if cmd == "continue":
                self.paused = False
            elif cmd == "mark_error":
                self._mark_and_improve(action)
                self.paused = False
            elif cmd == "screenshot":
                screenshot = pyautogui.screenshot()
                screenshot.save(f"debug_{action.timestamp}.png")
                print("✓ 스크린샷 저장됨")
            elif cmd == "quit":
                raise KeyboardInterrupt("사용자가 중단함")
```

    def _mark_and_improve(self, action: SemanticAction):
        """오류 표시 및 개선"""
        print("\n=== 오류 타입 선택 ===")
        print("1. 잘못된 요소 클릭")
        print("2. 요소를 찾지 못함")
        print("3. 예상과 다른 결과")
        print("4. 타이밍 문제")
        
        error_type = input("오류 타입 (1-4)> ").strip()
        
        # 현재 화면 분석
        current_screen = pyautogui.screenshot()
        
        # Vision LLM으로 재분석
        print("\n재분석 중...")
        improved_info = self._reanalyze_action(action, current_screen, error_type)
        
        print("\n=== 개선된 액션 정보 ===")
        print(json.dumps(improved_info, indent=2, ensure_ascii=False))
        
        choice = input("\n이 정보로 업데이트하시겠습니까? (y/n)> ").strip()
        if choice.lower() == 'y':
            action.semantic_info.update(improved_info)
            print("✓ 액션 정보 업데이트됨")
    
    def _reanalyze_action(self, action: SemanticAction, 
                         current_screen, error_type: str) -> dict:
        """액션 재분석"""
        
        original_info = action.semantic_info
        
        prompt = f"""
        이전에 기록된 액션 정보:
        {json.dumps(original_info, ensure_ascii=False)}
        
        오류 타입: {error_type}
        
        현재 화면에서 이 액션의 의도를 달성할 수 있는 요소를 찾아주세요.
        더 강건한 식별 정보를 제공해주세요.
        
        JSON 형식으로 반환:
        {{
            "target_element": {{
                "type": "...",
                "text": "...",
                "alternative_texts": ["유사한 텍스트들"],
                "visual_features": {{...}},
                "position_hints": ["위치 힌트들"]
            }},
            "fallback_strategies": ["대체 전략들"]
        }}
        """
        
        result = self.replayer.ui_analyzer.analyze_with_vision_llm(
            current_screen,
            prompt
        )
        return json.loads(result)

---

## Statistics Visualization (통계 시각화)

### AccuracyReporter 컴포넌트

```python
class AccuracyReporter:
    """정확도 리포터"""
    
    def __init__(self, test_case_name: str):
        self.test_case_name = test_case_name
        self.data_dir = f"accuracy_data/{test_case_name}"
    
    def show_statistics(self):
        """통계 표시"""
        sessions = self._load_all_sessions()
        
        if not sessions:
            print("실행 이력이 없습니다.")
            return
        
        print(f"\n=== {self.test_case_name} 실행 이력 ===\n")
        print(f"{'날짜':<20} {'성공률':<10} {'오류 수':<10} {'의미론적 매칭':<15}")
        print("-" * 60)
        
        for session in sessions:
            date = session['session_id']
            success_rate = f"{session['success_rate']:.1f}%"
            failures = session['failed_actions']
            semantic_rate = f"{session['semantic_match_rate']:.1f}%"
            
            print(f"{date:<20} {success_rate:<10} {failures:<10} {semantic_rate:<15}")
        
        # 추세 분석
        self._show_trend_analysis(sessions)
    
    def generate_html_report(self, output_path: str = None):
        """HTML 리포트 생성"""
        sessions = self._load_all_sessions()
        
        if not sessions:
            print("실행 이력이 없습니다.")
            return
        
        html = self._generate_html_template(sessions)
        
        if output_path is None:
            output_path = f"reports/{self.test_case_name}_report.html"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ HTML 리포트 생성: {output_path}")
    
    def _generate_html_template(self, sessions: list) -> str:
        """HTML 템플릿 생성"""
        
        # 정확도 추세 데이터
        dates = [s['session_id'] for s in sessions]
        success_rates = [s['success_rate'] for s in sessions]
        
        # 오류 타입 분포
        all_failures = {}
        for session in sessions:
            for reason, count in session.get('failure_reasons', {}).items():
                all_failures[reason] = all_failures.get(reason, 0) + count
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.test_case_name} - 정확도 리포트</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .chart {{ margin: 30px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>{self.test_case_name} 정확도 리포트</h1>
    
    <h2>정확도 추세</h2>
    <div id="trend-chart" class="chart"></div>
    
    <h2>오류 타입 분포</h2>
    <div id="error-chart" class="chart"></div>
    
    <h2>실행 이력</h2>
    <table>
        <tr>
            <th>날짜</th>
            <th>성공률</th>
            <th>총 액션</th>
            <th>성공</th>
            <th>실패</th>
            <th>의미론적 매칭</th>
        </tr>
        {''.join([f'''
        <tr>
            <td>{s['session_id']}</td>
            <td>{s['success_rate']:.1f}%</td>
            <td>{s['total_actions']}</td>
            <td>{s['successful_actions']}</td>
            <td>{s['failed_actions']}</td>
            <td>{s['semantic_match_rate']:.1f}%</td>
        </tr>
        ''' for s in sessions])}
    </table>
    
    <script>
        // 정확도 추세 그래프
        var trendData = [{{
            x: {dates},
            y: {success_rates},
            type: 'scatter',
            mode: 'lines+markers',
            name: '성공률'
        }}];
        
        var trendLayout = {{
            title: '시간에 따른 성공률 변화',
            xaxis: {{ title: '날짜' }},
            yaxis: {{ title: '성공률 (%)' }}
        }};
        
        Plotly.newPlot('trend-chart', trendData, trendLayout);
        
        // 오류 타입 분포 그래프
        var errorData = [{{
            labels: {list(all_failures.keys())},
            values: {list(all_failures.values())},
            type: 'pie'
        }}];
        
        var errorLayout = {{
            title: '오류 타입별 분포'
        }};
        
        Plotly.newPlot('error-chart', errorData, errorLayout);
    </script>
</body>
</html>
        """
        
        return html
```

---

## Automatic Retraining (자동 재학습)

### ActionRetrainer 컴포넌트

```python
class ActionRetrainer:
    """액션 재학습기"""
    
    def __init__(self, test_case_manager: TestCaseManager,
                 ui_analyzer: UIAnalyzer):
        self.test_case_manager = test_case_manager
        self.ui_analyzer = ui_analyzer
    
    def find_retraining_candidates(self, test_case_name: str) -> list:
        """재학습 후보 찾기"""
        sessions = self._load_sessions(test_case_name)
        
        # 액션별 실패율 계산
        action_stats = {}
        for session in sessions:
            for result in session['results']:
                action_id = result['action_id']
                if action_id not in action_stats:
                    action_stats[action_id] = {
                        'total': 0,
                        'failures': 0,
                        'failure_reasons': []
                    }
                
                action_stats[action_id]['total'] += 1
                if not result['success']:
                    action_stats[action_id]['failures'] += 1
                    action_stats[action_id]['failure_reasons'].append(
                        result['failure_reason']
                    )
        
        # 실패율 30% 이상인 액션 찾기
        candidates = []
        for action_id, stats in action_stats.items():
            failure_rate = stats['failures'] / stats['total']
            if failure_rate >= 0.3:
                candidates.append({
                    'action_id': action_id,
                    'failure_rate': failure_rate * 100,
                    'total_executions': stats['total'],
                    'failures': stats['failures'],
                    'common_reasons': self._get_common_reasons(
                        stats['failure_reasons']
                    )
                })
        
        return sorted(candidates, key=lambda x: x['failure_rate'], reverse=True)
```
