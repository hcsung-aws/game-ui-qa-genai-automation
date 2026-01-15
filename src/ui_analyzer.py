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
        
        Requirements: 1.3, 2.3
        
        Returns:
            구조화된 프롬프트 문자열 (bounding_box 정보 포함)
        """
        return """You are a game UI analysis expert. Analyze the provided game screenshot and identify interactive UI elements.

        CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no code blocks.

        Response format (copy this structure exactly):
        {"buttons":[{"text":"button text","x":100,"y":200,"width":80,"height":40,"bounding_box":{"x":60,"y":180,"width":80,"height":40},"confidence":0.95,"description":"description"}],"icons":[{"type":"icon type","x":100,"y":200,"width":40,"height":40,"bounding_box":{"x":80,"y":180,"width":40,"height":40},"confidence":0.9,"description":"description"}],"text_fields":[{"content":"text content","x":100,"y":200,"width":100,"height":20,"bounding_box":{"x":50,"y":190,"width":100,"height":20},"confidence":0.85}]}

        Rules:
        1. All coordinates are integers in pixels
        2. x, y are CENTER coordinates of the element
        3. bounding_box.x = x - width/2, bounding_box.y = y - height/2
        4. confidence is a float between 0.0 and 1.0
        5. Include ONLY interactive elements
        6. If no elements found, return: {"buttons":[],"icons":[],"text_fields":[]}
        7. DO NOT include any text outside the JSON object
        8. DO NOT use markdown code blocks
        9. Ensure all strings are properly quoted and escaped"""

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
            Exception: API 호출 또는 JSON 파싱 실패 시
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
        
        # JSON 파싱 (실패 시 예외 발생)
        ui_data = self._parse_ui_response(response_text)
        
        return ui_data

    def _parse_ui_response(self, response_text: str) -> dict:
        """Vision LLM 응답을 파싱하여 UI 요소 정보 추출
        
        Requirements: 1.3, 2.3, 2.4, 2.7
        
        Args:
            response_text: Vision LLM의 응답 텍스트
            
        Returns:
            UI 요소 정보 딕셔너리 (bounding_box 포함)
            
        Raises:
            json.JSONDecodeError: JSON 파싱 및 복구 모두 실패 시
        """
        # 기본 구조
        default_result = {
            "buttons": [],
            "icons": [],
            "text_fields": []
        }
        
        # JSON 문자열 추출
        json_str = self._extract_json_string(response_text)
        if not json_str:
            logger.warning("응답에서 JSON을 찾을 수 없습니다")
            return default_result
        
        # JSON 파싱 시도
        try:
            ui_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 실패, 복구 시도: {e}")
            # JSON 복구 시도
            ui_data = self._try_fix_json(json_str)
            if ui_data is None:
                raise  # 복구 실패 시 예외 재발생
        
        # 필수 키 확인 및 기본값 설정
        result = {
            "buttons": ui_data.get("buttons", []),
            "icons": ui_data.get("icons", []),
            "text_fields": ui_data.get("text_fields", [])
        }
        
        # 각 요소의 필수 필드 검증 및 bounding_box 보정
        result["buttons"] = self._validate_and_enrich_elements(result["buttons"], ["x", "y"])
        result["icons"] = self._validate_and_enrich_elements(result["icons"], ["x", "y"])
        result["text_fields"] = self._validate_and_enrich_elements(result["text_fields"], ["x", "y"])
        
        return result
    
    def _extract_json_string(self, response_text: str) -> Optional[str]:
        """응답 텍스트에서 JSON 문자열 추출
        
        Args:
            response_text: Vision LLM의 응답 텍스트
            
        Returns:
            추출된 JSON 문자열 또는 None
        """
        # JSON 블록 추출 시도 (```json ... ``` 형식 처리)
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            return response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            return response_text[start:end].strip()
        else:
            # JSON 객체 직접 찾기
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                return response_text[start:end]
        return None
    
    def _try_fix_json(self, json_str: str) -> Optional[dict]:
        """손상된 JSON 문자열 복구 시도
        
        일반적인 JSON 오류를 수정하여 파싱을 시도한다:
        - 후행 쉼표 제거
        - 잘린 문자열 닫기
        - 누락된 괄호 추가
        
        Args:
            json_str: 손상된 JSON 문자열
            
        Returns:
            복구된 딕셔너리 또는 None (복구 실패 시)
        """
        import re
        
        fixed_str = json_str
        
        try:
            # 1. 후행 쉼표 제거 (,] 또는 ,} 패턴)
            fixed_str = re.sub(r',\s*]', ']', fixed_str)
            fixed_str = re.sub(r',\s*}', '}', fixed_str)
            
            # 2. 잘린 문자열 처리 - 열린 따옴표 닫기
            # 홀수 개의 따옴표가 있으면 마지막에 따옴표 추가
            quote_count = fixed_str.count('"') - fixed_str.count('\\"')
            if quote_count % 2 == 1:
                # 마지막 열린 따옴표 찾아서 닫기
                last_quote = fixed_str.rfind('"')
                # 따옴표 뒤에 적절한 종료 추가
                fixed_str = fixed_str[:last_quote+1] + '"'
            
            # 3. 괄호 균형 맞추기
            open_braces = fixed_str.count('{') - fixed_str.count('}')
            open_brackets = fixed_str.count('[') - fixed_str.count(']')
            
            # 누락된 닫는 괄호 추가
            fixed_str = fixed_str.rstrip()
            if fixed_str.endswith(','):
                fixed_str = fixed_str[:-1]
            
            fixed_str += ']' * open_brackets
            fixed_str += '}' * open_braces
            
            # 4. 파싱 시도
            result = json.loads(fixed_str)
            logger.info("JSON 복구 성공")
            return result
            
        except json.JSONDecodeError:
            pass
        
        # 5. 더 공격적인 복구 시도 - 유효한 부분만 추출
        try:
            # buttons, icons, text_fields 배열만 개별 추출 시도
            result = {"buttons": [], "icons": [], "text_fields": []}
            
            for key in ["buttons", "icons", "text_fields"]:
                pattern = rf'"{key}"\s*:\s*\[(.*?)\]'
                match = re.search(pattern, json_str, re.DOTALL)
                if match:
                    array_content = match.group(1).strip()
                    if array_content:
                        # 개별 객체 추출
                        objects = self._extract_objects_from_array(array_content)
                        result[key] = objects
            
            if any(result.values()):
                logger.info(f"JSON 부분 복구 성공: buttons={len(result['buttons'])}, icons={len(result['icons'])}, text_fields={len(result['text_fields'])}")
                return result
                
        except Exception as e:
            logger.debug(f"부분 복구 실패: {e}")
        
        logger.error("JSON 복구 실패")
        return None
    
    def _extract_objects_from_array(self, array_content: str) -> list:
        """배열 내용에서 개별 JSON 객체 추출
        
        Args:
            array_content: 배열 내부 문자열 (괄호 제외)
            
        Returns:
            파싱된 객체 리스트
        """
        objects = []
        depth = 0
        start = -1
        
        for i, char in enumerate(array_content):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    obj_str = array_content[start:i+1]
                    try:
                        obj = json.loads(obj_str)
                        objects.append(obj)
                    except json.JSONDecodeError:
                        # 개별 객체 파싱 실패 시 건너뜀
                        pass
                    start = -1
        
        return objects
    
    def _validate_and_enrich_elements(self, elements: list, required_fields: list) -> list:
        """UI 요소 리스트에서 필수 필드 검증 및 bounding_box 보정
        
        Requirements: 1.3, 2.3
        
        Args:
            elements: UI 요소 리스트
            required_fields: 필수 필드 목록
            
        Returns:
            유효하고 bounding_box가 보정된 요소 리스트
        """
        valid_elements = []
        for element in elements:
            if not all(field in element for field in required_fields):
                logger.warning(f"필수 필드 누락된 요소 제외: {element}")
                continue
            
            # bounding_box 보정: 누락 시 x, y, width, height로 계산
            element = self._ensure_bounding_box(element)
            valid_elements.append(element)
        
        return valid_elements
    
    def _ensure_bounding_box(self, element: dict) -> dict:
        """UI 요소에 bounding_box가 없으면 x, y, width, height로 계산하여 추가
        
        Requirements: 1.3, 2.3
        
        Args:
            element: UI 요소 딕셔너리
            
        Returns:
            bounding_box가 보정된 요소 딕셔너리
        """
        # 이미 bounding_box가 있고 유효하면 그대로 반환
        if 'bounding_box' in element and isinstance(element['bounding_box'], dict):
            bbox = element['bounding_box']
            if all(key in bbox for key in ['x', 'y', 'width', 'height']):
                return element
        
        # bounding_box 계산: 중심 좌표와 크기로부터 좌상단 좌표 계산
        x = element.get('x', 0)
        y = element.get('y', 0)
        width = element.get('width', 0)
        height = element.get('height', 0)
        
        # 좌상단 좌표 계산 (중심 좌표 - 크기/2)
        bbox_x = int(x - width / 2) if width > 0 else x
        bbox_y = int(y - height / 2) if height > 0 else y
        
        element['bounding_box'] = {
            'x': bbox_x,
            'y': bbox_y,
            'width': int(width),
            'height': int(height)
        }
        
        return element
    
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

    def find_element_at_position(
        self, 
        ui_data: Dict[str, Any], 
        x: int, 
        y: int, 
        tolerance: int = 50
    ) -> Optional[Dict[str, Any]]:
        """특정 좌표에서 가장 가까운 UI 요소 찾기
        
        Requirements: 1.2, 3.2
        
        주어진 좌표에서 가장 가까운 UI 요소를 반환한다.
        bounding_box 내부에 포함되는 요소를 우선적으로 찾고,
        없으면 tolerance 범위 내에서 가장 가까운 요소를 반환한다.
        
        Args:
            ui_data: UI 분석 결과 딕셔너리 (buttons, icons, text_fields 포함)
            x: 찾을 X 좌표
            y: 찾을 Y 좌표
            tolerance: 허용 오차 (픽셀 단위, 기본값: 50)
            
        Returns:
            가장 가까운 UI 요소 딕셔너리 또는 None
            반환되는 요소에는 'element_type' 필드가 추가됨 ('button', 'icon', 'text_field')
        """
        # 모든 UI 요소를 하나의 리스트로 수집 (타입 정보 포함)
        all_elements = []
        
        for button in ui_data.get("buttons", []):
            element = button.copy()
            element["element_type"] = "button"
            all_elements.append(element)
        
        for icon in ui_data.get("icons", []):
            element = icon.copy()
            element["element_type"] = "icon"
            all_elements.append(element)
        
        for text_field in ui_data.get("text_fields", []):
            element = text_field.copy()
            element["element_type"] = "text_field"
            all_elements.append(element)
        
        if not all_elements:
            logger.warning(f"UI 데이터에 요소가 없습니다. 좌표 ({x}, {y})에서 요소를 찾을 수 없습니다.")
            return None
        
        # 1단계: bounding_box 내부에 포함되는 요소 찾기
        contained_elements = []
        for element in all_elements:
            if self._is_point_in_bounding_box(element, x, y):
                # 중심 좌표와의 거리 계산
                distance = self._calculate_distance_to_center(element, x, y)
                contained_elements.append((element, distance))
        
        if contained_elements:
            # bounding_box 내부 요소 중 중심에 가장 가까운 요소 반환
            contained_elements.sort(key=lambda item: item[1])
            best_element = contained_elements[0][0]
            logger.debug(f"좌표 ({x}, {y})가 bounding_box 내부에 포함된 요소 발견: {best_element.get('text', best_element.get('type', best_element.get('content', 'unknown')))}")
            return best_element
        
        # 2단계: tolerance 범위 내에서 가장 가까운 요소 찾기
        closest_element = None
        min_distance = float('inf')
        
        for element in all_elements:
            distance = self._calculate_distance_to_center(element, x, y)
            if distance < min_distance and distance <= tolerance:
                min_distance = distance
                closest_element = element
        
        if closest_element:
            logger.debug(f"좌표 ({x}, {y})에서 tolerance {tolerance} 내 가장 가까운 요소 발견 (거리: {min_distance:.1f})")
            return closest_element
        
        logger.warning(f"좌표 ({x}, {y})에서 tolerance {tolerance} 내에 UI 요소를 찾을 수 없습니다.")
        return None

    def _is_point_in_bounding_box(self, element: Dict[str, Any], x: int, y: int) -> bool:
        """좌표가 요소의 bounding_box 내부에 있는지 확인
        
        Args:
            element: UI 요소 딕셔너리
            x: X 좌표
            y: Y 좌표
            
        Returns:
            bounding_box 내부에 있으면 True, 아니면 False
        """
        bbox = element.get("bounding_box")
        if not bbox or not isinstance(bbox, dict):
            return False
        
        bbox_x = bbox.get("x", 0)
        bbox_y = bbox.get("y", 0)
        bbox_width = bbox.get("width", 0)
        bbox_height = bbox.get("height", 0)
        
        # bounding_box 내부 포함 여부 확인
        return (bbox_x <= x <= bbox_x + bbox_width and 
                bbox_y <= y <= bbox_y + bbox_height)

    def _calculate_distance_to_center(self, element: Dict[str, Any], x: int, y: int) -> float:
        """좌표와 요소 중심 간의 유클리드 거리 계산
        
        Args:
            element: UI 요소 딕셔너리
            x: X 좌표
            y: Y 좌표
            
        Returns:
            유클리드 거리
        """
        import math
        
        center_x = element.get("x", 0)
        center_y = element.get("y", 0)
        
        return math.sqrt((center_x - x) ** 2 + (center_y - y) ** 2)
