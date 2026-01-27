"""
자동 플레이 테스트 생성기

MatchResult를 바탕으로 PlayTestCase를 생성하고 실행한다.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable

from .models import (
    MatchResult,
    PlayTestCase,
    PlayTestResult,
    BVTReference,
    SemanticAction,
    SemanticTestCase,
    TestStatus
)
from .tc_loader import SemanticTestCaseLoader


logger = logging.getLogger(__name__)


class AutoPlayGenerator:
    """자동 플레이 테스트 생성기
    
    MatchResult로부터 PlayTestCase를 생성하고,
    SemanticActionReplayer를 활용하여 실행한다.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
    """
    
    def __init__(
        self,
        replayer=None,
        config=None,
        tc_loader: Optional[SemanticTestCaseLoader] = None,
        screenshot_dir: str = "screenshots"
    ):
        """
        Args:
            replayer: SemanticActionReplayer 인스턴스 (선택사항)
            config: ConfigManager 인스턴스 (선택사항)
            tc_loader: SemanticTestCaseLoader 인스턴스 (선택사항)
            screenshot_dir: 스크린샷 저장 디렉토리
        """
        self.replayer = replayer
        self.config = config
        self.tc_loader = tc_loader or SemanticTestCaseLoader()
        self.screenshot_dir = screenshot_dir
        self._test_cases_cache: dict = {}
    
    def generate(self, match_result: MatchResult) -> Optional[PlayTestCase]:
        """매칭 결과로부터 플레이 테스트 케이스 생성
        
        Requirements: 4.1, 4.2, 4.3, 4.7
        
        Args:
            match_result: 매칭 결과
            
        Returns:
            PlayTestCase 객체 또는 None (생성 실패 시)
        """
        # 고신뢰도 매칭만 처리 (Requirements: 4.1)
        if not match_result.is_high_confidence:
            logger.warning(
                f"저신뢰도 매칭은 플레이 테스트 생성 불가: "
                f"BVT #{match_result.bvt_case.no}, "
                f"신뢰도 {match_result.confidence_score:.2f}"
            )
            return None
        
        if not match_result.is_matched:
            logger.warning(f"매칭되지 않은 결과: BVT #{match_result.bvt_case.no}")
            return None
        
        if match_result.action_range is None:
            logger.warning(
                f"액션 범위가 없음: BVT #{match_result.bvt_case.no}"
            )
            return None
        
        # BVT 참조 정보 생성 (Requirements: 4.3)
        bvt_ref = BVTReference(
            no=match_result.bvt_case.no,
            category1=match_result.bvt_case.category1,
            category2=match_result.bvt_case.category2,
            category3=match_result.bvt_case.category3,
            check=match_result.bvt_case.check
        )
        
        # 원본 테스트 케이스에서 액션 추출 (Requirements: 4.2)
        source_tc_name = match_result.matched_test_case
        actions = self._extract_actions(
            source_tc_name,
            match_result.action_range.start_index,
            match_result.action_range.end_index
        )
        
        if not actions:
            logger.warning(
                f"액션 추출 실패: {source_tc_name}, "
                f"범위 [{match_result.action_range.start_index}, "
                f"{match_result.action_range.end_index}]"
            )
            return None
        
        # 플레이 테스트 케이스 생성
        play_test_name = self._generate_play_test_name(match_result)
        
        play_test = PlayTestCase(
            name=play_test_name,
            bvt_reference=bvt_ref,
            source_test_case=source_tc_name,
            actions=actions,
            created_at=datetime.now().isoformat()
        )
        
        logger.info(
            f"플레이 테스트 생성 완료: {play_test_name}, "
            f"액션 수: {len(actions)}"
        )
        
        return play_test
    
    def generate_from_test_case(
        self,
        match_result: MatchResult,
        test_case: SemanticTestCase
    ) -> Optional[PlayTestCase]:
        """테스트 케이스 객체로부터 직접 플레이 테스트 생성
        
        Requirements: 4.1, 4.2, 4.3, 4.7
        
        Args:
            match_result: 매칭 결과
            test_case: 원본 테스트 케이스 객체
            
        Returns:
            PlayTestCase 객체 또는 None
        """
        # 고신뢰도 매칭만 처리
        if not match_result.is_high_confidence:
            logger.warning(
                f"저신뢰도 매칭은 플레이 테스트 생성 불가: "
                f"BVT #{match_result.bvt_case.no}"
            )
            return None
        
        if match_result.action_range is None:
            logger.warning(f"액션 범위가 없음: BVT #{match_result.bvt_case.no}")
            return None
        
        # BVT 참조 정보 생성
        bvt_ref = BVTReference(
            no=match_result.bvt_case.no,
            category1=match_result.bvt_case.category1,
            category2=match_result.bvt_case.category2,
            category3=match_result.bvt_case.category3,
            check=match_result.bvt_case.check
        )
        
        # 액션 범위 추출
        start_idx = match_result.action_range.start_index
        end_idx = match_result.action_range.end_index
        
        # 범위 검증
        if start_idx < 0 or end_idx >= len(test_case.actions):
            logger.warning(
                f"액션 범위 초과: [{start_idx}, {end_idx}], "
                f"총 액션 수: {len(test_case.actions)}"
            )
            # 범위 조정
            start_idx = max(0, start_idx)
            end_idx = min(end_idx, len(test_case.actions) - 1)
        
        if start_idx > end_idx:
            logger.warning(f"잘못된 액션 범위: [{start_idx}, {end_idx}]")
            return None
        
        # 액션 추출 (end_idx 포함)
        actions = test_case.actions[start_idx:end_idx + 1]
        
        if not actions:
            logger.warning("추출된 액션이 없음")
            return None
        
        # 플레이 테스트 케이스 생성
        play_test_name = self._generate_play_test_name(match_result)
        
        return PlayTestCase(
            name=play_test_name,
            bvt_reference=bvt_ref,
            source_test_case=test_case.name,
            actions=actions,
            created_at=datetime.now().isoformat()
        )
    
    def execute(
        self,
        play_test: PlayTestCase,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> PlayTestResult:
        """플레이 테스트 실행
        
        Requirements: 4.4, 4.5, 4.6, 4.7
        
        Args:
            play_test: 실행할 플레이 테스트
            progress_callback: 진행 콜백 (current, total, message)
            
        Returns:
            PlayTestResult 객체
        """
        start_time = time.time()
        executed_actions = 0
        failed_actions = 0
        screenshots: List[str] = []
        error_message: Optional[str] = None
        
        logger.info(f"플레이 테스트 실행 시작: {play_test.name}")
        
        try:
            total_actions = len(play_test.actions)
            
            for i, action in enumerate(play_test.actions):
                if progress_callback:
                    progress_callback(
                        i + 1, 
                        total_actions, 
                        f"액션 {i + 1}/{total_actions}: {action.description}"
                    )
                
                try:
                    # 액션 실행 (Requirements: 4.5)
                    result = self._execute_action(action, i)
                    executed_actions += 1
                    
                    # 스크린샷 캡처 (Requirements: 4.4)
                    screenshot_path = self._capture_screenshot(play_test.name, i)
                    if screenshot_path:
                        screenshots.append(screenshot_path)
                    
                    if not result:
                        failed_actions += 1
                        logger.warning(f"액션 {i + 1} 실패: {action.description}")
                        # 실패해도 계속 진행 (Requirements: 4.6)
                    
                except Exception as e:
                    # 개별 액션 실패 처리 (Requirements: 4.6)
                    failed_actions += 1
                    executed_actions += 1
                    logger.warning(f"액션 {i + 1} 실행 오류: {e}")
                    continue
            
            # 테스트 결과 판정 (Requirements: 4.7)
            if failed_actions == 0:
                status = TestStatus.PASS
            elif failed_actions == total_actions:
                status = TestStatus.BLOCKED
            else:
                status = TestStatus.FAIL
                error_message = f"{failed_actions}개 액션 실패"
        
        except Exception as e:
            status = TestStatus.BLOCKED
            error_message = str(e)
            logger.error(f"플레이 테스트 실행 오류: {e}")
        
        execution_time = time.time() - start_time
        
        result = PlayTestResult(
            play_test_name=play_test.name,
            bvt_no=play_test.bvt_reference.no,
            status=status,
            executed_actions=executed_actions,
            failed_actions=failed_actions,
            screenshots=screenshots,
            error_message=error_message,
            execution_time=execution_time
        )
        
        logger.info(
            f"플레이 테스트 완료: {play_test.name}, "
            f"상태: {status.value}, "
            f"실행 시간: {execution_time:.2f}초"
        )
        
        return result
    
    def save_play_test(
        self,
        play_test: PlayTestCase,
        output_dir: str
    ) -> str:
        """플레이 테스트를 JSON 파일로 저장
        
        Requirements: 4.8
        
        Args:
            play_test: 저장할 플레이 테스트
            output_dir: 출력 디렉토리
            
        Returns:
            저장된 파일 경로
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_name = f"{play_test.name}.json"
        file_path = output_path / file_name
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(play_test.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"플레이 테스트 저장: {file_path}")
        return str(file_path)
    
    def load_play_test(self, file_path: str) -> Optional[PlayTestCase]:
        """JSON 파일에서 플레이 테스트 로드
        
        Args:
            file_path: JSON 파일 경로
            
        Returns:
            PlayTestCase 객체 또는 None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return PlayTestCase.from_dict(data)
        except Exception as e:
            logger.error(f"플레이 테스트 로드 실패: {e}")
            return None
    
    def load_test_case(self, json_path: str) -> Optional[SemanticTestCase]:
        """테스트 케이스 파일 로드 (캐싱 적용)
        
        Args:
            json_path: JSON 파일 경로
            
        Returns:
            SemanticTestCase 객체 또는 None
        """
        if json_path in self._test_cases_cache:
            return self._test_cases_cache[json_path]
        
        test_case = self.tc_loader.load_file(json_path)
        if test_case:
            self._test_cases_cache[json_path] = test_case
        
        return test_case
    
    def _extract_actions(
        self,
        test_case_name: str,
        start_index: int,
        end_index: int
    ) -> List[SemanticAction]:
        """원본 테스트 케이스에서 액션 범위 추출
        
        Args:
            test_case_name: 테스트 케이스 이름
            start_index: 시작 인덱스
            end_index: 종료 인덱스 (포함)
            
        Returns:
            SemanticAction 리스트
        """
        # 캐시에서 테스트 케이스 찾기
        for tc in self._test_cases_cache.values():
            if tc.name == test_case_name:
                if start_index < 0 or end_index >= len(tc.actions):
                    logger.warning(
                        f"액션 범위 초과: [{start_index}, {end_index}], "
                        f"총 액션 수: {len(tc.actions)}"
                    )
                    start_index = max(0, start_index)
                    end_index = min(end_index, len(tc.actions) - 1)
                
                return tc.actions[start_index:end_index + 1]
        
        logger.warning(f"테스트 케이스를 찾을 수 없음: {test_case_name}")
        return []
    
    def _generate_play_test_name(self, match_result: MatchResult) -> str:
        """플레이 테스트 이름 생성
        
        Args:
            match_result: 매칭 결과
            
        Returns:
            플레이 테스트 이름
        """
        bvt_no = match_result.bvt_case.no
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"bvt_{bvt_no:04d}_play_{timestamp}"
    
    def _execute_action(self, action: SemanticAction, index: int) -> bool:
        """단일 액션 실행
        
        Args:
            action: 실행할 액션
            index: 액션 인덱스
            
        Returns:
            성공 여부
        """
        if self.replayer is None:
            logger.warning("Replayer가 설정되지 않음, 액션 실행 건너뜀")
            return True  # 테스트 모드에서는 성공으로 처리
        
        try:
            # SemanticActionReplayer의 replay_action 사용
            from src.semantic_action_recorder import SemanticAction as RecorderAction
            
            # 모델 변환 (bvt_integration.models -> semantic_action_recorder)
            recorder_action = RecorderAction(
                timestamp=action.timestamp,
                action_type=action.action_type,
                x=action.x,
                y=action.y,
                description=action.description,
                screenshot_path=action.screenshot_path,
                button=action.button,
                key=action.key,
                scroll_dx=action.scroll_dx,
                scroll_dy=action.scroll_dy,
                screenshot_before_path=action.screenshot_before_path,
                screenshot_after_path=action.screenshot_after_path,
                click_region_crop_path=action.click_region_crop_path,
                ui_state_hash_before=action.ui_state_hash_before,
                ui_state_hash_after=action.ui_state_hash_after,
                semantic_info=action.semantic_info,
                screen_transition=action.screen_transition
            )
            
            result = self.replayer.replay_action(recorder_action)
            return result.success
            
        except Exception as e:
            logger.error(f"액션 실행 오류: {e}")
            return False
    
    def _capture_screenshot(self, test_name: str, action_index: int) -> Optional[str]:
        """스크린샷 캡처
        
        Args:
            test_name: 테스트 이름
            action_index: 액션 인덱스
            
        Returns:
            스크린샷 파일 경로 또는 None
        """
        try:
            import pyautogui
            
            screenshot_path = Path(self.screenshot_dir)
            screenshot_path.mkdir(parents=True, exist_ok=True)
            
            file_name = f"{test_name}_action_{action_index:04d}.png"
            file_path = screenshot_path / file_name
            
            screenshot = pyautogui.screenshot()
            screenshot.save(str(file_path))
            
            return str(file_path)
            
        except Exception as e:
            logger.warning(f"스크린샷 캡처 실패: {e}")
            return None
    
    def cache_test_case(self, test_case: SemanticTestCase) -> None:
        """테스트 케이스를 캐시에 추가
        
        Args:
            test_case: 캐시할 테스트 케이스
        """
        self._test_cases_cache[test_case.json_path] = test_case
    
    def clear_cache(self) -> None:
        """테스트 케이스 캐시 초기화"""
        self._test_cases_cache.clear()
