"""
UIAnalyzer 테스트

Requirements: 2.1, 2.2, 2.3, 2.4, 2.7
"""

import base64
import io
import json
import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer


class TestUIAnalyzerInit:
    """UIAnalyzer 초기화 테스트"""
    
    def test_init_with_config(self, tmp_path):
        """설정으로 초기화 테스트"""
        # 설정 파일 생성
        config_path = tmp_path / "config.json"
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "max_tokens": 2000
            },
            "automation": {
                "screenshot_dir": "screenshots"
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        # Bedrock 클라이언트 초기화 모킹
        with patch('boto3.client') as mock_boto:
            mock_boto.return_value = Mock()
            analyzer = UIAnalyzer(config)
            
            assert analyzer.config == config
            mock_boto.assert_called_once_with(
                service_name='bedrock-runtime',
                region_name='ap-northeast-2'
            )


class TestScreenshotCapture:
    """스크린샷 캡처 테스트"""
    
    def test_capture_screenshot_returns_image(self, tmp_path):
        """스크린샷 캡처가 PIL Image를 반환하는지 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        # pyautogui.screenshot 모킹
        mock_image = Image.new('RGB', (100, 100), color='red')
        with patch('pyautogui.screenshot', return_value=mock_image):
            result = analyzer.capture_screenshot()
            
            assert isinstance(result, Image.Image)
            assert result.size == (100, 100)
    
    def test_capture_screenshot_saves_to_path(self, tmp_path):
        """스크린샷이 지정된 경로에 저장되는지 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        mock_image = Image.new('RGB', (100, 100), color='blue')
        save_path = str(tmp_path / "test_screenshot.png")
        
        with patch('pyautogui.screenshot', return_value=mock_image):
            result = analyzer.capture_screenshot(save_path)
            
            assert os.path.exists(save_path)
            saved_image = Image.open(save_path)
            assert saved_image.size == (100, 100)


class TestBase64Encoding:
    """Base64 인코딩/디코딩 테스트"""
    
    def test_encode_image_to_base64(self, tmp_path):
        """이미지를 base64로 인코딩 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        # 테스트 이미지 생성
        test_image = Image.new('RGB', (50, 50), color='green')
        
        # 인코딩
        encoded = analyzer.encode_image_to_base64(test_image)
        
        # 결과 검증
        assert isinstance(encoded, str)
        assert len(encoded) > 0
        # base64 디코딩 가능한지 확인
        decoded_bytes = base64.b64decode(encoded)
        assert len(decoded_bytes) > 0
    
    def test_base64_round_trip(self, tmp_path):
        """base64 인코딩/디코딩 round trip 테스트
        
        Property 2: 이미지 인코딩 round trip
        """
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        # 테스트 이미지 생성
        original_image = Image.new('RGB', (100, 100), color='purple')
        
        # Round trip
        encoded = analyzer.encode_image_to_base64(original_image)
        decoded_image = analyzer.decode_base64_to_image(encoded)
        
        # 크기 비교
        assert original_image.size == decoded_image.size
        assert original_image.mode == decoded_image.mode


class TestVisionLLMAnalysis:
    """Vision LLM 분석 테스트"""
    
    def test_analyze_with_vision_llm_success(self, tmp_path):
        """Vision LLM 분석 성공 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "max_tokens": 2000
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        # Mock Bedrock 응답
        mock_response = {
            "content": [
                {
                    "text": json.dumps({
                        "buttons": [{"text": "Start", "x": 100, "y": 200, "width": 80, "height": 40, "confidence": 0.95}],
                        "icons": [{"type": "settings", "x": 50, "y": 50, "confidence": 0.88}],
                        "text_fields": [{"content": "Player Name", "x": 300, "y": 150, "confidence": 0.92}]
                    })
                }
            ]
        }
        
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = {
            'body': io.BytesIO(json.dumps(mock_response).encode())
        }
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
            
            test_image = Image.new('RGB', (800, 600), color='black')
            result = analyzer.analyze_with_vision_llm(test_image)
            
            assert "buttons" in result
            assert "icons" in result
            assert "text_fields" in result
            assert len(result["buttons"]) == 1
            assert result["buttons"][0]["text"] == "Start"
            assert result["buttons"][0]["x"] == 100
            assert result["buttons"][0]["y"] == 200
    
    def test_analyze_with_vision_llm_no_client(self, tmp_path):
        """Bedrock 클라이언트 없이 분석 시도 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client', side_effect=Exception("Connection failed")):
            analyzer = UIAnalyzer(config)
            analyzer.bedrock_client = None
            
            test_image = Image.new('RGB', (100, 100), color='white')
            
            with pytest.raises(Exception) as exc_info:
                analyzer.analyze_with_vision_llm(test_image)
            
            assert "Bedrock 클라이언트가 초기화되지 않았습니다" in str(exc_info.value)


class TestUIResponseParsing:
    """UI 응답 파싱 테스트"""
    
    def test_parse_json_response(self, tmp_path):
        """JSON 응답 파싱 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        response_text = json.dumps({
            "buttons": [{"text": "OK", "x": 100, "y": 200}],
            "icons": [],
            "text_fields": []
        })
        
        result = analyzer._parse_ui_response(response_text)
        
        assert "buttons" in result
        assert len(result["buttons"]) == 1
        assert result["buttons"][0]["text"] == "OK"
    
    def test_parse_json_with_code_block(self, tmp_path):
        """코드 블록으로 감싸진 JSON 파싱 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        response_text = '''```json
{
    "buttons": [{"text": "Cancel", "x": 200, "y": 300}],
    "icons": [],
    "text_fields": []
}
```'''
        
        result = analyzer._parse_ui_response(response_text)
        
        assert len(result["buttons"]) == 1
        assert result["buttons"][0]["text"] == "Cancel"
    
    def test_parse_invalid_json(self, tmp_path):
        """잘못된 JSON 파싱 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        response_text = "This is not valid JSON"
        
        result = analyzer._parse_ui_response(response_text)
        
        # 기본 빈 구조 반환
        assert result == {"buttons": [], "icons": [], "text_fields": []}
    
    def test_validate_elements_filters_invalid(self, tmp_path):
        """필수 필드 없는 요소 필터링 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        elements = [
            {"text": "Valid", "x": 100, "y": 200},  # 유효
            {"text": "Missing Y", "x": 100},  # y 누락
            {"text": "Missing X", "y": 200},  # x 누락
            {"x": 300, "y": 400}  # 유효 (text는 필수 아님)
        ]
        
        result = analyzer._validate_elements(elements, ["x", "y"])
        
        assert len(result) == 2
        assert result[0]["text"] == "Valid"


class TestRetryLogic:
    """재시도 로직 테스트 (Requirements 2.5)"""
    
    def test_retry_with_exponential_backoff(self, tmp_path):
        """지수 백오프 재시도 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "retry_delay": 0.1  # 테스트를 위해 짧은 지연
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        mock_bedrock = Mock()
        # 처음 2번 실패, 3번째 성공
        mock_response = {
            "content": [{"text": json.dumps({"buttons": [], "icons": [], "text_fields": []})}]
        }
        mock_bedrock.invoke_model.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            {'body': io.BytesIO(json.dumps(mock_response).encode())}
        ]
        
        with patch('boto3.client', return_value=mock_bedrock):
            with patch('time.sleep') as mock_sleep:
                analyzer = UIAnalyzer(config)
                test_image = Image.new('RGB', (100, 100), color='white')
                
                result = analyzer.analyze_with_retry(test_image, retry_count=3)
                
                # 3번 호출되어야 함
                assert mock_bedrock.invoke_model.call_count == 3
                # sleep이 2번 호출되어야 함 (첫 번째, 두 번째 실패 후)
                assert mock_sleep.call_count == 2
                # 지수 백오프 확인: 0.1초, 0.2초
                mock_sleep.assert_any_call(0.1)
                mock_sleep.assert_any_call(0.2)
                # 성공 결과
                assert result["source"] == "vision_llm"
    
    def test_retry_all_failures_triggers_ocr_fallback(self, tmp_path):
        """모든 재시도 실패 시 OCR 폴백 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "retry_delay": 0.01
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("Always fails")
        
        with patch('boto3.client', return_value=mock_bedrock):
            with patch('time.sleep'):
                analyzer = UIAnalyzer(config)
                test_image = Image.new('RGB', (100, 100), color='white')
                
                # OCR 폴백 모킹
                with patch.object(analyzer, 'analyze_with_ocr', return_value=[
                    {"text": "Test", "confidence": 0.9, "bbox": [[0,0],[10,0],[10,10],[0,10]], "x": 5, "y": 5}
                ]):
                    result = analyzer.analyze_with_retry(test_image, retry_count=3)
                    
                    # 3번 재시도 후 OCR 폴백
                    assert mock_bedrock.invoke_model.call_count == 3
                    assert result["source"] == "ocr_fallback"
                    assert len(result["text_fields"]) == 1
    
    def test_retry_count_from_config(self, tmp_path):
        """설정에서 재시도 횟수 가져오기 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "retry_count": 2,
                "retry_delay": 0.01
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("Always fails")
        
        mock_image = Image.new('RGB', (100, 100), color='white')
        
        with patch('boto3.client', return_value=mock_bedrock):
            with patch('pyautogui.screenshot', return_value=mock_image):
                with patch('time.sleep'):
                    analyzer = UIAnalyzer(config)
                    
                    # OCR도 실패하도록 설정
                    with patch.object(analyzer, 'analyze_with_ocr', return_value=[]):
                        result = analyzer.analyze()
                        
                        # 설정된 2번만 재시도
                        assert mock_bedrock.invoke_model.call_count == 2


class TestOCRFallback:
    """OCR 폴백 테스트 (Requirements 2.6)"""
    
    def test_paddleocr_installation_verification(self, tmp_path):
        """PaddleOCR 설치 확인 테스트 - 실제 모듈 import 테스트"""
        # PaddleOCR 모듈이 설치되어 있는지 확인
        try:
            import paddleocr
            assert hasattr(paddleocr, 'PaddleOCR'), "PaddleOCR 클래스가 존재해야 합니다"
            assert hasattr(paddleocr, '__version__'), "버전 정보가 존재해야 합니다"
            print(f"PaddleOCR 버전: {paddleocr.__version__}")
        except ImportError:
            pytest.fail("PaddleOCR이 설치되지 않았습니다. 'pip install paddleocr paddlepaddle'로 설치하세요.")
    
    def test_ocr_engine_real_initialization(self, tmp_path):
        """실제 PaddleOCR 엔진 초기화 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        # 전역 인스턴스 초기화
        import src.ui_analyzer as ui_module
        original_instance = ui_module._paddleocr_instance
        ui_module._paddleocr_instance = None
        
        try:
            with patch('boto3.client'):
                analyzer = UIAnalyzer(config)
                
                # 실제 OCR 엔진 가져오기
                ocr = analyzer._get_ocr_engine()
                
                # OCR 엔진이 정상적으로 초기화되었는지 확인
                assert ocr is not None, "OCR 엔진이 초기화되어야 합니다"
                
                # 싱글톤 패턴 확인 - 두 번째 호출도 같은 인스턴스 반환
                ocr2 = analyzer._get_ocr_engine()
                assert ocr is ocr2, "싱글톤 패턴: 같은 인스턴스를 반환해야 합니다"
        finally:
            # 원래 상태로 복원
            ui_module._paddleocr_instance = original_instance
    
    def test_ocr_analyze_with_real_image(self, tmp_path):
        """실제 이미지로 OCR 분석 테스트"""
        from PIL import ImageDraw, ImageFont
        
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        # 전역 인스턴스 초기화
        import src.ui_analyzer as ui_module
        original_instance = ui_module._paddleocr_instance
        ui_module._paddleocr_instance = None
        
        try:
            with patch('boto3.client'):
                analyzer = UIAnalyzer(config)
                
                # 텍스트가 포함된 테스트 이미지 생성
                test_image = Image.new('RGB', (400, 200), color='white')
                draw = ImageDraw.Draw(test_image)
                
                # 큰 텍스트 그리기 (OCR이 인식하기 쉽도록)
                draw.text((50, 50), "Hello World", fill='black')
                draw.text((50, 100), "Test Button", fill='black')
                
                # OCR 분석 실행
                result = analyzer.analyze_with_ocr(test_image)
                
                # 결과 검증
                assert isinstance(result, list), "결과는 리스트여야 합니다"
                
                # 결과가 있으면 구조 검증
                if len(result) > 0:
                    for item in result:
                        assert "text" in item, "각 결과에 'text' 필드가 있어야 합니다"
                        assert "confidence" in item, "각 결과에 'confidence' 필드가 있어야 합니다"
                        assert "x" in item, "각 결과에 'x' 좌표가 있어야 합니다"
                        assert "y" in item, "각 결과에 'y' 좌표가 있어야 합니다"
                        assert "bbox" in item, "각 결과에 'bbox' 필드가 있어야 합니다"
                        
                        # 좌표가 유효한 범위인지 확인
                        assert 0 <= item["x"] <= 400, f"x 좌표가 이미지 범위 내여야 합니다: {item['x']}"
                        assert 0 <= item["y"] <= 200, f"y 좌표가 이미지 범위 내여야 합니다: {item['y']}"
                        assert 0 <= item["confidence"] <= 1, f"confidence가 0~1 범위여야 합니다: {item['confidence']}"
                    
                    print(f"OCR 결과: {len(result)}개 텍스트 인식됨")
                    for item in result:
                        print(f"  - '{item['text']}' (confidence: {item['confidence']:.2f}, pos: ({item['x']}, {item['y']}))")
        finally:
            # 원래 상태로 복원
            ui_module._paddleocr_instance = original_instance
    
    def test_ocr_engine_lazy_initialization(self, tmp_path):
        """OCR 엔진 지연 초기화 테스트 (모킹)"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
            
            # 전역 변수 초기화
            import src.ui_analyzer as ui_module
            original_instance = ui_module._paddleocr_instance
            ui_module._paddleocr_instance = None
            
            try:
                # PaddleOCR 모듈 모킹
                mock_ocr_instance = Mock()
                mock_paddleocr_module = Mock()
                mock_paddleocr_module.PaddleOCR.return_value = mock_ocr_instance
                
                with patch.dict('sys.modules', {'paddleocr': mock_paddleocr_module}):
                    ocr = analyzer._get_ocr_engine()
                    
                    # PaddleOCR이 호출되었는지 확인
                    mock_paddleocr_module.PaddleOCR.assert_called_once()
            finally:
                # 원래 상태로 복원
                ui_module._paddleocr_instance = original_instance
    
    def test_ocr_fallback_returns_text_fields(self, tmp_path):
        """OCR 폴백이 text_fields를 반환하는지 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        # OCR 결과를 UI 형식으로 변환
        ocr_results = [
            {"text": "Button1", "confidence": 0.95, "bbox": [[10,10],[100,10],[100,40],[10,40]], "x": 55, "y": 25},
            {"text": "Label", "confidence": 0.88, "bbox": [[200,50],[300,50],[300,80],[200,80]], "x": 250, "y": 65}
        ]
        
        result = analyzer._convert_ocr_to_ui_format(ocr_results)
        
        assert result["source"] == "ocr_fallback"
        assert len(result["text_fields"]) == 2
        assert result["text_fields"][0]["content"] == "Button1"
        assert result["text_fields"][0]["x"] == 55
        assert result["text_fields"][0]["y"] == 25
        assert result["buttons"] == []  # OCR로는 버튼 구분 불가
        assert result["icons"] == []    # OCR로는 아이콘 구분 불가
    
    def test_ocr_not_installed_returns_empty(self, tmp_path):
        """PaddleOCR 미설치 시 빈 결과 반환 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2"}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        with patch('boto3.client'):
            analyzer = UIAnalyzer(config)
        
        # PaddleOCR import 실패 시뮬레이션
        with patch('src.ui_analyzer._paddleocr_instance', None):
            with patch.dict('sys.modules', {'paddleocr': None}):
                with patch.object(analyzer, '_get_ocr_engine', return_value=None):
                    test_image = Image.new('RGB', (100, 100), color='white')
                    result = analyzer.analyze_with_ocr(test_image)
                    
                    assert result == []


class TestAnalyzeMethod:
    """analyze 메서드 통합 테스트"""
    
    def test_analyze_success(self, tmp_path):
        """전체 분석 플로우 성공 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "max_tokens": 2000
            },
            "automation": {
                "screenshot_dir": str(tmp_path / "screenshots")
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        # Mock 설정
        mock_response = {
            "content": [
                {
                    "text": json.dumps({
                        "buttons": [{"text": "Play", "x": 400, "y": 300, "width": 100, "height": 50, "confidence": 0.9}],
                        "icons": [],
                        "text_fields": []
                    })
                }
            ]
        }
        
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.return_value = {
            'body': io.BytesIO(json.dumps(mock_response).encode())
        }
        
        mock_image = Image.new('RGB', (800, 600), color='gray')
        
        with patch('boto3.client', return_value=mock_bedrock):
            with patch('pyautogui.screenshot', return_value=mock_image):
                analyzer = UIAnalyzer(config)
                result = analyzer.analyze()
                
                assert "buttons" in result
                assert len(result["buttons"]) == 1
                assert result["buttons"][0]["text"] == "Play"
                assert result["source"] == "vision_llm"
    
    def test_analyze_with_error_returns_empty_result(self, tmp_path):
        """분석 실패 시 빈 결과 반환 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2", "retry_delay": 0.01}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("API Error")
        
        mock_image = Image.new('RGB', (100, 100), color='white')
        
        with patch('boto3.client', return_value=mock_bedrock):
            with patch('pyautogui.screenshot', return_value=mock_image):
                with patch('time.sleep'):
                    analyzer = UIAnalyzer(config)
                    
                    # OCR도 실패하도록 설정
                    with patch.object(analyzer, 'analyze_with_ocr', return_value=[]):
                        result = analyzer.analyze()
                        
                        assert "buttons" in result
                        assert "icons" in result
                        assert "text_fields" in result
                        assert "error" in result
                        assert result["source"] == "failed"
    
    def test_analyze_with_ocr_fallback_success(self, tmp_path):
        """Vision LLM 실패 후 OCR 폴백 성공 테스트"""
        config_path = tmp_path / "config.json"
        config_data = {"aws": {"region": "ap-northeast-2", "retry_delay": 0.01}}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(str(config_path))
        config.load_config()
        
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("API Error")
        
        mock_image = Image.new('RGB', (100, 100), color='white')
        
        with patch('boto3.client', return_value=mock_bedrock):
            with patch('pyautogui.screenshot', return_value=mock_image):
                with patch('time.sleep'):
                    analyzer = UIAnalyzer(config)
                    
                    # OCR 성공 시뮬레이션
                    with patch.object(analyzer, 'analyze_with_ocr', return_value=[
                        {"text": "OCR Text", "confidence": 0.9, "bbox": [], "x": 100, "y": 200}
                    ]):
                        result = analyzer.analyze()
                        
                        assert result["source"] == "ocr_fallback"
                        assert len(result["text_fields"]) == 1
                        assert result["text_fields"][0]["content"] == "OCR Text"
