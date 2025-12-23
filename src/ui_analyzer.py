"""
UIAnalyzer - Vision LLM 기반 UI 분석기

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
"""

import base64
import io
import json
import logging
import os
import time
from typing import Optional, List, Dict, Any

import boto3
from PIL import Image
import pyautogui
import numpy as np

from src.config_manager import ConfigManager


logger = logging.getLogger(__name__)


# PaddleOCR 지연 로딩을 위한 전역 변수
_paddleocr_instance = None


class UIAnalyzer:
    """UI 분석기 - Vision LLM을 통해 게임 화면의 UI 요소를 분석"""
    
    def __init__(self, config: ConfigManager):
        """
        Args:
            config: 설정 관리자
        """
        self.config = config
        self.bedrock_client = None
        self.ocr_engine = None
        self._initialize_bedrock_client()
    
    def _get_ocr_engine(self):
        """PaddleOCR 엔진 지연 초기화 (싱글톤)
        
        Requirements: 2.6
        
        Returns:
            PaddleOCR 인스턴스
        """
        global _paddleocr_instance
        
        if _paddleocr_instance is None:
            try:
                from paddleocr import PaddleOCR
                # PaddleOCR 3.x 버전 호환 설정
                # lang: 한국어 지원 (korean)
                # use_textline_orientation: 텍스트 방향 분류 사용 (use_angle_cls deprecated)
                _paddleocr_instance = PaddleOCR(
                    use_textline_orientation=True,
                    lang='korean'
                )
                logger.info("PaddleOCR 엔진 초기화 완료")
            except ImportError:
                logger.warning("PaddleOCR이 설치되지 않았습니다. OCR 폴백을 사용할 수 없습니다.")
                return None
            except Exception as e:
                logger.error(f"PaddleOCR 초기화 실패: {e}")
                return None
        
        return _paddleocr_instance
    
    def _initialize_bedrock_client(self):
        """AWS Bedrock 클라이언트 초기화
        
        Requirements: 2.3, 10.2
        """
        region = self.config.get('aws.region', 'ap-northeast-2')
        try:
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=region
            )
            logger.info(f"Bedrock 클라이언트 초기화 완료 (region: {region})")
        except Exception as e:
            logger.error(f"Bedrock 클라이언트 초기화 실패: {e}")
            self.bedrock_client = None
    
    def capture_screenshot(self, save_path: Optional[str] = None) -> Image.Image:
        """현재 화면 캡처
        
        Requirements: 2.1
        
        Args:
            save_path: 저장할 경로 (선택사항)
            
        Returns:
            PIL Image 객체
        """
        screenshot = pyautogui.screenshot()
        
        if save_path:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(save_path), exist_ok=True) if os.path.dirname(save_path) else None
            screenshot.save(save_path, format='PNG')
            logger.info(f"스크린샷 저장: {save_path}")
        
        return screenshot

    def encode_image_to_base64(self, image: Image.Image) -> str:
        """이미지를 base64로 인코딩
        
        Requirements: 2.2
        
        Args:
            image: PIL Image 객체
            
        Returns:
            base64 인코딩된 문자열
        """
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        image_bytes = buffer.read()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def decode_base64_to_image(self, base64_string: str) -> Image.Image:
        """base64 문자열을 이미지로 디코딩
        
        Args:
            base64_string: base64 인코딩된 문자열
            
        Returns:
            PIL Image 객체
        """
        image_bytes = base64.b64decode(base64_string)
        buffer = io.BytesIO(image_bytes)
        return Image.open(buffer)
    
    def _build_vision_prompt(self) -> str:
        """Vision LLM용 프롬프트 생성
        
        Returns:
            구조화된 프롬프트 문자열
        """
        return """당신은 게임 UI 분석 전문가입니다. 제공된 게임 화면 스크린샷을 분석하여 상호작용 가능한 UI 요소들을 식별해주세요.

다음 형식의 JSON으로 응답해주세요:
{
    "buttons": [
        {"text": "버튼 텍스트", "x": 중심X좌표, "y": 중심Y좌표, "width": 너비, "height": 높이, "confidence": 신뢰도}
    ],
    "icons": [
        {"type": "아이콘 타입", "x": 중심X좌표, "y": 중심Y좌표, "confidence": 신뢰도}
    ],
    "text_fields": [
        {"content": "텍스트 내용", "x": X좌표, "y": Y좌표, "confidence": 신뢰도}
    ]
}

분석 시 주의사항:
1. 모든 좌표는 픽셀 단위의 정수로 제공
2. confidence는 0.0~1.0 사이의 값
3. 버튼, 아이콘, 텍스트 필드를 구분하여 분류
4. 상호작용 가능한 요소만 포함
5. JSON만 응답하고 다른 설명은 포함하지 마세요"""

    def analyze_with_vision_llm(self, image: Image.Image) -> dict:
        """Vision LLM으로 UI 분석
        
        Requirements: 2.3, 2.4, 2.7
        
        Args:
            image: 분석할 이미지
            
        Returns:
            UI 요소 정보 딕셔너리
            {
                "buttons": [{"text": str, "x": int, "y": int, "width": int, "height": int, "confidence": float}],
                "icons": [{"type": str, "x": int, "y": int, "confidence": float}],
                "text_fields": [{"content": str, "x": int, "y": int, "confidence": float}]
            }
            
        Raises:
            Exception: API 호출 실패 시
        """
        if not self.bedrock_client:
            raise Exception("Bedrock 클라이언트가 초기화되지 않았습니다")
        
        # 이미지를 base64로 인코딩
        image_base64 = self.encode_image_to_base64(image)
        
        # 모델 ID 및 설정 가져오기
        model_id = self.config.get('aws.model_id', 'anthropic.claude-sonnet-4-5-20250929-v1:0')
        max_tokens = self.config.get('aws.max_tokens', 2000)
        
        # Claude Messages API 형식으로 요청 구성
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": self._build_vision_prompt()
                        }
                    ]
                }
            ]
        }
        
        # API 호출
        response = self.bedrock_client.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )
        
        # 응답 파싱
        response_body = json.loads(response['body'].read())
        
        # Claude 응답에서 텍스트 추출
        if 'content' in response_body and len(response_body['content']) > 0:
            response_text = response_body['content'][0].get('text', '')
        else:
            raise Exception("Vision LLM 응답에서 텍스트를 찾을 수 없습니다")
        
        # JSON 파싱
        ui_data = self._parse_ui_response(response_text)
        
        return ui_data

    def _parse_ui_response(self, response_text: str) -> dict:
        """Vision LLM 응답을 파싱하여 UI 요소 정보 추출
        
        Requirements: 2.4, 2.7
        
        Args:
            response_text: Vision LLM의 응답 텍스트
            
        Returns:
            UI 요소 정보 딕셔너리
        """
        # 기본 구조
        default_result = {
            "buttons": [],
            "icons": [],
            "text_fields": []
        }
        
        try:
            # JSON 블록 추출 시도 (```json ... ``` 형식 처리)
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_str = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                json_str = response_text[start:end].strip()
            else:
                # JSON 객체 직접 찾기
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = response_text[start:end]
                else:
                    logger.warning("응답에서 JSON을 찾을 수 없습니다")
                    return default_result
            
            # JSON 파싱
            ui_data = json.loads(json_str)
            
            # 필수 키 확인 및 기본값 설정
            result = {
                "buttons": ui_data.get("buttons", []),
                "icons": ui_data.get("icons", []),
                "text_fields": ui_data.get("text_fields", [])
            }
            
            # 각 요소의 필수 필드 검증
            result["buttons"] = self._validate_elements(result["buttons"], ["x", "y"])
            result["icons"] = self._validate_elements(result["icons"], ["x", "y"])
            result["text_fields"] = self._validate_elements(result["text_fields"], ["x", "y"])
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            return default_result
        except Exception as e:
            logger.error(f"응답 파싱 중 오류: {e}")
            return default_result
    
    def _validate_elements(self, elements: list, required_fields: list) -> list:
        """UI 요소 리스트에서 필수 필드가 있는 요소만 필터링
        
        Args:
            elements: UI 요소 리스트
            required_fields: 필수 필드 목록
            
        Returns:
            유효한 요소만 포함된 리스트
        """
        valid_elements = []
        for element in elements:
            if all(field in element for field in required_fields):
                valid_elements.append(element)
            else:
                logger.warning(f"필수 필드 누락된 요소 제외: {element}")
        return valid_elements

    def analyze_with_ocr(self, image: Image.Image) -> List[Dict[str, Any]]:
        """OCR로 텍스트 추출 (Vision LLM 폴백)
        
        Requirements: 2.6
        
        Args:
            image: 분석할 이미지
            
        Returns:
            텍스트 정보 리스트
            [{"text": str, "confidence": float, "bbox": list, "x": int, "y": int}]
        """
        ocr = self._get_ocr_engine()
        if ocr is None:
            logger.error("OCR 엔진을 사용할 수 없습니다")
            return []
        
        try:
            # PIL Image를 numpy array로 변환
            image_np = np.array(image)
            
            # OCR 실행 - PaddleOCR 3.x에서는 predict() 사용
            # 하위 호환성을 위해 ocr() 메서드도 지원하지만 deprecated
            if hasattr(ocr, 'predict'):
                result = ocr.predict(image_np)
            else:
                # 이전 버전 호환
                result = ocr.ocr(image_np, cls=True)
            
            text_results = []
            
            # PaddleOCR 3.x predict() 결과 형식 처리
            if result and isinstance(result, dict) and 'rec_texts' in result:
                # 새로운 형식: {'rec_texts': [...], 'rec_scores': [...], 'dt_polys': [...]}
                rec_texts = result.get('rec_texts', [[]])[0] if result.get('rec_texts') else []
                rec_scores = result.get('rec_scores', [[]])[0] if result.get('rec_scores') else []
                dt_polys = result.get('dt_polys', [[]])[0] if result.get('dt_polys') else []
                
                for i, text in enumerate(rec_texts):
                    if text:
                        confidence = float(rec_scores[i]) if i < len(rec_scores) else 0.0
                        bbox = dt_polys[i].tolist() if i < len(dt_polys) else []
                        
                        # bbox에서 중심 좌표 계산
                        if bbox and len(bbox) >= 4:
                            x_coords = [point[0] for point in bbox]
                            y_coords = [point[1] for point in bbox]
                            center_x = int(sum(x_coords) / len(x_coords))
                            center_y = int(sum(y_coords) / len(y_coords))
                        else:
                            center_x, center_y = 0, 0
                        
                        text_results.append({
                            "text": text,
                            "confidence": confidence,
                            "bbox": bbox,
                            "x": center_x,
                            "y": center_y
                        })
            elif result and result[0]:
                # 이전 형식 (ocr() 메서드 결과)
                for line in result[0]:
                    if line and len(line) >= 2:
                        bbox = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                        text_info = line[1]  # (text, confidence)
                        
                        if text_info and len(text_info) >= 2:
                            text = text_info[0]
                            confidence = float(text_info[1])
                            
                            # bbox에서 중심 좌표 계산
                            x_coords = [point[0] for point in bbox]
                            y_coords = [point[1] for point in bbox]
                            center_x = int(sum(x_coords) / len(x_coords))
                            center_y = int(sum(y_coords) / len(y_coords))
                            
                            text_results.append({
                                "text": text,
                                "confidence": confidence,
                                "bbox": bbox,
                                "x": center_x,
                                "y": center_y
                            })
            
            logger.info(f"OCR 분석 완료: {len(text_results)}개 텍스트 추출")
            return text_results
            
        except Exception as e:
            logger.error(f"OCR 분석 실패: {e}")
            return []

    def _convert_ocr_to_ui_format(self, ocr_results: List[Dict[str, Any]]) -> dict:
        """OCR 결과를 UI 분석 결과 형식으로 변환
        
        Args:
            ocr_results: OCR 결과 리스트
            
        Returns:
            UI 요소 정보 딕셔너리
        """
        # OCR 결과를 text_fields로 변환
        text_fields = []
        for item in ocr_results:
            text_fields.append({
                "content": item["text"],
                "x": item["x"],
                "y": item["y"],
                "confidence": item["confidence"]
            })
        
        return {
            "buttons": [],  # OCR로는 버튼 구분 불가
            "icons": [],    # OCR로는 아이콘 구분 불가
            "text_fields": text_fields,
            "source": "ocr_fallback"
        }

    def analyze_with_retry(self, image: Image.Image, retry_count: int = 3) -> dict:
        """지수 백오프 재시도 로직이 포함된 Vision LLM 분석
        
        Requirements: 2.5, 2.6
        
        Args:
            image: 분석할 이미지
            retry_count: 최대 재시도 횟수 (기본값: 3)
            
        Returns:
            UI 요소 정보 딕셔너리
        """
        base_delay = self.config.get('aws.retry_delay', 1.0)
        last_exception = None
        
        for attempt in range(retry_count):
            try:
                logger.info(f"Vision LLM 분석 시도 {attempt + 1}/{retry_count}")
                result = self.analyze_with_vision_llm(image)
                result["source"] = "vision_llm"
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Vision LLM 분석 실패 (시도 {attempt + 1}/{retry_count}): {e}")
                
                if attempt < retry_count - 1:
                    # 지수 백오프: 1초, 2초, 4초...
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"{delay}초 후 재시도...")
                    time.sleep(delay)
        
        # 모든 재시도 실패 - OCR 폴백
        logger.warning(f"Vision LLM 재시도 모두 실패. OCR 폴백 시도...")
        
        try:
            ocr_results = self.analyze_with_ocr(image)
            if ocr_results:
                result = self._convert_ocr_to_ui_format(ocr_results)
                logger.info("OCR 폴백 성공")
                return result
            else:
                logger.error("OCR 폴백도 결과 없음")
        except Exception as ocr_error:
            logger.error(f"OCR 폴백 실패: {ocr_error}")
        
        # 모든 방법 실패
        return {
            "buttons": [],
            "icons": [],
            "text_fields": [],
            "error": str(last_exception) if last_exception else "분석 실패",
            "source": "failed"
        }

    def analyze(self, save_screenshot: bool = False, retry_count: int = 3) -> dict:
        """UI 분석 수행 (스크린샷 캡처 + Vision LLM 분석 + 재시도 + OCR 폴백)
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
        
        Args:
            save_screenshot: 스크린샷 저장 여부
            retry_count: Vision LLM 최대 재시도 횟수 (기본값: 3)
            
        Returns:
            UI 요소 정보 딕셔너리
        """
        # 스크린샷 캡처
        screenshot_dir = self.config.get('automation.screenshot_dir', 'screenshots')
        save_path = None
        if save_screenshot:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{screenshot_dir}/analysis_{timestamp}.png"
        
        image = self.capture_screenshot(save_path)
        
        # 설정에서 재시도 횟수 가져오기 (기본값: 3)
        config_retry_count = self.config.get('aws.retry_count', retry_count)
        
        # Vision LLM으로 분석 (재시도 로직 포함)
        ui_data = self.analyze_with_retry(image, config_retry_count)
        
        source = ui_data.get("source", "unknown")
        logger.info(f"UI 분석 완료 (source: {source}): 버튼 {len(ui_data['buttons'])}개, "
                   f"아이콘 {len(ui_data['icons'])}개, "
                   f"텍스트 필드 {len(ui_data['text_fields'])}개")
        
        return ui_data
