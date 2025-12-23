#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Game QA Automation System - 메인 진입점

게임 QA 자동화 시스템을 시작하는 메인 스크립트.
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.qa_automation_controller import QAAutomationController
from src.cli_interface import CLIInterface


def main():
    """메인 함수"""
    # 설정 파일 경로 (명령줄 인자로 지정 가능)
    config_path = 'config.json'
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    # 컨트롤러 초기화
    controller = QAAutomationController(config_path)
    
    if not controller.initialize():
        print("❌ 시스템 초기화에 실패했습니다.")
        sys.exit(1)
    
    # CLI 인터페이스 시작
    cli = CLIInterface(controller)
    
    try:
        cli.start_interactive_session()
    finally:
        # 리소스 정리
        controller.cleanup()


if __name__ == '__main__':
    main()
