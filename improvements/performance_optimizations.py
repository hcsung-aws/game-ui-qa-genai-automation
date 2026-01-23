"""
성능 최적화 개선 사항

이 파일은 게임 QA 자동화 프레임워크의 성능 최적화 방안을 포함합니다.
"""

import hashlib
import time
from typing import Dict, Optional, Any
from collections import OrderedDict


class LRUCache:
    """LRU (Least Recently Used) 캐시 구현"""
    
    def __init__(self, max_size: int = 100):
        """
        Args:
            max_size: 최대 캐시 크기
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if key in self.cache:
            # 최근 사용으로 이동
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any) -> None:
        """캐시에 값 저장"""
        if key in self.cache:
            # 기존 값 업데이트
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.max_size:
            # 가장 오래된 항목 제거
            self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self) -> None:
        """캐시 초기화"""
        self.cache.clear()
    
    def size(self) -> int:
        """현재 캐시 크기"""
        return len(self.cache)


class VisionLLMCache:
    """Vision LLM 결과 캐싱 시스템"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Args:
            max_size: 최대 캐시 크기
            ttl_seconds: 캐시 유효 시간 (초)
        """
        self.cache = LRUCache(max_size)
        self.ttl_seconds = ttl_seconds
        self.timestamps: Dict[str, float] = {}
    
    def _generate_cache_key(self, image_hash: str, prompt: str) -> str:
        """캐시 키 생성"""
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        return f"{image_hash}:{prompt_hash}"
    
    def _is_expired(self, key: str) -> bool:
        """캐시 만료 여부 확인"""
        if key not in self.timestamps:
            return True
        
        return (time.time() - self.timestamps[key]) > self.ttl_seconds
    
    def get_cached_result(self, image_hash: str, prompt: str) -> Optional[Dict]:
        """캐시된 결과 조회"""
        cache_key = self._generate_cache_key(image_hash, prompt)
        
        if self._is_expired(cache_key):
            self._remove_expired_entry(cache_key)
            return None
        
        return self.cache.get(cache_key)
    
    def cache_result(self, image_hash: str, prompt: str, result: Dict) -> None:
        """결과 캐싱"""
        cache_key = self._generate_cache_key(image_hash, prompt)
        
        self.cache.put(cache_key, result)
        self.timestamps[cache_key] = time.time()
    
    def _remove_expired_entry(self, key: str) -> None:
        """만료된 항목 제거"""
        if key in self.timestamps:
            del self.timestamps[key]
    
    def cleanup_expired(self) -> int:
        """만료된 캐시 항목 정리"""
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.timestamps.items():
            if (current_time - timestamp) > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_expired_entry(key)
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        return {
            "cache_size": self.cache.size(),
            "max_size": self.cache.max_size,
            "ttl_seconds": self.ttl_seconds,
            "active_entries": len(self.timestamps)
        }


class ImageHashGenerator:
    """이미지 해시 생성기"""
    
    @staticmethod
    def generate_file_hash(file_path: str) -> str:
        """파일 해시 생성"""
        hash_md5 = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                # 큰 파일을 위한 청크 단위 읽기
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except (IOError, OSError) as e:
            raise ValueError(f"파일 해시 생성 실패: {e}")
        
        return hash_md5.hexdigest()
    
    @staticmethod
    def generate_content_hash(content: bytes) -> str:
        """콘텐츠 해시 생성"""
        return hashlib.md5(content).hexdigest()


class PerformanceMonitor:
    """성능 모니터링 유틸리티"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
    
    def record_execution_time(self, operation: str, execution_time: float) -> None:
        """실행 시간 기록"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(execution_time)
    
    def get_average_time(self, operation: str) -> Optional[float]:
        """평균 실행 시간 조회"""
        if operation not in self.metrics or not self.metrics[operation]:
            return None
        
        times = self.metrics[operation]
        return sum(times) / len(times)
    
    def get_stats(self, operation: str) -> Optional[Dict[str, float]]:
        """상세 통계 정보"""
        if operation not in self.metrics or not self.metrics[operation]:
            return None
        
        times = self.metrics[operation]
        return {
            "count": len(times),
            "average": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "total": sum(times)
        }
    
    def clear_metrics(self, operation: Optional[str] = None) -> None:
        """메트릭 초기화"""
        if operation:
            self.metrics.pop(operation, None)
        else:
            self.metrics.clear()


def timing_decorator(monitor: PerformanceMonitor, operation_name: str):
    """실행 시간 측정 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                monitor.record_execution_time(operation_name, execution_time)
        return wrapper
    return decorator


class BatchProcessor:
    """배치 처리 유틸리티"""
    
    @staticmethod
    def process_in_batches(items: list, batch_size: int, processor_func):
        """항목들을 배치 단위로 처리"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = processor_func(batch)
            results.extend(batch_results)
        
        return results
    
    @staticmethod
    def chunk_list(items: list, chunk_size: int) -> list:
        """리스트를 청크 단위로 분할"""
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

