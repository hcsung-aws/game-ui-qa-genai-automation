"""
InputMonitor 기본 테스트

InputMonitor, ActionRecorder, Action 클래스의 기본 기능을 테스트한다.
"""

import pytest
from datetime import datetime
from src.input_monitor import InputMonitor, ActionRecorder, Action
from src.config_manager import ConfigManager


class TestAction:
    """Action 데이터 클래스 테스트"""
    
    def test_action_creation(self):
        """액션 생성 테스트"""
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100,
            y=200,
            description='테스트 클릭',
            button='left'
        )
        
        assert action.action_type == 'click'
        assert action.x == 100
        assert action.y == 200
        assert action.button == 'left'


class TestActionRecorder:
    """ActionRecorder 테스트"""
    
    def test_recorder_initialization(self):
        """ActionRecorder 초기화 테스트"""
        config = ConfigManager()
        config.config = {'automation': {'screenshot_on_action': False}}
        
        recorder = ActionRecorder(config)
        
        assert recorder.actions == []
        assert recorder.last_action_time is None
    
    def test_record_single_action(self):
        """단일 액션 기록 테스트"""
        config = ConfigManager()
        config.config = {'automation': {'screenshot_on_action': False}}
        
        recorder = ActionRecorder(config)
        
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100,
            y=200,
            description='테스트 클릭'
        )
        
        recorder.record_action(action)
        
        assert len(recorder.get_actions()) == 1
        assert recorder.get_actions()[0].action_type == 'click'
    
    def test_clear_actions(self):
        """액션 초기화 테스트"""
        config = ConfigManager()
        config.config = {'automation': {'screenshot_on_action': False}}
        
        recorder = ActionRecorder(config)
        
        action = Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=100,
            y=200,
            description='테스트 클릭'
        )
        
        recorder.record_action(action)
        assert len(recorder.get_actions()) == 1
        
        recorder.clear_actions()
        assert len(recorder.get_actions()) == 0
        assert recorder.last_action_time is None


class TestInputMonitor:
    """InputMonitor 테스트"""
    
    def test_monitor_initialization(self):
        """InputMonitor 초기화 테스트"""
        config = ConfigManager()
        config.config = {'automation': {'screenshot_on_action': False}}
        
        recorder = ActionRecorder(config)
        monitor = InputMonitor(recorder)
        
        assert monitor.action_recorder == recorder
        assert monitor.is_recording is False
        assert monitor.mouse_listener is None
        assert monitor.keyboard_listener is None
    
    def test_start_stop_monitoring(self):
        """모니터링 시작/중지 테스트"""
        config = ConfigManager()
        config.config = {'automation': {'screenshot_on_action': False}}
        
        recorder = ActionRecorder(config)
        monitor = InputMonitor(recorder)
        
        # 모니터링 시작
        monitor.start_monitoring()
        assert monitor.is_recording is True
        assert monitor.mouse_listener is not None
        assert monitor.keyboard_listener is not None
        
        # 모니터링 중지
        monitor.stop_monitoring()
        assert monitor.is_recording is False
    
    def test_click_event_capture(self):
        """클릭 이벤트 캡처 검증 (Requirements 3.2)
        
        마우스 클릭 시 좌표와 버튼 정보가 올바르게 캡처되는지 검증한다.
        """
        from pynput.mouse import Button
        
        config = ConfigManager()
        config.config = {'automation': {'screenshot_on_action': False}}
        
        recorder = ActionRecorder(config)
        monitor = InputMonitor(recorder)
        
        # 모니터링 시작
        monitor.start_monitoring()
        
        # 클릭 이벤트 시뮬레이션 (pressed=True)
        test_x, test_y = 640, 480
        monitor._on_mouse_click(test_x, test_y, Button.left, pressed=True)
        
        # 액션이 기록되었는지 확인
        actions = recorder.get_actions()
        assert len(actions) == 1
        
        # 클릭 정보 검증
        click_action = actions[0]
        assert click_action.action_type == 'click'
        assert click_action.x == test_x
        assert click_action.y == test_y
        assert click_action.button == 'left'
        assert f'클릭 ({test_x}, {test_y})' in click_action.description
        
        # 모니터링 중지
        monitor.stop_monitoring()
    
    def test_click_event_not_captured_when_not_recording(self):
        """기록 중이 아닐 때 클릭 이벤트가 캡처되지 않는지 검증"""
        from pynput.mouse import Button
        
        config = ConfigManager()
        config.config = {'automation': {'screenshot_on_action': False}}
        
        recorder = ActionRecorder(config)
        monitor = InputMonitor(recorder)
        
        # 모니터링을 시작하지 않은 상태에서 클릭
        monitor._on_mouse_click(100, 200, Button.left, pressed=True)
        
        # 액션이 기록되지 않았는지 확인
        actions = recorder.get_actions()
        assert len(actions) == 0
    
    def test_keyboard_event_capture(self):
        """키보드 이벤트 캡처 검증 (Requirements 3.3)
        
        키보드 입력 시 키 정보가 올바르게 캡처되는지 검증한다.
        """
        from pynput.keyboard import KeyCode
        
        config = ConfigManager()
        config.config = {'automation': {'screenshot_on_action': False}}
        
        recorder = ActionRecorder(config)
        monitor = InputMonitor(recorder)
        
        # 모니터링 시작
        monitor.start_monitoring()
        
        # 일반 문자 키 입력 시뮬레이션
        test_key = KeyCode.from_char('a')
        monitor._on_key_press(test_key)
        
        # 액션이 기록되었는지 확인
        actions = recorder.get_actions()
        assert len(actions) == 1
        
        # 키 입력 정보 검증
        key_action = actions[0]
        assert key_action.action_type == 'key_press'
        assert key_action.key == 'a'
        assert '키 입력: a' in key_action.description
        
        # 모니터링 중지
        monitor.stop_monitoring()
    
    def test_keyboard_special_key_capture(self):
        """특수 키 캡처 검증
        
        Enter, Shift 등 특수 키가 올바르게 캡처되는지 검증한다.
        """
        from pynput.keyboard import Key
        
        config = ConfigManager()
        config.config = {'automation': {'screenshot_on_action': False}}
        
        recorder = ActionRecorder(config)
        monitor = InputMonitor(recorder)
        
        # 모니터링 시작
        monitor.start_monitoring()
        
        # 특수 키 입력 시뮬레이션 (Enter)
        monitor._on_key_press(Key.enter)
        
        # 액션이 기록되었는지 확인
        actions = recorder.get_actions()
        assert len(actions) == 1
        
        # 특수 키 정보 검증
        key_action = actions[0]
        assert key_action.action_type == 'key_press'
        assert 'Key.enter' in key_action.key
        assert '키 입력:' in key_action.description
        
        # 모니터링 중지
        monitor.stop_monitoring()
    
    def test_keyboard_event_not_captured_when_not_recording(self):
        """기록 중이 아닐 때 키보드 이벤트가 캡처되지 않는지 검증"""
        from pynput.keyboard import KeyCode
        
        config = ConfigManager()
        config.config = {'automation': {'screenshot_on_action': False}}
        
        recorder = ActionRecorder(config)
        monitor = InputMonitor(recorder)
        
        # 모니터링을 시작하지 않은 상태에서 키 입력
        test_key = KeyCode.from_char('x')
        monitor._on_key_press(test_key)
        
        # 액션이 기록되지 않았는지 확인
        actions = recorder.get_actions()
        assert len(actions) == 0
