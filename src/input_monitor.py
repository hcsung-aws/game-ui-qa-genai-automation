"""
Input Monitor Module

pynput을 사용하여 사용자의 마우스와 키보드 입력을 실시간으로 모니터링하고 기록한다.
"""

import time
import os
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field
from pynput import mouse, keyboard
import pyautogui

from src.window_capture import WindowCapture


@dataclass
class Action:
    """액션 데이터 클래스"""
    timestamp: str
    action_type: str  # 'click', 'key_press', 'scroll', 'wait'
    x: int
    y: int
    description: str
    screenshot_path: Optional[str] = None  # 액션 후 스크린샷 (화면 전환 완료 후)
    screenshot_before_path: Optional[str] = None  # 액션 전 스크린샷 (클릭 시점)
    button: Optional[str] = None  # 'left', 'right', 'middle'
    key: Optional[str] = None
    scroll_dx: Optional[int] = None
    scroll_dy: Optional[int] = None


class ActionRecorder:
    """액션 기록기"""
    
    def __init__(self, config):
        """
        Args:
            config: 설정 관리자 (ConfigManager)
        """
        self.config = config
        self.actions: List[Action] = []
        self.last_action_time: Optional[datetime] = None
        self._screenshot_counter = 0
        self._pending_before_screenshot: Optional[str] = None  # 클릭 전 스크린샷 경로
        
        # 게임 윈도우 캡처 설정
        window_title = config.get('game.window_title', '')
        self._window_capture = WindowCapture(window_title) if window_title else None
        self._capture_delay = config.get('automation.capture_delay', 0.5)
        
        # 스크린샷 디렉토리 확인
        screenshot_dir = config.get('automation.screenshot_dir', 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
    
    def _find_game_window(self):
        """게임 윈도우 찾기 (최초 1회)"""
        if self._window_capture and not self._window_capture._hwnd:
            self._window_capture.find_window()
    
    def _get_window_offset(self) -> tuple:
        """게임 윈도우의 화면상 오프셋 가져오기
        
        Returns:
            (left, top) 오프셋 튜플. 윈도우를 찾지 못하면 (0, 0) 반환
        """
        self._find_game_window()
        
        if self._window_capture and self._window_capture._hwnd:
            rect = self._window_capture.get_window_rect()
            if rect:
                return (rect[0], rect[1])  # left, top
        
        return (0, 0)
    
    def convert_to_window_coords(self, screen_x: int, screen_y: int) -> tuple:
        """전체 화면 좌표를 게임 윈도우 기준 상대 좌표로 변환
        
        Args:
            screen_x: 전체 화면 X 좌표
            screen_y: 전체 화면 Y 좌표
            
        Returns:
            (window_x, window_y) 윈도우 기준 상대 좌표
        """
        offset_x, offset_y = self._get_window_offset()
        return (screen_x - offset_x, screen_y - offset_y)
    
    def _capture_game_screenshot(self) -> Optional[any]:
        """게임 윈도우만 스크린샷 캡처
        
        Returns:
            PIL Image 또는 None
        """
        self._find_game_window()
        
        if self._window_capture and self._window_capture._hwnd:
            # 게임 윈도우 영역만 캡처
            return self._window_capture.capture_window_region()
        else:
            # 윈도우를 찾지 못하면 전체 화면 캡처
            return pyautogui.screenshot()
    
    def capture_before_screenshot(self) -> Optional[str]:
        """클릭 전 스크린샷 캡처 (클릭 시점의 화면 상태)
        
        InputMonitor에서 클릭 이벤트 발생 시 호출하여
        클릭 직전의 화면 상태를 캡처한다.
        
        Returns:
            저장된 스크린샷 경로 또는 None
        """
        if not self.config.get('automation.screenshot_on_action', False):
            return None
        
        screenshot_dir = self.config.get('automation.screenshot_dir', 'screenshots')
        screenshot_path = f"{screenshot_dir}/action_{self._screenshot_counter:04d}_before.png"
        
        screenshot = self._capture_game_screenshot()
        if screenshot:
            screenshot.save(screenshot_path)
            self._pending_before_screenshot = screenshot_path
            return screenshot_path
        
        return None
    
    def record_action(self, action: Action):
        """액션 기록
        
        스크린샷은 액션 실행 후 일정 시간 대기 후 캡처한다.
        (화면 전환이 완료된 상태를 캡처하기 위함)
        클릭 전 스크린샷은 capture_before_screenshot()에서 미리 캡처된 것을 사용한다.
        
        Args:
            action: 기록할 액션
        """
        # 이전 액션과의 시간 차이 계산 (스크린샷 캡처 전에 수행)
        current_time = datetime.now()
        if self.last_action_time:
            time_diff = (current_time - self.last_action_time).total_seconds()
            if time_diff > 0.5:  # 0.5초 이상 차이나면 wait 액션 추가
                wait_action = Action(
                    timestamp=self.last_action_time.isoformat(),
                    action_type='wait',
                    x=0,
                    y=0,
                    description=f'{time_diff:.1f}초 대기'
                )
                self.actions.append(wait_action)
        
        # 클릭 전 스크린샷 설정 (미리 캡처된 것이 있으면)
        if self._pending_before_screenshot:
            action.screenshot_before_path = self._pending_before_screenshot
            self._pending_before_screenshot = None
        
        # 스크린샷 캡처 (설정에 따라) - 액션 후 스크린샷
        # 클릭/키 입력 후 화면 전환 시간을 위해 대기 후 캡처
        if self.config.get('automation.screenshot_on_action', False):
            # 캡처 전 대기 (화면 전환 완료 대기)
            if self._capture_delay > 0:
                time.sleep(self._capture_delay)
            
            screenshot_dir = self.config.get('automation.screenshot_dir', 'screenshots')
            screenshot_path = f"{screenshot_dir}/action_{self._screenshot_counter:04d}.png"
            
            # 게임 윈도우만 캡처
            screenshot = self._capture_game_screenshot()
            if screenshot:
                screenshot.save(screenshot_path)
                action.screenshot_path = screenshot_path
                self._screenshot_counter += 1
        
        self.actions.append(action)
        self.last_action_time = datetime.now()  # 스크린샷 캡처 후 시간 갱신
    
    def get_actions(self) -> List[Action]:
        """기록된 액션 목록 반환
        
        마지막에 'stop' + Enter 패턴이 있으면 제거한다.
        (녹화 중단을 위한 터미널 입력이므로)
        
        Returns:
            액션 리스트
        """
        actions = self.actions.copy()
        actions = self._remove_trailing_stop_pattern(actions)
        return actions
    
    def _remove_trailing_stop_pattern(self, actions: List[Action]) -> List[Action]:
        """마지막 터미널 입력 패턴 제거
        
        녹화 중단을 위해 터미널에 입력한 내용을 제거한다.
        - 마지막 key_press들 중 Enter로 끝나는 패턴 제거
        - 그 직전의 클릭 액션도 제거 (터미널 클릭)
        
        Args:
            actions: 액션 리스트
            
        Returns:
            패턴이 제거된 액션 리스트
        """
        if len(actions) < 2:
            return actions
        
        # 뒤에서부터 key_press 액션들 찾기
        cut_index = len(actions)
        found_enter = False
        
        for i in range(len(actions) - 1, -1, -1):
            action = actions[i]
            
            if action.action_type == 'key_press':
                # Enter 키로 끝나는지 확인
                if action.key == 'Key.enter':
                    found_enter = True
                cut_index = i
            elif action.action_type == 'wait':
                # wait 액션은 건너뜀
                continue
            else:
                # 다른 타입의 액션 (click 등)
                if found_enter:
                    # Enter가 있었으면 이 액션(터미널 클릭)도 제거
                    cut_index = i
                break
        
        if found_enter and cut_index < len(actions):
            # 직전의 wait 액션도 제거
            if cut_index > 0 and actions[cut_index - 1].action_type == 'wait':
                cut_index -= 1
            return actions[:cut_index]
        
        return actions
    
    def clear_actions(self):
        """기록된 액션 초기화"""
        self.actions = []
        self.last_action_time = None
        self._screenshot_counter = 0


class InputMonitor:
    """입력 모니터
    
    pynput을 사용하여 마우스와 키보드 입력을 실시간으로 모니터링한다.
    """
    
    def __init__(self, action_recorder: ActionRecorder):
        """
        Args:
            action_recorder: 액션 기록기
        """
        self.action_recorder = action_recorder
        self.mouse_listener: Optional[mouse.Listener] = None
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.is_recording = False
    
    def start_monitoring(self):
        """입력 모니터링 시작"""
        self.is_recording = True
        
        # 마우스 리스너 시작
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener.start()
        
        # 키보드 리스너 시작
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        self.keyboard_listener.start()
    
    def stop_monitoring(self):
        """입력 모니터링 중지"""
        self.is_recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
    
    def _on_mouse_click(self, x, y, button, pressed):
        """마우스 클릭 이벤트 핸들러
        
        Args:
            x: X 좌표 (전체 화면 기준)
            y: Y 좌표 (전체 화면 기준)
            button: 마우스 버튼
            pressed: 눌림/뗌 상태
        """
        if pressed and self.is_recording:
            # 클릭 전 스크린샷 캡처 (클릭 시점의 화면 상태)
            # 예외 발생 시에도 액션 기록은 계속 진행
            try:
                self.action_recorder.capture_before_screenshot()
            except Exception:
                pass  # 스크린샷 실패해도 액션 기록은 진행
            
            # 전체 화면 좌표를 게임 윈도우 기준 상대 좌표로 변환
            window_x, window_y = self.action_recorder.convert_to_window_coords(x, y)
            
            action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='click',
                x=window_x,
                y=window_y,
                description=f'클릭 ({window_x}, {window_y})',
                button=button.name
            )
            self.action_recorder.record_action(action)
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """마우스 스크롤 이벤트 핸들러
        
        Args:
            x: X 좌표 (전체 화면 기준)
            y: Y 좌표 (전체 화면 기준)
            dx: 수평 스크롤 양
            dy: 수직 스크롤 양
        """
        if self.is_recording:
            # 전체 화면 좌표를 게임 윈도우 기준 상대 좌표로 변환
            window_x, window_y = self.action_recorder.convert_to_window_coords(x, y)
            
            action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='scroll',
                x=window_x,
                y=window_y,
                description=f'스크롤 ({dx}, {dy})',
                scroll_dx=dx,
                scroll_dy=dy
            )
            self.action_recorder.record_action(action)
    
    def _on_key_press(self, key):
        """키보드 입력 이벤트 핸들러
        
        Args:
            key: 눌린 키
        """
        if self.is_recording:
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key)
            
            action = Action(
                timestamp=datetime.now().isoformat(),
                action_type='key_press',
                x=0,
                y=0,
                description=f'키 입력: {key_char}',
                key=key_char
            )
            self.action_recorder.record_action(action)
