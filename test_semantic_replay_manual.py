#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
의미론적 테스트 기록 및 재현 수동 테스트 스크립트

이 스크립트는 실제 게임에서 의미론적 기록/재현 기능을 테스트합니다.

사용법:
    python test_semantic_replay_manual.py record <test_name>  # 녹화
    python test_semantic_replay_manual.py replay <test_name>  # 재현
    python test_semantic_replay_manual.py compare <test_name> # 비교 분석
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_manager import ConfigManager
from src.input_monitor import InputMonitor, ActionRecorder
from src.semantic_action_recorder import SemanticActionRecorder, SemanticAction
from src.semantic_action_replayer import SemanticActionReplayer, ReplayResult
from src.ui_analyzer import UIAnalyzer
from src.script_generator import ScriptGenerator


class SemanticTestRunner:
    """의미론적 테스트 실행기"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.config = ConfigManager(config_path)
        self.config.load_config()
        
        self.ui_analyzer = UIAnalyzer(self.config)
        self.semantic_recorder = SemanticActionRecorder(self.config, self.ui_analyzer)
        self.semantic_replayer = SemanticActionReplayer(self.config, self.ui_analyzer)
        self.script_generator = ScriptGenerator(self.config)
        
        self.test_cases_dir = self.config.get('test_cases.directory', 'test_cases')
        self.screenshots_dir = self.config.get('automation.screenshot_dir', 'screenshots')
        
        os.makedirs(self.test_cases_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def record_with_semantic_info(self, test_name: str, duration_seconds: int = 60):
        """의미론적 정보와 함께 테스트 케이스 녹화
        
        Args:
            test_name: 테스트 케이스 이름
            duration_seconds: 최대 녹화 시간 (초)
        """
        print("=" * 60)
        print("  의미론적 테스트 케이스 녹화")
        print("=" * 60)
        print()
        print(f"테스트 이름: {test_name}")
        print(f"최대 녹화 시간: {duration_seconds}초")
        print()
        print("5초 후 녹화를 시작합니다. 게임 창을 활성화하세요...")
        print()
        
        for i in range(5, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        print()
        print("🔴 녹화 시작! 게임을 플레이하세요.")
        print("   Ctrl+C를 누르면 녹화가 중지됩니다.")
        print()
        
        # ActionRecorder 생성 및 InputMonitor 연결
        action_recorder = ActionRecorder(self.config)
        input_monitor = InputMonitor(action_recorder)
        
        # 녹화 시작
        input_monitor.start_monitoring()
        
        try:
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                time.sleep(0.5)
                elapsed = int(time.time() - start_time)
                action_count = len(action_recorder.get_actions())
                print(f"\r  경과: {elapsed}초 | 기록된 액션: {action_count}개", end="", flush=True)
        except KeyboardInterrupt:
            print("\n")
            print("녹화가 중지되었습니다.")
        finally:
            input_monitor.stop_monitoring()
        
        # 기록된 액션 가져오기
        actions = action_recorder.get_actions()
        print()
        print(f"✓ 총 {len(actions)}개의 액션이 기록되었습니다.")
        
        if not actions:
            print("❌ 기록된 액션이 없습니다.")
            return
        
        # 의미론적 정보 추가 (클릭 액션에 대해 - 저장된 스크린샷 기반 분석)
        print()
        print("의미론적 정보를 분석 중...")
        print("  (저장된 스크린샷을 기반으로 분석합니다)")
        semantic_actions = []
        
        for i, action in enumerate(actions):
            print(f"\r  분석 중: {i+1}/{len(actions)}", end="", flush=True)
            
            if action.action_type == 'click':
                # 저장된 스크린샷 기반 의미론적 분석 수행
                semantic_action = self._analyze_action_from_screenshot(action, i)
                semantic_actions.append(semantic_action)
            else:
                # 클릭이 아닌 액션은 그대로 변환
                semantic_action = SemanticAction(
                    timestamp=action.timestamp,
                    action_type=action.action_type,
                    x=action.x,
                    y=action.y,
                    description=action.description,
                    button=action.button,
                    key=action.key,
                    scroll_dx=action.scroll_dx,
                    scroll_dy=action.scroll_dy,
                    screenshot_path=action.screenshot_path
                )
                semantic_actions.append(semantic_action)
        
        print()
        print()
        
        # 테스트 케이스 저장
        self._save_semantic_test_case(test_name, semantic_actions)
        
        print(f"✓ 테스트 케이스 '{test_name}'이(가) 저장되었습니다.")
        print(f"  JSON: {self.test_cases_dir}/{test_name}_semantic.json")
    
    def _save_semantic_test_case(self, test_name: str, actions: List[SemanticAction]):
        """의미론적 테스트 케이스 저장"""
        json_path = os.path.join(self.test_cases_dir, f"{test_name}_semantic.json")
        
        test_case_data = {
            "name": test_name,
            "version": "2.0",
            "created_at": datetime.now().isoformat(),
            "semantic_enabled": True,
            "actions": [action.to_dict() for action in actions]
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(test_case_data, f, indent=2, ensure_ascii=False)
    
    def _analyze_action_from_screenshot(self, action, action_index: int) -> SemanticAction:
        """저장된 스크린샷을 기반으로 액션의 의미론적 정보 분석
        
        녹화 시 저장된 스크린샷 파일을 로드하여 Vision LLM으로 분석한다.
        스크린샷이 없거나 분석 실패 시 기본 SemanticAction을 반환한다.
        
        Args:
            action: 분석할 Action 객체
            action_index: 액션 인덱스 (로깅용)
            
        Returns:
            의미론적 정보가 포함된 SemanticAction
        """
        from PIL import Image
        
        # 기본 SemanticAction 생성
        semantic_action = SemanticAction(
            timestamp=action.timestamp,
            action_type=action.action_type,
            x=action.x,
            y=action.y,
            description=action.description,
            button=action.button,
            screenshot_path=action.screenshot_path,
            screenshot_before_path=action.screenshot_before_path  # 클릭 전 스크린샷
        )
        
        # 스크린샷 파일 확인 (클릭 전 스크린샷 우선 사용)
        screenshot_path = action.screenshot_before_path or action.screenshot_path
        if not screenshot_path or not os.path.exists(screenshot_path):
            print(f"\n  ⚠ 액션 {action_index}: 스크린샷 없음, 기본값 사용")
            semantic_action.semantic_info = {
                "intent": "unknown_action",
                "target_element": {
                    "type": "unknown",
                    "text": "",
                    "description": f"좌표 ({action.x}, {action.y})의 알 수 없는 요소",
                    "bounding_box": {"x": action.x, "y": action.y, "width": 0, "height": 0},
                    "confidence": 0.0
                },
                "context": {
                    "screen_state": "unknown",
                    "expected_result": "unknown"
                }
            }
            return semantic_action
        
        try:
            # 스크린샷 로드
            image = Image.open(screenshot_path)
            
            # Vision LLM으로 UI 분석
            ui_data = self.ui_analyzer.analyze_with_retry(image)
            
            # 클릭 좌표에서 가장 가까운 UI 요소 찾기
            element = self.ui_analyzer.find_element_at_position(ui_data, action.x, action.y)
            
            if element:
                # target_element 구조 생성
                element_type = element.get("element_type", element.get("type", "unknown"))
                
                if element_type == "text_field":
                    text = element.get("content", element.get("text", ""))
                else:
                    text = element.get("text", element.get("type", ""))
                
                description = element.get("description", f"{element_type}: {text}")
                
                # bounding_box 추출 또는 계산
                bounding_box = element.get("bounding_box")
                if not bounding_box or not isinstance(bounding_box, dict):
                    elem_x = element.get("x", action.x)
                    elem_y = element.get("y", action.y)
                    width = element.get("width", 0)
                    height = element.get("height", 0)
                    bounding_box = {
                        "x": int(elem_x - width / 2) if width > 0 else elem_x,
                        "y": int(elem_y - height / 2) if height > 0 else elem_y,
                        "width": int(width),
                        "height": int(height)
                    }
                
                target_element = {
                    "type": element_type,
                    "text": text,
                    "description": description,
                    "bounding_box": bounding_box,
                    "confidence": element.get("confidence", 0.0)
                }
                
                # 의도 추론
                intent = self._infer_intent_from_element(target_element)
                
                semantic_action.semantic_info = {
                    "intent": intent,
                    "target_element": target_element,
                    "context": {
                        "screen_state": "captured",
                        "expected_result": "unknown"
                    }
                }
            else:
                # 요소를 찾지 못한 경우 - 클릭 좌표 주변 200x200 크롭 이미지 저장
                crop_path = self._save_click_region_crop(image, action.x, action.y, action_index)
                semantic_action.click_region_crop_path = crop_path
                
                semantic_action.semantic_info = {
                    "intent": "unknown_action",
                    "target_element": {
                        "type": "unknown",
                        "text": "",
                        "description": f"좌표 ({action.x}, {action.y})의 알 수 없는 요소",
                        "bounding_box": {"x": action.x, "y": action.y, "width": 0, "height": 0},
                        "confidence": 0.0
                    },
                    "context": {
                        "screen_state": "captured",
                        "expected_result": "unknown"
                    }
                }
                
        except Exception as e:
            print(f"\n  ⚠ 액션 {action_index} 분석 실패: {e}")
            semantic_action.semantic_info = {
                "intent": "unknown_action",
                "target_element": {
                    "type": "unknown",
                    "text": "",
                    "description": f"분석 실패: {e}",
                    "bounding_box": {"x": action.x, "y": action.y, "width": 0, "height": 0},
                    "confidence": 0.0
                },
                "context": {
                    "screen_state": "error",
                    "expected_result": "unknown"
                }
            }
        
        return semantic_action
    
    def _infer_intent_from_element(self, target_element: Dict[str, Any]) -> str:
        """UI 요소 정보로부터 의도 추론
        
        Args:
            target_element: 타겟 UI 요소 정보
            
        Returns:
            추론된 의도 문자열
        """
        element_type = target_element.get('type', 'unknown')
        element_text = target_element.get('text', '').lower()
        
        if element_type == 'button':
            if any(keyword in element_text for keyword in ['시작', 'start', '입장', 'enter', 'play']):
                return 'start_game'
            elif any(keyword in element_text for keyword in ['설정', 'settings', 'option']):
                return 'open_settings'
            elif any(keyword in element_text for keyword in ['확인', 'ok', 'confirm', '예']):
                return 'confirm_action'
            elif any(keyword in element_text for keyword in ['취소', 'cancel', '아니오']):
                return 'cancel_action'
            elif any(keyword in element_text for keyword in ['닫기', 'close', 'x']):
                return 'close_dialog'
            else:
                return 'click_button'
        elif element_type == 'text_field':
            return 'focus_input'
        elif element_type == 'icon':
            return 'click_icon'
        
        return 'unknown_action'
    
    def _save_click_region_crop(self, image, x: int, y: int, action_index: int) -> str:
        """클릭 좌표 주변 200x200 영역을 크롭하여 저장
        
        UI 요소 감지 실패 시 클릭 좌표 주변 영역을 저장하여
        재현 시 시각적 참고 및 템플릿 매칭에 활용한다.
        
        Args:
            image: PIL Image 객체
            x: 클릭 X 좌표
            y: 클릭 Y 좌표
            action_index: 액션 인덱스
            
        Returns:
            저장된 크롭 이미지 경로
        """
        try:
            # 크롭 영역 계산 (클릭 좌표 중심 ±100px = 200x200)
            crop_size = 100  # 반경
            img_width, img_height = image.size
            
            left = max(0, x - crop_size)
            top = max(0, y - crop_size)
            right = min(img_width, x + crop_size)
            bottom = min(img_height, y + crop_size)
            
            # 크롭 실행
            cropped = image.crop((left, top, right, bottom))
            
            # 파일명 생성 및 저장
            crop_filename = f"crop_{action_index:04d}.png"
            crop_path = os.path.join(self.screenshots_dir, crop_filename)
            cropped.save(crop_path, format='PNG')
            
            return crop_path
            
        except Exception as e:
            print(f"\n  ⚠ 크롭 이미지 저장 실패: {e}")
            return None
    
    def replay_with_semantic_matching(self, test_name_or_path: str, skip_wait: bool = True):
        """의미론적 매칭을 사용하여 테스트 케이스 재현
        
        Args:
            test_name_or_path: 테스트 케이스 이름 또는 JSON 파일 경로
            skip_wait: 대기 액션 건너뛰기 (기본: True)
        """
        print("=" * 60)
        print("  의미론적 테스트 케이스 재현")
        print("=" * 60)
        print()
        
        if skip_wait:
            print("✓ 빠른 재현 모드: 대기 시간 건너뛰기")
            print()
        
        # 테스트 케이스 로드 - 파일 경로 또는 이름 지원
        if test_name_or_path.endswith('.json') and os.path.exists(test_name_or_path):
            # 직접 파일 경로가 주어진 경우
            json_path = test_name_or_path
            test_name = os.path.splitext(os.path.basename(test_name_or_path))[0]
        else:
            # 테스트 이름으로 파일 찾기
            test_name = test_name_or_path
            json_path = os.path.join(self.test_cases_dir, f"{test_name}_semantic.json")
            
            if not os.path.exists(json_path):
                # 일반 테스트 케이스 시도
                json_path = os.path.join(self.test_cases_dir, f"{test_name}.json")
                if not os.path.exists(json_path):
                    print(f"❌ 테스트 케이스를 찾을 수 없습니다: {test_name}")
                    return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            test_case = json.load(f)
        
        print(f"테스트 케이스: {test_case.get('name', test_name)}")
        print(f"생성일: {test_case.get('created_at', 'Unknown')}")
        print(f"버전: {test_case.get('version', '1.0')}")
        print(f"액션 수: {len(test_case.get('actions', []))}")
        print()
        
        # 액션을 SemanticAction으로 변환
        actions = []
        for action_dict in test_case.get('actions', []):
            action = SemanticAction.from_dict(action_dict)
            actions.append(action)
        
        print("5초 후 재현을 시작합니다. 게임 창을 활성화하세요...")
        print()
        
        for i in range(5, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        print()
        print("🔵 재현 시작!")
        print()
        
        # 재현 실행
        results: List[ReplayResult] = []
        
        for i, action in enumerate(actions):
            print(f"[{i+1}/{len(actions)}] {action.description}")
            
            try:
                if action.action_type == 'click':
                    # 의미론적 매칭 사용
                    result = self.semantic_replayer.replay_click_with_semantic_matching(action)
                    results.append(result)
                    
                    if result.success:
                        method_str = "의미론적" if result.method == 'semantic' else "좌표"
                        print(f"  ✓ 성공 ({method_str} 매칭)")
                        if result.coordinate_change:
                            print(f"    좌표 변경: {result.coordinate_change}")
                    else:
                        print(f"  ❌ 실패: {result.error_message}")
                
                elif action.action_type == 'wait':
                    # 대기 액션
                    import re
                    match = re.search(r'(\d+\.?\d*)초', action.description)
                    if match:
                        wait_time = float(match.group(1))
                        if skip_wait:
                            print(f"  ⏭ {wait_time}초 대기 (건너뜀)")
                        else:
                            print(f"  ⏳ {wait_time}초 대기...")
                            time.sleep(wait_time)
                    
                    result = ReplayResult(
                        action_id=f"action_{i:04d}",
                        success=True,
                        method='direct',
                        original_coords=(0, 0)
                    )
                    results.append(result)
                
                else:
                    # 기타 액션
                    result = self.semantic_replayer.replay_action(action)
                    results.append(result)
                
            except Exception as e:
                print(f"  ❌ 오류: {e}")
                result = ReplayResult(
                    action_id=f"action_{i:04d}",
                    success=False,
                    method='failed',
                    original_coords=(action.x, action.y),
                    error_message=str(e)
                )
                results.append(result)
            
            # 액션 간 딜레이
            action_delay = self.config.get('automation.action_delay', 0.5)
            time.sleep(action_delay)
        
        print()
        print("=" * 60)
        print("  재현 결과 요약")
        print("=" * 60)
        
        # 통계 계산
        total = len(results)
        success_count = sum(1 for r in results if r.success)
        semantic_count = sum(1 for r in results if r.method == 'semantic')
        coordinate_count = sum(1 for r in results if r.method in ['direct', 'coordinate'])
        failed_count = sum(1 for r in results if not r.success)
        
        print(f"총 액션: {total}")
        print(f"성공: {success_count} ({success_count/total*100:.1f}%)")
        print(f"  - 의미론적 매칭: {semantic_count}")
        print(f"  - 좌표 매칭: {coordinate_count}")
        print(f"실패: {failed_count}")
        
        # 결과 저장
        self._save_replay_results(test_name, results)
    
    def _save_replay_results(self, test_name: str, results: List[ReplayResult]):
        """재현 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"reports/{test_name}_{timestamp}_semantic_report.json"
        
        os.makedirs("reports", exist_ok=True)
        
        report_data = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "total_actions": len(results),
            "success_count": sum(1 for r in results if r.success),
            "semantic_match_count": sum(1 for r in results if r.method == 'semantic'),
            "coordinate_match_count": sum(1 for r in results if r.method in ['direct', 'coordinate']),
            "failed_count": sum(1 for r in results if not r.success),
            "results": [
                {
                    "action_id": r.action_id,
                    "success": r.success,
                    "method": r.method,
                    "original_coords": r.original_coords,
                    "actual_coords": r.actual_coords,
                    "coordinate_change": r.coordinate_change,
                    "match_confidence": r.match_confidence,
                    "error_message": r.error_message
                }
                for r in results
            ]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print()
        print(f"✓ 결과 리포트 저장: {report_path}")
    
    def compare_results(self, test_name: str):
        """테스트 케이스의 재현 결과 비교 분석
        
        Args:
            test_name: 테스트 케이스 이름
        """
        print("=" * 60)
        print("  재현 결과 비교 분석")
        print("=" * 60)
        print()
        
        # 리포트 파일 찾기
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            print("❌ 리포트 디렉토리가 없습니다.")
            return
        
        report_files = [
            f for f in os.listdir(reports_dir)
            if f.startswith(test_name) and f.endswith('_semantic_report.json')
        ]
        
        if not report_files:
            print(f"❌ '{test_name}'에 대한 리포트를 찾을 수 없습니다.")
            return
        
        # 최신 리포트 로드
        report_files.sort(reverse=True)
        latest_report_path = os.path.join(reports_dir, report_files[0])
        
        with open(latest_report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        print(f"리포트: {report_files[0]}")
        print(f"테스트 시간: {report.get('timestamp', 'Unknown')}")
        print()
        
        # 통계 출력
        total = report.get('total_actions', 0)
        success = report.get('success_count', 0)
        semantic = report.get('semantic_match_count', 0)
        coordinate = report.get('coordinate_match_count', 0)
        failed = report.get('failed_count', 0)
        
        print("[전체 통계]")
        print(f"  총 액션: {total}")
        print(f"  성공률: {success/total*100:.1f}%" if total > 0 else "  성공률: N/A")
        print()
        
        print("[매칭 방법 분석]")
        print(f"  의미론적 매칭: {semantic} ({semantic/total*100:.1f}%)" if total > 0 else "  의미론적 매칭: 0")
        print(f"  좌표 매칭: {coordinate} ({coordinate/total*100:.1f}%)" if total > 0 else "  좌표 매칭: 0")
        print(f"  실패: {failed} ({failed/total*100:.1f}%)" if total > 0 else "  실패: 0")
        print()
        
        # 좌표 변경 분석
        results = report.get('results', [])
        coord_changes = [
            r['coordinate_change'] for r in results
            if r.get('coordinate_change') and r['coordinate_change'] != (0, 0)
        ]
        
        if coord_changes:
            print("[좌표 변경 분석]")
            avg_x = sum(abs(c[0]) for c in coord_changes) / len(coord_changes)
            avg_y = sum(abs(c[1]) for c in coord_changes) / len(coord_changes)
            max_x = max(abs(c[0]) for c in coord_changes)
            max_y = max(abs(c[1]) for c in coord_changes)
            
            print(f"  좌표 변경된 액션: {len(coord_changes)}개")
            print(f"  평균 X 변위: {avg_x:.1f}px")
            print(f"  평균 Y 변위: {avg_y:.1f}px")
            print(f"  최대 X 변위: {max_x}px")
            print(f"  최대 Y 변위: {max_y}px")
        else:
            print("[좌표 변경 분석]")
            print("  좌표 변경 없음")
        
        print()
        
        # 실패한 액션 상세
        failed_results = [r for r in results if not r.get('success')]
        if failed_results:
            print("[실패한 액션]")
            for r in failed_results:
                print(f"  - {r.get('action_id')}: {r.get('error_message', 'Unknown error')}")


def print_usage():
    """사용법 출력"""
    print("""
의미론적 테스트 기록 및 재현 스크립트

사용법:
    python test_semantic_replay_manual.py record <test_name> [duration]
        - 새로운 테스트 케이스를 녹화합니다.
        - duration: 최대 녹화 시간 (초, 기본값: 60)
    
    python test_semantic_replay_manual.py replay <test_name_or_path> [--full-replay]
        - 저장된 테스트 케이스를 의미론적 매칭으로 재현합니다.
        - test_name_or_path: 테스트 이름 또는 JSON 파일 경로
        - --full-replay: 대기 시간을 건너뛰지 않고 전체 재현
    
    python test_semantic_replay_manual.py compare <test_name>
        - 재현 결과를 분석하고 비교합니다.

예시:
    python test_semantic_replay_manual.py record my_test 120
    python test_semantic_replay_manual.py replay my_test
    python test_semantic_replay_manual.py replay test_cases/sr-test-0001.json
    python test_semantic_replay_manual.py replay my_test --full-replay
    python test_semantic_replay_manual.py compare my_test
""")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    test_name = sys.argv[2]
    
    runner = SemanticTestRunner()
    
    if command == 'record':
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60
        runner.record_with_semantic_info(test_name, duration)
    
    elif command == 'replay':
        # --full-replay 옵션 확인
        skip_wait = '--full-replay' not in sys.argv
        runner.replay_with_semantic_matching(test_name, skip_wait=skip_wait)
    
    elif command == 'compare':
        runner.compare_results(test_name)
    
    else:
        print(f"❌ 알 수 없는 명령어: {command}")
        print_usage()
        sys.exit(1)
