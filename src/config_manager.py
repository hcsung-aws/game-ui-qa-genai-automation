"""
ConfigManager - 설정 파일 관리

Requirements: 1.4, 1.5, 10.1
"""

import json
import os
from typing import Any, Optional


class ConfigManager:
    """설정 파일 관리"""
    
    def __init__(self, config_path: str = 'config.json'):
        """
        Args:
            config_path: 설정 파일 경로
        """
        self.config_path = config_path
        self.config = {}
    
    def load_config(self) -> dict:
        """설정 파일 로드
        
        Returns:
            설정 딕셔너리
            
        Raises:
            FileNotFoundError: 설정 파일이 없을 때
            json.JSONDecodeError: JSON 형식이 잘못되었을 때
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        return self.config
    
    def create_default_config(self) -> dict:
        """기본 설정 생성
        
        Returns:
            기본 설정 딕셔너리
        """
        default_config = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "max_tokens": 2000,
                "retry_count": 3,
                "retry_delay": 1.0
            },
            "game": {
                "exe_path": "C:/path/to/game.exe",
                "window_title": "Game Window",
                "startup_wait": 5
            },
            "automation": {
                "action_delay": 0.5,
                "screenshot_on_action": True,
                "screenshot_dir": "screenshots",
                "verify_mode": False,
                "hash_threshold": 5
            },
            "test_cases": {
                "directory": "test_cases"
            }
        }
        
        # 파일로 저장
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        self.config = default_config
        return default_config
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """중첩된 키 경로로 설정값 가져오기
        
        Args:
            key_path: 점으로 구분된 키 경로 (예: 'aws.region')
            default: 키가 없을 때 반환할 기본값
            
        Returns:
            설정값 또는 기본값
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def save_config(self, config: Optional[dict] = None) -> None:
        """설정을 파일로 저장
        
        Args:
            config: 저장할 설정 딕셔너리 (None이면 현재 설정 저장)
        """
        if config is not None:
            self.config = config
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
