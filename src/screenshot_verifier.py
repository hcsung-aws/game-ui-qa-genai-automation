"""
ScreenshotVerifier - 스크린샷 비교 검증기

녹화 시 저장된 스크린샷과 replay 시 캡처한 스크린샷을 비교하여
화면 일치 여부를 판단한다.
"""

import os
import logging
from typing import Tuple, Optional
from PIL import Image
import imagehash

logger = logging.getLogger(__name__)


class ScreenshotVerifier:
    """스크린샷 비교 검증기"""
    
    def __init__(self, hash_threshold: int = 5):
        """
        Args:
            hash_threshold: 이미지 해시 차이 임계값 (낮을수록 엄격)
                           0: 완전 일치
                           1-5: 거의 일치
                           6-10: 유사
                           10+: 다름
        """
        self.hash_threshold = hash_threshold
    
    def compute_hash(self, image: Image.Image) -> imagehash.ImageHash:
        """이미지의 perceptual hash 계산
        
        Args:
            image: PIL Image 객체
            
        Returns:
            ImageHash 객체
        """
        return imagehash.phash(image)
    
    def compare_images(self, image1: Image.Image, image2: Image.Image) -> Tuple[bool, int, float]:
        """두 이미지 비교
        
        Args:
            image1: 첫 번째 이미지 (기준)
            image2: 두 번째 이미지 (비교 대상)
            
        Returns:
            (일치 여부, 해시 차이, 유사도 점수 0.0~1.0)
        """
        hash1 = self.compute_hash(image1)
        hash2 = self.compute_hash(image2)
        
        # 해시 차이 계산 (Hamming distance)
        hash_diff = hash1 - hash2
        
        # 유사도 점수 계산 (0~1, 1이 완전 일치)
        # phash는 64비트이므로 최대 차이는 64
        similarity = 1.0 - (hash_diff / 64.0)
        
        # 임계값 기준 일치 여부 판단
        is_match = hash_diff <= self.hash_threshold
        
        logger.debug(f"이미지 비교: hash_diff={hash_diff}, similarity={similarity:.3f}, match={is_match}")
        
        return is_match, hash_diff, similarity
    
    def compare_files(self, path1: str, path2: str) -> Tuple[bool, int, float]:
        """두 이미지 파일 비교
        
        Args:
            path1: 첫 번째 이미지 경로
            path2: 두 번째 이미지 경로
            
        Returns:
            (일치 여부, 해시 차이, 유사도 점수)
            
        Raises:
            FileNotFoundError: 파일이 없을 때
        """
        if not os.path.exists(path1):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없음: {path1}")
        if not os.path.exists(path2):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없음: {path2}")
        
        image1 = Image.open(path1)
        image2 = Image.open(path2)
        
        return self.compare_images(image1, image2)
    
    def verify_screenshot(self, expected_path: str, actual_image: Image.Image) -> dict:
        """스크린샷 검증
        
        Args:
            expected_path: 예상 스크린샷 경로 (녹화 시 저장된 것)
            actual_image: 실제 캡처된 이미지
            
        Returns:
            검증 결과 딕셔너리
            {
                "match": bool,
                "hash_diff": int,
                "similarity": float,
                "expected_path": str,
                "error": str (실패 시)
            }
        """
        result = {
            "match": False,
            "hash_diff": -1,
            "similarity": 0.0,
            "expected_path": expected_path,
            "error": ""
        }
        
        try:
            if not os.path.exists(expected_path):
                result["error"] = f"예상 스크린샷 없음: {expected_path}"
                logger.warning(result["error"])
                return result
            
            expected_image = Image.open(expected_path)
            is_match, hash_diff, similarity = self.compare_images(expected_image, actual_image)
            
            result["match"] = is_match
            result["hash_diff"] = hash_diff
            result["similarity"] = similarity
            
            if is_match:
                logger.info(f"스크린샷 일치: {expected_path} (similarity={similarity:.3f})")
            else:
                logger.warning(f"스크린샷 불일치: {expected_path} (hash_diff={hash_diff}, similarity={similarity:.3f})")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"스크린샷 검증 실패: {e}")
        
        return result
