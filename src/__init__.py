"""
Game QA Automation Framework

AWS Bedrock Claude Sonnet 4.5를 활용한 Vision 기반 UI 분석과
PyAutoGUI를 통한 자동화 액션 실행 프레임워크
"""

__version__ = "0.1.0"

from src.config_manager import ConfigManager
from src.game_process_manager import GameProcessManager
from src.input_monitor import InputMonitor, ActionRecorder, Action
from src.script_generator import ScriptGenerator
from src.qa_automation_controller import QAAutomationController
from src.cli_interface import CLIInterface
from src.ui_analyzer import UIAnalyzer
from src.semantic_action_recorder import SemanticAction, SemanticActionRecorder

__all__ = [
    'ConfigManager',
    'GameProcessManager',
    'InputMonitor',
    'ActionRecorder',
    'Action',
    'ScriptGenerator',
    'QAAutomationController',
    'CLIInterface',
    'UIAnalyzer',
    'SemanticAction',
    'SemanticActionRecorder',
]
