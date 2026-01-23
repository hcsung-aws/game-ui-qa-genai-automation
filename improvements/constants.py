"""
상수 관리 개선 사항

이 파일은 게임 QA 자동화 프레임워크의 상수들을 중앙화하여 관리합니다.
"""

from enum import Enum
from typing import Final


class Config:
    """설정 관련 상수"""
    
    # 기본 지연 시간 (초)
    DEFAULT_ACTION_DELAY: Final[float] = 0.5
    DEFAULT_CAPTURE_DELAY: Final[float] = 2.0
    DEFAULT_STARTUP_WAIT: Final[int] = 5
    
    # 재시도 설정
    DEFAULT_RETRY_COUNT: Final[int] = 3
    DEFAULT_RETRY_DELAY: Final[float] = 1.0
    MAX_RETRY_ATTEMPTS: Final[int] = 5
    
    # 임계값 설정
    DEFAULT_HASH_THRESHOLD: Final[int] = 5
    DEFAULT_SIMILARITY_THRESHOLD: Final[float] = 0.8
    SEMANTIC_CONFIDENCE_THRESHOLD: Final[float] = 0.7
    
    # AWS 설정
    DEFAULT_AWS_REGION: Final[str] = "ap-northeast-2"
    DEFAULT_MODEL_ID: Final[str] = "anthropic.claude-sonnet-4-5-20250929-v1:0"
    DEFAULT_MAX_TOKENS: Final[int] = 2000
    
    # 캐시 설정
    DEFAULT_CACHE_SIZE: Final[int] = 100
    DEFAULT_CACHE_TTL: Final[int] = 3600  # 1시간
    
    # 파일 크기 제한
    MAX_SCREENSHOT_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
    MAX_LOG_FILE_SIZE: Final[int] = 50 * 1024 * 1024   # 50MB
    MAX_TEST_CASE_NAME_LENGTH: Final[int] = 100


class Paths:
    """경로 관련 상수"""
    
    # 기본 디렉토리
    DEFAULT_CONFIG_FILE: Final[str] = "config.json"
    DEFAULT_SCREENSHOT_DIR: Final[str] = "screenshots"
    DEFAULT_TEST_CASES_DIR: Final[str] = "test_cases"
    DEFAULT_REPORTS_DIR: Final[str] = "reports"
    DEFAULT_LOGS_DIR: Final[str] = "logs"
    
    # 파일 확장자
    JSON_EXTENSION: Final[str] = ".json"
    PYTHON_EXTENSION: Final[str] = ".py"
    PNG_EXTENSION: Final[str] = ".png"
    TXT_EXTENSION: Final[str] = ".txt"
    
    # 허용된 실행 파일 확장자
    ALLOWED_EXECUTABLE_EXTENSIONS: Final[tuple] = ('.exe', '.app', '.bin')


class Messages:
    """메시지 관련 상수"""
    
    # 성공 메시지
    INIT_SUCCESS: Final[str] = "✓ 시스템 초기화 성공"
    GAME_START_SUCCESS: Final[str] = "✓ 게임 시작 성공"
    RECORDING_START_SUCCESS: Final[str] = "✓ 입력 기록 시작"
    RECORDING_STOP_SUCCESS: Final[str] = "✓ 입력 기록 중지"
    TEST_CASE_SAVE_SUCCESS: Final[str] = "✓ 테스트 케이스 저장 완료"
    TEST_CASE_LOAD_SUCCESS: Final[str] = "✓ 테스트 케이스 로드 완료"
    REPLAY_SUCCESS: Final[str] = "✓ 테스트 케이스 재실행 완료"
    
    # 오류 메시지
    INIT_FAILED: Final[str] = "❌ 시스템 초기화 실패"
    GAME_START_FAILED: Final[str] = "❌ 게임 시작 실패"
    CONFIG_FILE_NOT_FOUND: Final[str] = "❌ 설정 파일을 찾을 수 없습니다"
    TEST_CASE_NOT_FOUND: Final[str] = "❌ 테스트 케이스를 찾을 수 없습니다"
    INVALID_TEST_CASE_NAME: Final[str] = "❌ 유효하지 않은 테스트 케이스 이름입니다"
    PERMISSION_DENIED: Final[str] = "❌ 권한이 없습니다"
    
    # 경고 메시지
    NO_ACTIONS_RECORDED: Final[str] = "⚠ 기록된 액션이 없습니다"
    LOW_SIMILARITY_WARNING: Final[str] = "⚠ 스크린샷 유사도가 낮습니다"
    VISION_LLM_FALLBACK: Final[str] = "⚠ Vision LLM 분석 실패, 원래 좌표로 폴백"


class ActionTypes:
    """액션 타입 상수"""
    
    CLICK: Final[str] = "click"
    KEY_PRESS: Final[str] = "key_press"
    SCROLL: Final[str] = "scroll"
    WAIT: Final[str] = "wait"
    SCREENSHOT: Final[str] = "screenshot"


class TestResults:
    """테스트 결과 상수"""
    
    PASS: Final[str] = "pass"
    FAIL: Final[str] = "fail"
    WARNING: Final[str] = "warning"
    SKIP: Final[str] = "skip"


class LogLevels:
    """로그 레벨 상수"""
    
    DEBUG: Final[str] = "DEBUG"
    INFO: Final[str] = "INFO"
    WARNING: Final[str] = "WARNING"
    ERROR: Final[str] = "ERROR"
    CRITICAL: Final[str] = "CRITICAL"


class ErrorCodes:
    """오류 코드 상수"""
    
    # 설정 관련 오류
    CONFIG_FILE_NOT_FOUND: Final[str] = "E001"
    CONFIG_INVALID_FORMAT: Final[str] = "E002"
    CONFIG_PERMISSION_DENIED: Final[str] = "E003"
    
    # 게임 프로세스 관련 오류
    GAME_EXE_NOT_FOUND: Final[str] = "E101"
    GAME_PERMISSION_DENIED: Final[str] = "E102"
    GAME_PROCESS_ERROR: Final[str] = "E103"
    
    # Vision LLM 관련 오류
    VISION_AUTH_ERROR: Final[str] = "E201"
    VISION_RATE_LIMIT: Final[str] = "E202"
    VISION_TIMEOUT: Final[str] = "E203"
    VISION_UNKNOWN_ERROR: Final[str] = "E204"
    
    # 테스트 케이스 관련 오류
    TEST_CASE_NOT_FOUND: Final[str] = "E301"
    TEST_CASE_INVALID_FORMAT: Final[str] = "E302"
    TEST_CASE_SAVE_ERROR: Final[str] = "E303"
    
    # 스크린샷 관련 오류
    SCREENSHOT_PERMISSION_DENIED: Final[str] = "E401"
    SCREENSHOT_FILE_NOT_FOUND: Final[str] = "E402"
    SCREENSHOT_CAPTURE_ERROR: Final[str] = "E403"


class UIElements:
    """UI 요소 타입 상수"""
    
    BUTTON: Final[str] = "button"
    TEXT_INPUT: Final[str] = "text_input"
    CHECKBOX: Final[str] = "checkbox"
    DROPDOWN: Final[str] = "dropdown"
    MENU_ITEM: Final[str] = "menu_item"
    ICON: Final[str] = "icon"
    LINK: Final[str] = "link"
    IMAGE: Final[str] = "image"
    UNKNOWN: Final[str] = "unknown"


class FilePatterns:
    """파일 패턴 상수"""
    
    # 날짜/시간 패턴
    TIMESTAMP_FORMAT: Final[str] = "%Y%m%d_%H%M%S"
    ISO_TIMESTAMP_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S"
    
    # 파일명 패턴
    SCREENSHOT_PATTERN: Final[str] = "screenshot_{timestamp}.png"
    REPORT_PATTERN: Final[str] = "{test_name}_{timestamp}_report"
    LOG_PATTERN: Final[str] = "game_qa_{date}.log"
    
    # 정규식 패턴
    VALID_FILENAME_PATTERN: Final[str] = r'^[a-zA-Z0-9_\-\.]+$'
    INVALID_CHARS_PATTERN: Final[str] = r'[<>:"/\\|?*\x00-\x1f]'

