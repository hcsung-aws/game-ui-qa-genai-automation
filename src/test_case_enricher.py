"""
TestCaseEnricher - 기존 테스트 케이스에 의미론적 정보를 추가하는 컴포넌트

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

from PIL import Image

from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer


logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    """보강 결과 데이터 클래스
    
    Requirements: 5.4, 5.5
    
    Attributes:
        total_actions: 전체 액션 수
        enriched_count: 보강 성공한 액션 수
        skipped_count: 스크린샷 누락 등으로 스킵된 액션 수
        failed_count: 보강 실패한 액션 수
        version: 보강 후 버전 식별자
    """
    total_actions: int
    enriched_count: int
    skipped_count: int
    failed_count: int
    version: str


class TestCaseEnricher:
    """테스트 케이스 보강기
    
    기존 테스트 케이스에 의미론적 정보를 추가하여
    의미론적 재현이 가능하도록 한다.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """
    
    def __init__(self, config: ConfigManager, ui_analyzer: Optional[UIAnalyzer] = None):
        """
        Args:
            config: 설정 관리자
            ui_analyzer: UI 분석기 (선택사항, 없으면 새로 생성)
        """
        self.config = config
        self.ui_analyzer = ui_analyzer or UIAnalyzer(config)
    
    def is_legacy_test_case(self, test_case: Dict[str, Any]) -> bool:
        """레거시 테스트 케이스 여부 확인
        
        semantic_info 필드가 누락되었거나 비어있는 클릭 액션이
        하나라도 있으면 레거시로 판단한다.
        
        Requirements: 5.1
        
        Args:
            test_case: 테스트 케이스 딕셔너리
            
        Returns:
            레거시 테스트 케이스이면 True, 아니면 False
        """
        actions = test_case.get("actions", [])
        
        for action in actions:
            action_type = action.get("action_type", "")
            
            # 클릭 액션만 검사
            if action_type == "click":
                semantic_info = action.get("semantic_info")
                
                # semantic_info가 없거나 비어있으면 레거시
                if semantic_info is None or semantic_info == {}:
                    return True
                
                # target_element가 없거나 비어있으면 레거시
                target_element = semantic_info.get("target_element")
                if target_element is None or target_element == {}:
                    return True
        
        return False

    def _enrich_action(
        self, 
        action: Dict[str, Any], 
        screenshot_dir: str
    ) -> Tuple[Dict[str, Any], str]:
        """단일 액션 보강
        
        스크린샷 파일을 로드하고 Vision LLM으로 분석하여
        semantic_info 필드를 추가한다. 기존 필드는 모두 유지한다.
        
        Requirements: 5.2, 5.3, 5.6
        
        Args:
            action: 보강할 액션 딕셔너리
            screenshot_dir: 스크린샷 디렉토리 경로
            
        Returns:
            (보강된 액션, 상태) 튜플
            상태: "enriched", "skipped", "failed"
        """
        # 기존 필드 모두 복사하여 보존 (Requirements: 5.6)
        enriched_action = dict(action)
        
        # 클릭 액션이 아니면 그대로 반환
        if action.get("action_type") != "click":
            return enriched_action, "skipped"
        
        # 이미 semantic_info가 있고 유효하면 스킵
        existing_semantic = action.get("semantic_info", {})
        if existing_semantic and existing_semantic.get("target_element"):
            return enriched_action, "skipped"
        
        # 스크린샷 경로 결정 (screenshot_before_path 우선, 없으면 screenshot_path)
        screenshot_path = action.get("screenshot_before_path") or action.get("screenshot_path")
        
        if not screenshot_path:
            logger.warning(f"액션에 스크린샷 경로가 없습니다: {action.get('description', 'unknown')}")
            enriched_action["enrichment_status"] = "skipped"
            return enriched_action, "skipped"
        
        # 절대 경로 또는 상대 경로 처리
        if not os.path.isabs(screenshot_path):
            full_path = os.path.join(screenshot_dir, os.path.basename(screenshot_path))
        else:
            full_path = screenshot_path
        
        # 스크린샷 파일 존재 확인
        if not os.path.exists(full_path):
            logger.warning(f"스크린샷 파일이 없습니다: {full_path}")
            enriched_action["enrichment_status"] = "skipped"
            return enriched_action, "skipped"
        
        try:
            # 스크린샷 로드
            image = Image.open(full_path)
            
            # Vision LLM으로 분석
            ui_data = self.ui_analyzer.analyze_with_retry(image)
            
            # 클릭 좌표에서 UI 요소 찾기
            x = action.get("x", 0)
            y = action.get("y", 0)
            
            target_element = self._find_target_element(ui_data, x, y)
            
            # semantic_info 구성
            enriched_action["semantic_info"] = {
                "intent": self._infer_intent(action, target_element),
                "target_element": target_element,
                "context": {
                    "screen_state": "enriched",
                    "expected_result": "unknown"
                }
            }
            
            enriched_action["enrichment_status"] = "enriched"
            logger.info(f"액션 보강 성공: ({x}, {y}) -> {target_element.get('text', 'unknown')}")
            return enriched_action, "enriched"
            
        except Exception as e:
            logger.error(f"액션 보강 실패: {e}")
            enriched_action["enrichment_status"] = "failed"
            return enriched_action, "failed"
    
    def _find_target_element(
        self, 
        ui_data: Dict[str, Any], 
        x: int, 
        y: int
    ) -> Dict[str, Any]:
        """클릭 좌표에서 가장 가까운 UI 요소 찾기
        
        Args:
            ui_data: UI 분석 결과
            x: X 좌표
            y: Y 좌표
            
        Returns:
            target_element 딕셔너리
        """
        # UIAnalyzer의 find_element_at_position 활용
        element = self.ui_analyzer.find_element_at_position(ui_data, x, y, tolerance=100)
        
        if element:
            return {
                "type": element.get("element_type", element.get("type", "unknown")),
                "text": element.get("text", element.get("content", "")),
                "description": element.get("description", ""),
                "bounding_box": element.get("bounding_box", {"x": x, "y": y, "width": 0, "height": 0}),
                "confidence": element.get("confidence", 0.0)
            }
        
        # 요소를 찾지 못한 경우 기본값 반환
        return {
            "type": "unknown",
            "text": "",
            "description": f"좌표 ({x}, {y})의 알 수 없는 요소",
            "bounding_box": {"x": x, "y": y, "width": 0, "height": 0},
            "confidence": 0.0
        }
    
    def _infer_intent(self, action: Dict[str, Any], target_element: Dict[str, Any]) -> str:
        """액션의 의도 추론
        
        Args:
            action: 액션 딕셔너리
            target_element: 타겟 UI 요소 정보
            
        Returns:
            추론된 의도 문자열
        """
        element_type = target_element.get('type', 'unknown')
        element_text = target_element.get('text', '').lower()
        
        # 버튼 클릭 의도 추론
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
        
        # 텍스트 필드 클릭 의도
        elif element_type == 'text_field':
            return 'focus_input'
        
        # 아이콘 클릭 의도
        elif element_type == 'icon':
            return 'click_icon'
        
        return 'unknown_action'

    def enrich_test_case(
        self, 
        test_case: Dict[str, Any], 
        screenshot_dir: str
    ) -> Tuple[Dict[str, Any], EnrichmentResult]:
        """테스트 케이스에 의미론적 정보 추가
        
        모든 클릭 액션에 대해 스크린샷을 분석하여 semantic_info를 추가한다.
        스크린샷이 누락된 액션은 스킵하고, 기존 데이터는 모두 유지한다.
        
        Requirements: 5.2, 5.3, 5.4, 5.5, 5.6
        
        Args:
            test_case: 보강할 테스트 케이스 딕셔너리
            screenshot_dir: 스크린샷 디렉토리 경로
            
        Returns:
            (보강된 테스트 케이스, EnrichmentResult) 튜플
        """
        # 기존 테스트 케이스 복사 (원본 보존)
        enriched_test_case = dict(test_case)
        
        # 통계 초기화
        total_actions = 0
        enriched_count = 0
        skipped_count = 0
        failed_count = 0
        
        # 액션 리스트 보강
        enriched_actions = []
        actions = test_case.get("actions", [])
        
        for action in actions:
            total_actions += 1
            
            # 액션 보강
            enriched_action, status = self._enrich_action(action, screenshot_dir)
            enriched_actions.append(enriched_action)
            
            # 통계 업데이트
            if status == "enriched":
                enriched_count += 1
            elif status == "skipped":
                skipped_count += 1
            elif status == "failed":
                failed_count += 1
        
        # 보강된 액션 리스트 설정
        enriched_test_case["actions"] = enriched_actions
        
        # 버전 식별자 업데이트 (Requirements: 5.4)
        old_version = test_case.get("version", "1.0")
        new_version = self._increment_version(old_version)
        enriched_test_case["version"] = new_version
        
        # 보강 시간 기록
        enriched_test_case["enriched_at"] = datetime.now().isoformat()
        
        # 결과 생성
        result = EnrichmentResult(
            total_actions=total_actions,
            enriched_count=enriched_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            version=new_version
        )
        
        logger.info(f"테스트 케이스 보강 완료: 전체 {total_actions}, "
                   f"보강 {enriched_count}, 스킵 {skipped_count}, 실패 {failed_count}")
        
        return enriched_test_case, result
    
    def _increment_version(self, version: str) -> str:
        """버전 번호 증가
        
        Args:
            version: 현재 버전 문자열 (예: "1.0", "2.1")
            
        Returns:
            증가된 버전 문자열
        """
        try:
            parts = version.split(".")
            if len(parts) >= 2:
                major = int(parts[0])
                minor = int(parts[1])
                return f"{major}.{minor + 1}"
            else:
                return f"{version}.1"
        except (ValueError, IndexError):
            return "2.0"
