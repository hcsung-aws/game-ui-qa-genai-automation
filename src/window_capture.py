"""
WindowCapture - 특정 윈도우 캡처 유틸리티

Windows에서 특정 프로세스의 창만 캡처하는 기능을 제공한다.
"""

import logging
from typing import Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)

# Windows 전용 모듈 지연 로딩
_win32gui = None
_win32ui = None
_win32con = None


def _load_win32_modules():
    """Win32 모듈 지연 로딩"""
    global _win32gui, _win32ui, _win32con
    
    if _win32gui is None:
        try:
            import win32gui
            import win32ui
            import win32con
            _win32gui = win32gui
            _win32ui = win32ui
            _win32con = win32con
            return True
        except ImportError:
            logger.warning("pywin32가 설치되지 않았습니다. pip install pywin32")
            return False
    return True


class WindowCapture:
    """특정 윈도우 캡처 클래스"""
    
    def __init__(self, window_title: str = None):
        """
        Args:
            window_title: 캡처할 윈도우 제목 (부분 일치)
        """
        self.window_title = window_title
        self._hwnd = None
    
    def find_window(self, title: str = None) -> Optional[int]:
        """윈도우 핸들 찾기
        
        Args:
            title: 윈도우 제목 (부분 일치)
            
        Returns:
            윈도우 핸들 (HWND) 또는 None
        """
        if not _load_win32_modules():
            return None
        
        search_title = title or self.window_title
        if not search_title:
            return None
        
        found_hwnd = None
        
        def enum_callback(hwnd, _):
            nonlocal found_hwnd
            if _win32gui.IsWindowVisible(hwnd):
                window_text = _win32gui.GetWindowText(hwnd)
                if search_title.lower() in window_text.lower():
                    found_hwnd = hwnd
                    return False  # 검색 중단
            return True
        
        try:
            _win32gui.EnumWindows(enum_callback, None)
        except Exception:
            pass  # EnumWindows가 False 반환 시 예외 발생
        
        if found_hwnd:
            self._hwnd = found_hwnd
            logger.info(f"윈도우 찾음: {_win32gui.GetWindowText(found_hwnd)} (hwnd={found_hwnd})")
        else:
            logger.warning(f"윈도우를 찾을 수 없음: {search_title}")
        
        return found_hwnd
    
    def get_window_rect(self, hwnd: int = None) -> Optional[Tuple[int, int, int, int]]:
        """윈도우 영역 가져오기
        
        Args:
            hwnd: 윈도우 핸들 (None이면 저장된 핸들 사용)
            
        Returns:
            (left, top, right, bottom) 또는 None
        """
        if not _load_win32_modules():
            return None
        
        hwnd = hwnd or self._hwnd
        if not hwnd:
            return None
        
        try:
            return _win32gui.GetWindowRect(hwnd)
        except Exception as e:
            logger.error(f"윈도우 영역 가져오기 실패: {e}")
            return None
    
    def capture_window(self, hwnd: int = None) -> Optional[Image.Image]:
        """특정 윈도우만 캡처
        
        Args:
            hwnd: 윈도우 핸들 (None이면 저장된 핸들 사용)
            
        Returns:
            PIL Image 또는 None
        """
        if not _load_win32_modules():
            logger.warning("Win32 모듈 없음, 전체 화면 캡처로 대체")
            import pyautogui
            return pyautogui.screenshot()
        
        hwnd = hwnd or self._hwnd
        if not hwnd:
            logger.warning("윈도우 핸들 없음, 전체 화면 캡처로 대체")
            import pyautogui
            return pyautogui.screenshot()
        
        try:
            # 윈도우 영역 가져오기
            left, top, right, bottom = _win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                logger.warning("윈도우 크기가 유효하지 않음")
                import pyautogui
                return pyautogui.screenshot()
            
            # 윈도우 DC 가져오기
            hwnd_dc = _win32gui.GetWindowDC(hwnd)
            mfc_dc = _win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # 비트맵 생성
            bitmap = _win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)
            
            # 윈도우 내용 복사 (PrintWindow 사용)
            # PW_RENDERFULLCONTENT = 2 (Windows 8.1+)
            try:
                import ctypes
                result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
                if not result:
                    # PrintWindow 실패 시 BitBlt 사용
                    save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), _win32con.SRCCOPY)
            except Exception:
                save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), _win32con.SRCCOPY)
            
            # 비트맵 데이터 추출
            bmp_info = bitmap.GetInfo()
            bmp_str = bitmap.GetBitmapBits(True)
            
            # PIL Image로 변환
            image = Image.frombuffer(
                'RGB',
                (bmp_info['bmWidth'], bmp_info['bmHeight']),
                bmp_str, 'raw', 'BGRX', 0, 1
            )
            
            # 리소스 정리
            _win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            _win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            logger.debug(f"윈도우 캡처 성공: {width}x{height}")
            return image
            
        except Exception as e:
            logger.error(f"윈도우 캡처 실패: {e}")
            # 실패 시 전체 화면 캡처로 대체
            import pyautogui
            return pyautogui.screenshot()
    
    def capture_window_region(self, hwnd: int = None) -> Optional[Image.Image]:
        """윈도우 영역만 전체 화면에서 잘라서 캡처 (대안 방법)
        
        PrintWindow가 작동하지 않는 경우 사용
        
        Args:
            hwnd: 윈도우 핸들
            
        Returns:
            PIL Image 또는 None
        """
        import pyautogui
        
        rect = self.get_window_rect(hwnd)
        if not rect:
            return pyautogui.screenshot()
        
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        
        # 전체 화면 캡처 후 윈도우 영역만 자르기
        full_screenshot = pyautogui.screenshot()
        cropped = full_screenshot.crop((left, top, right, bottom))
        
        logger.debug(f"윈도우 영역 캡처: ({left}, {top}) - {width}x{height}")
        return cropped


def capture_game_window(window_title: str) -> Image.Image:
    """게임 윈도우 캡처 헬퍼 함수
    
    Args:
        window_title: 게임 윈도우 제목
        
    Returns:
        PIL Image
    """
    capturer = WindowCapture(window_title)
    hwnd = capturer.find_window()
    
    if hwnd:
        # 먼저 PrintWindow 방식 시도
        image = capturer.capture_window(hwnd)
        if image:
            return image
        
        # 실패 시 영역 자르기 방식
        return capturer.capture_window_region(hwnd)
    else:
        # 윈도우를 찾지 못하면 전체 화면 캡처
        import pyautogui
        return pyautogui.screenshot()
