"""
ScriptGenerator - 기록된 액션을 Python 스크립트로 변환

Requirements: 5.1, 5.2, 5.3, 5.4, 2.1, 2.2, 2.3
"""

import json
import re
from typing import List, Dict, Any, Union
from src.input_monitor import Action
from src.semantic_action_recorder import SemanticAction


class ScriptGenerator:
    """스크립트 생성기"""
    
    def __init__(self, config):
        """
        Args:
            config: ConfigManager 인스턴스
        """
        self.config = config
    
    def generate_replay_script(self, actions: List[Action], output_path: str, 
                               verify_mode: bool = True) -> str:
        """재실행 스크립트 생성
        
        Args:
            actions: 액션 리스트
            output_path: 출력 파일 경로
            verify_mode: 검증 모드 지원 여부 (기본: True)
            
        Returns:
            생성된 스크립트 경로
        """
        # 스크립트 헤더 생성
        script_content = self._generate_script_header(verify_mode)
        
        # 액션 데이터 생성 (딕셔너리 형식으로 저장)
        script_content += self._generate_actions_data(actions)
        
        # replay_actions 함수 생성 (액션 코드 직접 생성)
        script_content += self._generate_replay_function_with_actions(actions, verify_mode)
        
        # 메인 실행 코드 생성
        script_content += self._generate_main_code(verify_mode)
        
        # UTF-8 인코딩으로 파일 저장 (Requirements 5.4)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return output_path
    
    def _generate_script_header(self, verify_mode: bool = True) -> str:
        """스크립트 헤더 생성
        
        Args:
            verify_mode: 검증 모드 지원 여부
            
        Returns:
            헤더 문자열
        """
        # config에서 윈도우 타이틀 가져오기
        window_title = self.config.get('game.window_title', '')
        
        header = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
자동 생성된 Replay Script

이 스크립트는 기록된 액션을 재실행합니다.
--verify 옵션으로 검증 모드를 활성화할 수 있습니다.

좌표는 게임 윈도우 기준 상대 좌표로 저장되어 있으며,
재현 시 윈도우 위치를 감지하여 스크린 절대 좌표로 변환합니다.
"""

import pyautogui
import time
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 윈도우 좌표 변환용 임포트
try:
    from src.window_capture import WindowCapture
    WINDOW_CAPTURE_AVAILABLE = True
except ImportError:
    WINDOW_CAPTURE_AVAILABLE = False

# 게임 윈도우 타이틀
GAME_WINDOW_TITLE = ''' + repr(window_title) + '''

# 윈도우 오프셋 캐시
_window_offset = None

def get_window_offset():
    """게임 윈도우의 스크린 오프셋 가져오기
    
    Returns:
        (offset_x, offset_y) 튜플
    """
    global _window_offset
    
    if _window_offset is not None:
        return _window_offset
    
    if WINDOW_CAPTURE_AVAILABLE and GAME_WINDOW_TITLE:
        try:
            wc = WindowCapture(GAME_WINDOW_TITLE)
            if wc.find_window():
                rect = wc.get_window_rect()
                if rect:
                    _window_offset = (rect[0], rect[1])
                    return _window_offset
        except Exception as e:
            print(f"⚠ 윈도우 오프셋 가져오기 실패: {e}")
    
    _window_offset = (0, 0)
    return _window_offset

def to_screen_coords(window_x, window_y):
    """윈도우 상대 좌표를 스크린 절대 좌표로 변환
    
    Args:
        window_x: 윈도우 기준 X 좌표
        window_y: 윈도우 기준 Y 좌표
        
    Returns:
        (screen_x, screen_y) 스크린 절대 좌표
    """
    offset_x, offset_y = get_window_offset()
    return (window_x + offset_x, window_y + offset_y)

'''
        if verify_mode:
            header += '''
# 검증 모드용 임포트
try:
    from src.config_manager import ConfigManager
    from src.replay_verifier import ReplayVerifier
    VERIFY_AVAILABLE = True
except ImportError:
    VERIFY_AVAILABLE = False

'''
        return header
    
    def _generate_actions_data(self, actions: List[Union[Action, SemanticAction]]) -> str:
        """액션 데이터를 Python 리스트로 변환
        
        SemanticAction의 경우 semantic_info, screenshot_before_path 등 
        추가 필드도 포함하여 저장한다.
        
        Requirements: 2.1, 2.2, 2.3
        
        Args:
            actions: 액션 리스트 (Action 또는 SemanticAction)
            
        Returns:
            액션 데이터 문자열
        """
        data = "# 기록된 액션 데이터\n"
        data += "ACTIONS = [\n"
        
        for action in actions:
            data += "    {\n"
            data += f"        'timestamp': {repr(action.timestamp)},\n"
            data += f"        'action_type': {repr(action.action_type)},\n"
            data += f"        'x': {action.x},\n"
            data += f"        'y': {action.y},\n"
            data += f"        'description': {repr(action.description)},\n"
            
            # wait 액션의 경우 description에서 시간 파싱 (Requirements 5.5)
            if action.action_type == 'wait':
                wait_time = self._parse_wait_time(action.description)
                data += f"        'wait_time': {wait_time},\n"
            
            # 선택적 필드 추가
            if action.button:
                data += f"        'button': '{action.button}',\n"
            if action.key:
                # 키 값을 문자열로 안전하게 변환
                key_str = str(action.key).replace("'", "\\'")
                data += f"        'key': '{key_str}',\n"
            if action.scroll_dx is not None:
                data += f"        'scroll_dx': {action.scroll_dx},\n"
            if action.scroll_dy is not None:
                data += f"        'scroll_dy': {action.scroll_dy},\n"
            if action.screenshot_path:
                data += f"        'screenshot_path': '{action.screenshot_path}',\n"
            
            # SemanticAction 추가 필드 (Requirements: 2.1, 2.2, 2.3)
            if isinstance(action, SemanticAction):
                # screenshot_before_path (Requirements: 2.2)
                if action.screenshot_before_path:
                    data += f"        'screenshot_before_path': {repr(action.screenshot_before_path)},\n"
                
                # screenshot_after_path
                if action.screenshot_after_path:
                    data += f"        'screenshot_after_path': {repr(action.screenshot_after_path)},\n"
                
                # click_region_crop_path
                if action.click_region_crop_path:
                    data += f"        'click_region_crop_path': {repr(action.click_region_crop_path)},\n"
                
                # ui_state_hash_before
                if action.ui_state_hash_before:
                    data += f"        'ui_state_hash_before': {repr(action.ui_state_hash_before)},\n"
                
                # ui_state_hash_after
                if action.ui_state_hash_after:
                    data += f"        'ui_state_hash_after': {repr(action.ui_state_hash_after)},\n"
                
                # semantic_info (Requirements: 2.1, 2.3)
                if action.semantic_info:
                    # semantic_info를 JSON 형식으로 직렬화
                    semantic_info_str = json.dumps(action.semantic_info, ensure_ascii=False, indent=12)
                    # 들여쓰기 조정
                    semantic_info_str = semantic_info_str.replace('\n', '\n        ')
                    data += f"        'semantic_info': {semantic_info_str},\n"
                
                # screen_transition
                if action.screen_transition:
                    screen_transition_str = json.dumps(action.screen_transition, ensure_ascii=False, indent=12)
                    screen_transition_str = screen_transition_str.replace('\n', '\n        ')
                    data += f"        'screen_transition': {screen_transition_str},\n"
            
            data += "    },\n"
        
        data += "]\n\n"
        return data
    
    def _parse_wait_time(self, description: str) -> float:
        """대기 액션의 description에서 시간 파싱
        
        Args:
            description: 액션 설명 (예: "2.5초 대기")
            
        Returns:
            대기 시간 (초)
        """
        # "N초 대기" 또는 "N.M초 대기" 형식에서 숫자 추출
        match = re.search(r'(\d+\.?\d*)초', description)
        if match:
            return float(match.group(1))
        else:
            # 파싱 실패 시 기본 1초
            return 1.0
    
    def _generate_replay_function_with_actions(self, actions: List[Action], 
                                                verify_mode: bool = True) -> str:
        """액션을 직접 코드로 변환하여 replay_actions 함수 생성
        
        Args:
            actions: 액션 리스트
            verify_mode: 검증 모드 지원 여부
            
        Returns:
            함수 코드 문자열
        """
        function = '''def replay_actions(action_delay=0.5, verify=False, test_case_name="unknown", skip_wait=True):
    """액션을 순서대로 재실행
    
    Args:
        action_delay: 액션 간 지연 시간 (초)
        verify: 검증 모드 활성화 여부
        test_case_name: 테스트 케이스 이름 (검증 모드용)
        skip_wait: 검증 모드에서 대기 액션 건너뛰기 (기본: True)
    """
    verifier = None
    
    # 윈도우 오프셋 미리 가져오기
    offset_x, offset_y = get_window_offset()
    if offset_x != 0 or offset_y != 0:
        print(f"✓ 게임 윈도우 감지: 오프셋 ({offset_x}, {offset_y})")
    else:
        print("⚠ 게임 윈도우를 찾지 못했습니다. 좌표가 정확하지 않을 수 있습니다.")
    
    # 검증 모드 초기화
    if verify and VERIFY_AVAILABLE:
        config = ConfigManager()
        config.load_config()
        verifier = ReplayVerifier(config)
        verifier.start_verification_session(test_case_name)
        print("✓ 검증 모드 활성화")
        if skip_wait:
            print("✓ 빠른 검증 모드: 대기 시간 건너뛰기")
        else:
            print("✓ 전체 재현 모드: 대기 시간 포함")
    elif verify and not VERIFY_AVAILABLE:
        print("⚠ 검증 모듈을 로드할 수 없습니다. 검증 없이 진행합니다.")
    
    print(f"총 {count}개의 액션을 재실행합니다...")
    print()
    
'''.replace('{count}', str(len(actions)))
        
        # 각 액션을 Python 코드로 변환
        for i, action in enumerate(actions, 1):
            # description을 안전하게 이스케이프
            safe_description = repr(action.description)
            
            # 액션 설명 출력
            function += f"    # 액션 {i}: {safe_description}\n"
            
            # wait 액션은 검증 모드에서 skip_wait 옵션에 따라 건너뛸 수 있음
            if action.action_type == 'wait':
                function += f"    # 검증 모드 + skip_wait일 때 대기 건너뛰기\n"
                function += f"    if verify and skip_wait:\n"
                function += f"        print(f'[{i}/{len(actions)}] ' + {safe_description} + ' (건너뜀)')\n"
                function += f"    else:\n"
                function += f"        print(f'[{i}/{len(actions)}] ' + {safe_description})\n"
                function += f"        try:\n"
                # wait 액션 코드 생성
                action_code = self._generate_action_code(action)
                for line in action_code.split('\n'):
                    if line.strip():
                        function += f"            {line}\n"
                function += f"            # 액션 간 지연 시간\n"
                function += f"            if action_delay > 0:\n"
                function += f"                time.sleep(action_delay)\n"
                function += f"        except Exception as e:\n"
                function += f"            print(f'  ❌ 액션 실행 실패: {{e}}')\n"
                function += f"            pass\n"
                function += "\n"
            else:
                function += f"    print(f'[{i}/{len(actions)}] ' + {safe_description})\n"
                function += "    try:\n"
                
                # 액션 타입별 코드 생성
                action_code = self._generate_action_code(action)
                # 들여쓰기 추가 (try 블록 내부)
                for line in action_code.split('\n'):
                    if line.strip():
                        function += f"        {line}\n"
                
                # 액션 간 지연
                function += "        # 액션 간 지연 시간\n"
                function += "        if action_delay > 0:\n"
                function += "            time.sleep(action_delay)\n"
            
            # 검증 모드: screenshot_path가 있는 액션만 검증 (wait 액션이 아닌 경우)
            if action.action_type != 'wait':
                if verify_mode and action.screenshot_path:
                    function += "        # 검증 모드: 스크린샷 검증\n"
                    function += "        if verifier:\n"
                    # 다음 액션이 있으면 다음 액션 정보 전달
                    if i < len(actions):
                        function += f"            next_action = ACTIONS[{i}] if {i} < len(ACTIONS) else None\n"
                        function += f"            verifier.capture_and_verify({i-1}, ACTIONS[{i-1}], next_action)\n"
                    else:
                        function += f"            verifier.capture_and_verify({i-1}, ACTIONS[{i-1}], None)\n"
                
                function += "    except Exception as e:\n"
                function += "        print(f'  ❌ 액션 실행 실패: {e}')\n"
                function += "        # 오류가 발생해도 계속 진행 (Requirements 9.5)\n"
                function += "        pass\n"
                function += "\n"
        
        function += "    print()\n"
        function += "    print('✓ 재실행 완료')\n"
        function += "\n"
        function += "    # 검증 보고서 생성\n"
        function += "    if verifier:\n"
        function += "        report = verifier.generate_report()\n"
        function += "        verifier.print_report(report)\n"
        function += "        verifier.save_report(report)\n"
        function += "        return report\n"
        function += "    return None\n\n\n"
        
        return function
    
    def _generate_action_code(self, action: Action) -> str:
        """액션을 Python 코드로 변환
        
        좌표는 윈도우 상대 좌표로 저장되어 있으므로,
        to_screen_coords()를 사용하여 스크린 절대 좌표로 변환한다.
        
        Args:
            action: 변환할 액션
            
        Returns:
            Python 코드 문자열
        """
        if action.action_type == 'click':
            button = action.button or 'left'
            # 윈도우 상대 좌표를 스크린 절대 좌표로 변환하여 클릭
            return f"screen_x, screen_y = to_screen_coords({action.x}, {action.y}); pyautogui.click(screen_x, screen_y, button='{button}')"
        
        elif action.action_type == 'key_press':
            if action.key:
                key_str = str(action.key).replace("'", "\\'")
                # 특수 키 처리
                if key_str.startswith('Key.'):
                    key_name = key_str.replace('Key.', '')
                    return f"pyautogui.press('{key_name}')"
                else:
                    return f"pyautogui.write('{key_str}')"
            return "pass  # 키 정보 없음"
        
        elif action.action_type == 'scroll':
            scroll_dy = action.scroll_dy or 0
            if scroll_dy != 0:
                # 윈도우 상대 좌표를 스크린 절대 좌표로 변환하여 스크롤
                return f"screen_x, screen_y = to_screen_coords({action.x}, {action.y}); pyautogui.scroll({scroll_dy * 100}, screen_x, screen_y)"
            return "pass  # 스크롤 양 없음"
        
        elif action.action_type == 'wait':
            # description에서 시간 파싱 (Requirements 5.5)
            wait_time = self._parse_wait_time(action.description)
            return f"time.sleep({wait_time})"
        
        else:
            return f"print('  ⚠ 알 수 없는 액션 타입: {action.action_type}')"
    
    def _generate_replay_function(self) -> str:
        """replay_actions 함수 생성
        
        Returns:
            함수 코드 문자열
        """
        function = '''def replay_actions(actions, action_delay=0.5):
    """액션을 순서대로 재실행
    
    Args:
        actions: 액션 리스트
        action_delay: 액션 간 지연 시간 (초)
    """
    print(f"총 {len(actions)}개의 액션을 재실행합니다...")
    print()
    
    # 윈도우 오프셋 미리 가져오기
    offset_x, offset_y = get_window_offset()
    if offset_x != 0 or offset_y != 0:
        print(f"✓ 게임 윈도우 감지: 오프셋 ({offset_x}, {offset_y})")
    else:
        print("⚠ 게임 윈도우를 찾지 못했습니다. 좌표가 정확하지 않을 수 있습니다.")
    print()
    
    for i, action in enumerate(actions, 1):
        action_type = action['action_type']
        x = action['x']
        y = action['y']
        description = action['description']
        
        # 액션 실행 전 설명 출력 (Requirements 5.6)
        print(f"[{i}/{len(actions)}] {description}")
        
        try:
            if action_type == 'click':
                # 윈도우 상대 좌표를 스크린 절대 좌표로 변환
                screen_x, screen_y = to_screen_coords(x, y)
                button = action.get('button', 'left')
                pyautogui.click(screen_x, screen_y, button=button)
                
            elif action_type == 'key_press':
                # 키보드 입력 실행
                key = action.get('key', '')
                if key:
                    # 특수 키 처리
                    if key.startswith('Key.'):
                        # pynput의 Key 객체 형식 처리
                        key_name = key.replace('Key.', '')
                        pyautogui.press(key_name)
                    else:
                        # 일반 문자 입력
                        pyautogui.write(key)
                
            elif action_type == 'scroll':
                # 윈도우 상대 좌표를 스크린 절대 좌표로 변환
                screen_x, screen_y = to_screen_coords(x, y)
                scroll_dy = action.get('scroll_dy', 0)
                if scroll_dy != 0:
                    # pyautogui는 양수가 위로, 음수가 아래로
                    pyautogui.scroll(scroll_dy * 100, screen_x, screen_y)
                
            elif action_type == 'wait':
                # 대기 액션 실행
                # wait_time은 액션 데이터에 직접 포함됨
                wait_time = action.get('wait_time', 1.0)
                time.sleep(wait_time)
            
            else:
                print(f"  ⚠ 알 수 없는 액션 타입: {action_type}")
            
            # 액션 간 지연 시간 (Requirements 6.5)
            if action_delay > 0:
                time.sleep(action_delay)
        
        except Exception as e:
            print(f"  ❌ 액션 실행 실패: {e}")
            # 오류가 발생해도 계속 진행 (Requirements 9.5)
            continue
    
    print()
    print("✓ 재실행 완료")


'''
        return function
    
    def _generate_main_code(self, verify_mode: bool = True) -> str:
        """메인 실행 코드 생성
        
        Args:
            verify_mode: 검증 모드 지원 여부
            
        Returns:
            메인 코드 문자열
        """
        main = '''if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Replay Script')
    parser.add_argument('--delay', type=float, default=0.5, help='액션 간 지연 시간 (초)')
    parser.add_argument('--verify', action='store_true', help='검증 모드 활성화')
    parser.add_argument('--full-replay', action='store_true', help='전체 재현 모드 (대기 시간 포함)')
    parser.add_argument('--name', type=str, default='unknown', help='테스트 케이스 이름')
    
    args = parser.parse_args()
    
    # 테스트 케이스 이름 자동 추출 (파일명에서)
    if args.name == 'unknown':
        import os
        args.name = os.path.splitext(os.path.basename(__file__))[0]
    
    # skip_wait: 검증 모드에서 기본 True, --full-replay 옵션 시 False
    skip_wait = not args.full_replay
    
    # 액션 재실행
    replay_actions(action_delay=args.delay, verify=args.verify, test_case_name=args.name, skip_wait=skip_wait)
'''
        return main

    def save_test_case_json(
        self, 
        actions: List[Union[Action, SemanticAction]], 
        output_path: str,
        test_case_name: str = "unknown",
        semantic_enabled: bool = False
    ) -> str:
        """테스트 케이스를 JSON 파일로 저장
        
        SemanticAction의 경우 semantic_info, screenshot_before_path 등
        모든 필드를 포함하여 저장한다.
        
        Requirements: 2.1, 2.2, 2.3
        
        Args:
            actions: 액션 리스트 (Action 또는 SemanticAction)
            output_path: 출력 JSON 파일 경로
            test_case_name: 테스트 케이스 이름
            semantic_enabled: 의미론적 기능 활성화 여부
            
        Returns:
            저장된 파일 경로
        """
        from datetime import datetime
        
        # 액션 데이터 변환
        actions_data = []
        for action in actions:
            if isinstance(action, SemanticAction):
                # SemanticAction의 to_dict() 메서드 사용
                action_dict = action.to_dict()
            else:
                # 일반 Action의 경우 기본 필드만 저장
                action_dict = {
                    "timestamp": action.timestamp,
                    "action_type": action.action_type,
                    "x": action.x,
                    "y": action.y,
                    "description": action.description,
                    "screenshot_path": action.screenshot_path,
                    "button": action.button,
                    "key": action.key,
                    "scroll_dx": action.scroll_dx,
                    "scroll_dy": action.scroll_dy
                }
            actions_data.append(action_dict)
        
        # 테스트 케이스 구조 생성
        test_case = {
            "name": test_case_name,
            "version": "2.0" if semantic_enabled else "1.0",
            "created_at": datetime.now().isoformat(),
            "semantic_enabled": semantic_enabled,
            "actions": actions_data
        }
        
        # JSON 파일로 저장 (UTF-8 인코딩)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_case, f, ensure_ascii=False, indent=2)
        
        return output_path

    def load_test_case_json(self, input_path: str) -> Dict[str, Any]:
        """JSON 파일에서 테스트 케이스 로드
        
        semantic_info가 포함된 경우 SemanticAction으로 변환하고,
        그렇지 않으면 일반 Action으로 변환한다.
        
        Requirements: 2.4, 2.5
        
        Args:
            input_path: 입력 JSON 파일 경로
            
        Returns:
            테스트 케이스 딕셔너리 (actions 필드에 Action/SemanticAction 리스트 포함)
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            test_case = json.load(f)
        
        # 액션 데이터 변환
        actions = []
        for action_dict in test_case.get("actions", []):
            action = self._dict_to_action(action_dict)
            actions.append(action)
        
        # 변환된 액션 리스트로 교체
        test_case["actions"] = actions
        
        return test_case

    def _dict_to_action(self, action_dict: Dict[str, Any]) -> Union[Action, SemanticAction]:
        """딕셔너리를 Action 또는 SemanticAction으로 변환
        
        semantic_info 필드가 있고 비어있지 않으면 SemanticAction으로,
        그렇지 않으면 일반 Action으로 변환한다.
        
        Requirements: 2.4, 2.5
        
        Args:
            action_dict: 액션 딕셔너리
            
        Returns:
            Action 또는 SemanticAction 인스턴스
        """
        # semantic_info가 있고 비어있지 않으면 SemanticAction으로 변환
        semantic_info = action_dict.get("semantic_info", {})
        has_semantic_fields = (
            semantic_info or 
            action_dict.get("screenshot_before_path") or
            action_dict.get("screen_transition")
        )
        
        if has_semantic_fields:
            return SemanticAction.from_dict(action_dict)
        else:
            # 일반 Action으로 변환
            return Action(
                timestamp=action_dict.get("timestamp", ""),
                action_type=action_dict.get("action_type", ""),
                x=action_dict.get("x", 0),
                y=action_dict.get("y", 0),
                description=action_dict.get("description", ""),
                screenshot_path=action_dict.get("screenshot_path"),
                button=action_dict.get("button"),
                key=action_dict.get("key"),
                scroll_dx=action_dict.get("scroll_dx"),
                scroll_dy=action_dict.get("scroll_dy")
            )

    def load_actions_from_json(self, input_path: str) -> List[Union[Action, SemanticAction]]:
        """JSON 파일에서 액션 리스트만 로드
        
        Requirements: 2.4, 2.5
        
        Args:
            input_path: 입력 JSON 파일 경로
            
        Returns:
            Action 또는 SemanticAction 리스트
        """
        test_case = self.load_test_case_json(input_path)
        return test_case.get("actions", [])


if __name__ == '__main__':
    # 간단한 테스트
    from config_manager import ConfigManager
    from input_monitor import Action
    from datetime import datetime
    
    config = ConfigManager()
    config.create_default_config()
    
    generator = ScriptGenerator(config)
    
    # 테스트 액션 생성
    test_actions = [
        Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=640,
            y=400,
            description='게임 시작 버튼 클릭',
            button='left'
        ),
        Action(
            timestamp=datetime.now().isoformat(),
            action_type='wait',
            x=0,
            y=0,
            description='2.0초 대기'
        ),
        Action(
            timestamp=datetime.now().isoformat(),
            action_type='key_press',
            x=0,
            y=0,
            description='플레이어 이름 입력',
            key='TestPlayer'
        ),
    ]
    
    # 스크립트 생성
    output_path = 'test_replay.py'
    generator.generate_replay_script(test_actions, output_path)
    print(f"테스트 스크립트 생성 완료: {output_path}")
