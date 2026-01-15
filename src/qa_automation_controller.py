"""
QAAutomationController - QA 자동화 컨트롤러

전체 시스템을 조율하는 메인 컨트롤러.
모든 컴포넌트를 초기화하고 조율한다.

Requirements: 1.1, 3.1, 3.8, 5.1, 6.1, 15.1, 15.2
"""

import os
import json
import subprocess
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from src.config_manager import ConfigManager
from src.game_process_manager import GameProcessManager
from src.input_monitor import InputMonitor, ActionRecorder, Action
from src.script_generator import ScriptGenerator
from src.accuracy_tracker import AccuracyTracker, AccuracyStatistics
from src.test_case_enricher import TestCaseEnricher, EnrichmentResult
from src.ui_analyzer import UIAnalyzer


class QAAutomationController:
    """QA 자동화 컨트롤러
    
    게임 QA 자동화 시스템의 모든 컴포넌트를 초기화하고 조율한다.
    """
    
    def __init__(self, config_path: str = 'config.json'):
        """
        Args:
            config_path: 설정 파일 경로
        """
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.game_manager: Optional[GameProcessManager] = None
        self.action_recorder: Optional[ActionRecorder] = None
        self.input_monitor: Optional[InputMonitor] = None
        self.script_generator: Optional[ScriptGenerator] = None
        self.accuracy_tracker: Optional[AccuracyTracker] = None
        self.ui_analyzer: Optional[UIAnalyzer] = None
        self.test_case_enricher: Optional[TestCaseEnricher] = None
        self.current_test_case: Optional[dict] = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """시스템 초기화
        
        설정을 로드하고 필요한 컴포넌트를 초기화한다.
        
        Returns:
            성공 여부
        """
        try:
            # 설정 로드 (없으면 기본 설정 생성)
            if os.path.exists(self.config_path):
                self.config_manager.load_config()
            else:
                print(f"설정 파일이 없습니다. 기본 설정을 생성합니다: {self.config_path}")
                self.config_manager.create_default_config()
            
            # 필요한 디렉토리 생성
            screenshot_dir = self.config_manager.get('automation.screenshot_dir', 'screenshots')
            test_cases_dir = self.config_manager.get('test_cases.directory', 'test_cases')
            
            os.makedirs(screenshot_dir, exist_ok=True)
            os.makedirs(test_cases_dir, exist_ok=True)
            
            # 컴포넌트 초기화
            self.game_manager = GameProcessManager(self.config_manager)
            self.action_recorder = ActionRecorder(self.config_manager)
            self.input_monitor = InputMonitor(self.action_recorder)
            self.script_generator = ScriptGenerator(self.config_manager)
            self.ui_analyzer = UIAnalyzer(self.config_manager)
            self.test_case_enricher = TestCaseEnricher(self.config_manager, self.ui_analyzer)
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"초기화 실패: {e}")
            return False
    
    def _ensure_initialized(self):
        """초기화 확인 및 자동 초기화"""
        if not self._initialized:
            self.initialize()
    
    def start_game(self) -> bool:
        """게임 시작 (Requirements 1.1)
        
        Returns:
            성공 여부
        """
        self._ensure_initialized()
        return self.game_manager.start_game()
    
    def start_recording(self):
        """입력 기록 시작 (Requirements 3.1)
        
        pynput을 사용하여 마우스와 키보드 입력 모니터링을 시작한다.
        """
        self._ensure_initialized()
        self.action_recorder.clear_actions()
        self.input_monitor.start_monitoring()
    
    def stop_recording(self):
        """입력 기록 중지 (Requirements 3.8)
        
        입력 모니터링을 중지한다.
        """
        self._ensure_initialized()
        self.input_monitor.stop_monitoring()
    
    def get_actions(self) -> List[Action]:
        """기록된 액션 목록 반환
        
        Returns:
            액션 리스트
        """
        self._ensure_initialized()
        return self.action_recorder.get_actions()
    
    def save_test_case(self, name: str) -> dict:
        """테스트 케이스 저장 (Requirements 5.1)
        
        기록된 액션을 테스트 케이스로 저장하고 Replay Script를 생성한다.
        
        Args:
            name: 테스트 케이스 이름
            
        Returns:
            저장된 테스트 케이스 정보
        """
        self._ensure_initialized()
        
        actions = self.action_recorder.get_actions()
        if not actions:
            raise ValueError("저장할 액션이 없습니다. 먼저 'record' 명령으로 액션을 기록하세요.")
        
        test_cases_dir = self.config_manager.get('test_cases.directory', 'test_cases')
        os.makedirs(test_cases_dir, exist_ok=True)
        
        # 파일 경로 설정
        script_path = os.path.join(test_cases_dir, f"{name}.py")
        json_path = os.path.join(test_cases_dir, f"{name}.json")
        
        # Replay Script 생성
        self.script_generator.generate_replay_script(actions, script_path)
        
        # 액션 데이터를 JSON으로 저장
        test_case_data = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "script_path": script_path,
            "json_path": json_path,
            "actions": [self._action_to_dict(action) for action in actions]
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(test_case_data, f, indent=2, ensure_ascii=False)
        
        self.current_test_case = test_case_data
        return test_case_data
    
    def _action_to_dict(self, action: Action) -> dict:
        """Action 객체를 딕셔너리로 변환
        
        Args:
            action: Action 객체
            
        Returns:
            딕셔너리
        """
        result = {
            "timestamp": action.timestamp,
            "action_type": action.action_type,
            "x": action.x,
            "y": action.y,
            "description": action.description
        }
        
        # 선택적 필드 추가
        if action.screenshot_path:
            result["screenshot_path"] = action.screenshot_path
        if action.screenshot_before_path:
            result["screenshot_before_path"] = action.screenshot_before_path
        if action.button:
            result["button"] = action.button
        if action.key:
            result["key"] = action.key
        if action.scroll_dx is not None:
            result["scroll_dx"] = action.scroll_dx
        if action.scroll_dy is not None:
            result["scroll_dy"] = action.scroll_dy
        
        return result
    
    def load_test_case(self, name: str) -> dict:
        """테스트 케이스 로드
        
        Args:
            name: 테스트 케이스 이름
            
        Returns:
            로드된 테스트 케이스 정보
            
        Raises:
            FileNotFoundError: 테스트 케이스가 없을 때
        """
        self._ensure_initialized()
        
        test_cases_dir = self.config_manager.get('test_cases.directory', 'test_cases')
        json_path = os.path.join(test_cases_dir, f"{name}.json")
        
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"테스트 케이스를 찾을 수 없습니다: {name}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            self.current_test_case = json.load(f)
        
        return self.current_test_case
    
    def replay_test_case(self, verify: bool = False):
        """테스트 케이스 재실행 (Requirements 6.1)
        
        로드된 테스트 케이스의 Replay Script를 실행한다.
        
        Args:
            verify: 검증 모드 활성화 여부
            
        Raises:
            ValueError: 로드된 테스트 케이스가 없을 때
        """
        self._ensure_initialized()
        
        if not self.current_test_case:
            raise ValueError("로드된 테스트 케이스가 없습니다. 먼저 테스트 케이스를 로드하세요.")
        
        script_path = self.current_test_case.get('script_path')
        if not script_path or not os.path.exists(script_path):
            raise FileNotFoundError(f"Replay Script를 찾을 수 없습니다: {script_path}")
        
        # Replay Script 실행
        cmd = ['python', script_path]
        if verify:
            cmd.append('--verify')
        
        print(f"Replay Script 실행: {script_path}")
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode != 0:
            print(f"⚠ Replay Script가 오류와 함께 종료되었습니다 (exit code: {result.returncode})")
    
    def list_test_cases(self) -> List[dict]:
        """저장된 테스트 케이스 목록 반환
        
        Returns:
            테스트 케이스 정보 리스트
        """
        self._ensure_initialized()
        
        test_cases_dir = self.config_manager.get('test_cases.directory', 'test_cases')
        test_cases = []
        
        if not os.path.exists(test_cases_dir):
            return test_cases
        
        for filename in os.listdir(test_cases_dir):
            if filename.endswith('.json'):
                json_path = os.path.join(test_cases_dir, filename)
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        test_cases.append({
                            "name": data.get("name", filename[:-5]),
                            "created_at": data.get("created_at", "Unknown"),
                            "action_count": len(data.get("actions", []))
                        })
                except (json.JSONDecodeError, IOError):
                    # 잘못된 JSON 파일은 건너뜀
                    continue
        
        return test_cases
    
    def get_execution_history(self, test_case_name: str = None) -> List[Dict[str, Any]]:
        """테스트 케이스의 실행 이력 조회 (Requirements 15.1)
        
        Args:
            test_case_name: 테스트 케이스 이름 (None이면 현재 로드된 테스트 케이스)
            
        Returns:
            실행 이력 리스트 (날짜, 성공률, 오류 수, 의미론적 매칭 사용률 포함)
            
        Raises:
            ValueError: 테스트 케이스가 지정되지 않았을 때
        """
        self._ensure_initialized()
        
        # 테스트 케이스 이름 결정
        if test_case_name is None:
            if self.current_test_case:
                test_case_name = self.current_test_case.get('name')
            else:
                raise ValueError("테스트 케이스가 지정되지 않았습니다. 먼저 테스트 케이스를 로드하거나 이름을 지정하세요.")
        
        # AccuracyTracker 생성 및 세션 목록 조회
        tracker = AccuracyTracker(test_case_name)
        sessions = tracker.list_sessions()
        
        return sessions
    
    def enrich_test_case(self, name: str) -> Tuple[Dict[str, Any], EnrichmentResult]:
        """테스트 케이스 보강 (Requirements 5.2, 5.4)
        
        기존 테스트 케이스에 의미론적 정보를 추가한다.
        
        Args:
            name: 테스트 케이스 이름
            
        Returns:
            (보강된 테스트 케이스, EnrichmentResult) 튜플
            
        Raises:
            FileNotFoundError: 테스트 케이스가 없을 때
        """
        self._ensure_initialized()
        
        # 테스트 케이스 로드
        test_case = self.load_test_case(name)
        
        # 스크린샷 디렉토리 결정
        screenshot_dir = self.config_manager.get('automation.screenshot_dir', 'screenshots')
        
        # 보강 수행
        enriched_test_case, result = self.test_case_enricher.enrich_test_case(
            test_case, screenshot_dir
        )
        
        # 보강된 테스트 케이스 저장
        test_cases_dir = self.config_manager.get('test_cases.directory', 'test_cases')
        json_path = os.path.join(test_cases_dir, f"{name}.json")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_test_case, f, indent=2, ensure_ascii=False)
        
        self.current_test_case = enriched_test_case
        return enriched_test_case, result
    
    def is_legacy_test_case(self, name: str) -> bool:
        """레거시 테스트 케이스 여부 확인 (Requirements 5.1)
        
        Args:
            name: 테스트 케이스 이름
            
        Returns:
            레거시 테스트 케이스이면 True
        """
        self._ensure_initialized()
        
        test_case = self.load_test_case(name)
        return self.test_case_enricher.is_legacy_test_case(test_case)
    
    def get_execution_statistics(self, test_case_name: str = None) -> Dict[str, Any]:
        """테스트 케이스의 전체 실행 통계 요약 (Requirements 15.2)
        
        Args:
            test_case_name: 테스트 케이스 이름 (None이면 현재 로드된 테스트 케이스)
            
        Returns:
            통계 요약 딕셔너리
        """
        self._ensure_initialized()
        
        # 테스트 케이스 이름 결정
        if test_case_name is None:
            if self.current_test_case:
                test_case_name = self.current_test_case.get('name')
            else:
                raise ValueError("테스트 케이스가 지정되지 않았습니다.")
        
        # 실행 이력 조회
        sessions = self.get_execution_history(test_case_name)
        
        if not sessions:
            return {
                "test_case_name": test_case_name,
                "total_executions": 0,
                "avg_success_rate": 0.0,
                "total_errors": 0,
                "avg_semantic_match_rate": 0.0,
                "latest_execution": None
            }
        
        # 통계 계산
        total_executions = len(sessions)
        total_success_rate = sum(s.get("success_rate", 0.0) for s in sessions)
        total_errors = sum(s.get("failure_count", 0) for s in sessions)
        total_semantic_rate = sum(s.get("semantic_match_rate", 0.0) for s in sessions)
        
        return {
            "test_case_name": test_case_name,
            "total_executions": total_executions,
            "avg_success_rate": total_success_rate / total_executions if total_executions > 0 else 0.0,
            "total_errors": total_errors,
            "avg_semantic_match_rate": total_semantic_rate / total_executions if total_executions > 0 else 0.0,
            "latest_execution": sessions[0] if sessions else None
        }
    
    def cleanup(self):
        """리소스 정리
        
        시스템 종료 시 호출하여 리소스를 정리한다.
        """
        if self.input_monitor and self.input_monitor.is_recording:
            self.input_monitor.stop_monitoring()
        
        if self.game_manager and self.game_manager.is_game_running():
            self.game_manager.stop_game()


if __name__ == '__main__':
    # 간단한 테스트
    controller = QAAutomationController()
    
    if controller.initialize():
        print("✓ QAAutomationController 초기화 성공")
        
        # 테스트 케이스 목록 확인
        test_cases = controller.list_test_cases()
        print(f"저장된 테스트 케이스: {len(test_cases)}개")
        for tc in test_cases:
            print(f"  - {tc['name']} ({tc['created_at']})")
        
        controller.cleanup()
    else:
        print("❌ QAAutomationController 초기화 실패")
