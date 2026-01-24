"""
의미론적 테스트 케이스 로더

테스트 케이스 JSON 파일들을 로드하여 SemanticTestCase 객체로 변환한다.

Requirements: 2.1, 2.2, 2.3
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from .models import SemanticTestCase, SemanticAction


logger = logging.getLogger(__name__)


class SemanticTestCaseLoader:
    """의미론적 테스트 케이스 로더
    
    테스트 케이스 JSON 파일을 로드하여 SemanticTestCase 객체로 변환한다.
    잘못된 파일은 건너뛰고 로깅한다.
    
    Requirements: 2.1, 2.2, 2.3
    """
    
    def load_file(self, file_path: str) -> Optional[SemanticTestCase]:
        """단일 테스트 케이스 파일 로드
        
        Args:
            file_path: JSON 파일 경로
            
        Returns:
            SemanticTestCase 객체 또는 None (파싱 실패 시)
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"파일이 존재하지 않음: {file_path}")
            return None
        
        if not path.suffix.lower() == '.json':
            logger.warning(f"JSON 파일이 아님: {file_path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._parse_test_case(data, str(path))
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 오류 ({file_path}): {e}")
            return None
        except Exception as e:
            logger.warning(f"파일 로드 오류 ({file_path}): {e}")
            return None
    
    def load_directory(self, dir_path: str) -> List[SemanticTestCase]:
        """디렉토리 내 모든 테스트 케이스 로드
        
        Args:
            dir_path: 테스트 케이스 디렉토리 경로
            
        Returns:
            SemanticTestCase 객체 리스트
        """
        path = Path(dir_path)
        
        if not path.exists():
            logger.warning(f"디렉토리가 존재하지 않음: {dir_path}")
            return []
        
        if not path.is_dir():
            logger.warning(f"디렉토리가 아님: {dir_path}")
            return []
        
        test_cases: List[SemanticTestCase] = []
        json_files = list(path.glob("*.json"))
        
        logger.info(f"디렉토리에서 {len(json_files)}개의 JSON 파일 발견: {dir_path}")
        
        for json_file in json_files:
            test_case = self.load_file(str(json_file))
            if test_case is not None:
                test_cases.append(test_case)
        
        logger.info(f"{len(test_cases)}개의 테스트 케이스 로드 완료")
        return test_cases
    
    def _parse_test_case(self, data: dict, json_path: str) -> Optional[SemanticTestCase]:
        """JSON 데이터를 SemanticTestCase로 변환
        
        Args:
            data: JSON 데이터 딕셔너리
            json_path: JSON 파일 경로
            
        Returns:
            SemanticTestCase 객체 또는 None
        """
        try:
            # 필수 필드 확인
            name = data.get("name", "")
            if not name:
                logger.warning(f"테스트 케이스 이름이 없음: {json_path}")
                return None
            
            created_at = data.get("created_at", "")
            actions_data = data.get("actions", [])
            
            # 액션 파싱
            actions = self._parse_actions(actions_data)
            
            return SemanticTestCase(
                name=name,
                created_at=created_at,
                actions=actions,
                json_path=json_path
            )
            
        except Exception as e:
            logger.warning(f"테스트 케이스 파싱 오류 ({json_path}): {e}")
            return None
    
    def _parse_actions(self, actions_data: list) -> List[SemanticAction]:
        """액션 리스트 파싱
        
        Args:
            actions_data: 액션 데이터 리스트
            
        Returns:
            SemanticAction 객체 리스트
        """
        actions: List[SemanticAction] = []
        
        for action_data in actions_data:
            try:
                action = SemanticAction.from_dict(action_data)
                actions.append(action)
            except Exception as e:
                logger.warning(f"액션 파싱 오류: {e}")
                continue
        
        return actions
