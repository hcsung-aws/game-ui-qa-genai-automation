"""
Property-based tests for UIAnalyzer

**Feature: game-qa-automation, Property 2: 이미지 인코딩 round trip**
**Feature: game-qa-automation, Property 3: UI 분석 결과 구조 완전성**
**Feature: game-qa-automation, Property 4: Vision LLM 재시도 지수 백오프**

Validates: Requirements 2.2, 2.5, 2.7
"""

import io
import os
import sys
import tempfile
import json
from io import BytesIO

from hypothesis import given, settings, strategies as st, assume
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from unittest.mock import patch, Mock
from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer


# ============================================================================
# Strategies (데이터 생성 전략)
# ============================================================================

# 이미지 크기 전략 (너무 크면 테스트가 느려지므로 제한)
image_size_strategy = st.tuples(
    st.integers(min_value=10, max_value=200),
    st.integers(min_value=10, max_value=200)
)

# RGB 색상 전략
rgb_color_strategy = st.tuples(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)

# 이미지 모드 전략
image_mode_strategy = st.sampled_from(['RGB', 'RGBA', 'L'])


def create_test_image(width: int, height: int, color: tuple, mode: str = 'RGB') -> Image.Image:
    """테스트용 이미지 생성
    
    Args:
        width: 이미지 너비
        height: 이미지 높이
        color: RGB 색상 튜플
        mode: 이미지 모드 ('RGB', 'RGBA', 'L')
        
    Returns:
        PIL Image 객체
    """
    if mode == 'L':
        # 그레이스케일의 경우 첫 번째 색상 값만 사용
        return Image.new(mode, (width, height), color=color[0])
    elif mode == 'RGBA':
        # RGBA의 경우 알파 채널 추가
        return Image.new(mode, (width, height), color=color + (255,))
    else:
        return Image.new(mode, (width, height), color=color)


def create_analyzer_with_mock(tmp_path) -> UIAnalyzer:
    """Mock Bedrock 클라이언트로 UIAnalyzer 생성
    
    Args:
        tmp_path: 임시 디렉토리 경로
        
    Returns:
        UIAnalyzer 인스턴스
    """
    config_path = os.path.join(tmp_path, "config.json")
    config_data = {
        "aws": {
            "region": "ap-northeast-2",
            "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
            "max_tokens": 2000
        }
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f)
    
    config = ConfigManager(config_path)
    config.load_config()
    
    with patch('boto3.client'):
        analyzer = UIAnalyzer(config)
    
    return analyzer


# ============================================================================
# Property 2: 이미지 인코딩 round trip
# ============================================================================

@settings(max_examples=100, deadline=None)
@given(
    size=image_size_strategy,
    color=rgb_color_strategy
)
def test_image_encoding_round_trip_rgb(size, color):
    """
    **Feature: game-qa-automation, Property 2: 이미지 인코딩 round trip**
    
    For any 유효한 RGB 이미지, base64로 인코딩한 후 디코딩하면 
    원래 이미지와 동일한 크기와 모드를 가져야 한다.
    
    Validates: Requirements 2.2
    """
    width, height = size
    
    with tempfile.TemporaryDirectory() as tmp_path:
        analyzer = create_analyzer_with_mock(tmp_path)
        
        # 원본 이미지 생성
        original_image = create_test_image(width, height, color, 'RGB')
        
        # Round trip: encode -> decode
        encoded = analyzer.encode_image_to_base64(original_image)
        decoded_image = analyzer.decode_base64_to_image(encoded)
        
        # 크기 검증
        assert original_image.size == decoded_image.size, \
            f"Size mismatch: original {original_image.size} != decoded {decoded_image.size}"
        
        # 모드 검증 (PNG 저장 시 모드가 유지되어야 함)
        assert original_image.mode == decoded_image.mode, \
            f"Mode mismatch: original {original_image.mode} != decoded {decoded_image.mode}"
        
        # 픽셀 데이터 검증 (손실 없는 PNG 포맷이므로 동일해야 함)
        original_pixels = list(original_image.getdata())
        decoded_pixels = list(decoded_image.getdata())
        assert original_pixels == decoded_pixels, \
            "Pixel data mismatch after round trip"


@settings(max_examples=50, deadline=None)
@given(
    size=image_size_strategy,
    color=rgb_color_strategy
)
def test_image_encoding_round_trip_rgba(size, color):
    """
    **Feature: game-qa-automation, Property 2: 이미지 인코딩 round trip**
    
    For any 유효한 RGBA 이미지, base64로 인코딩한 후 디코딩하면 
    원래 이미지와 동일해야 한다.
    
    Validates: Requirements 2.2
    """
    width, height = size
    
    with tempfile.TemporaryDirectory() as tmp_path:
        analyzer = create_analyzer_with_mock(tmp_path)
        
        # 원본 RGBA 이미지 생성
        original_image = create_test_image(width, height, color, 'RGBA')
        
        # Round trip
        encoded = analyzer.encode_image_to_base64(original_image)
        decoded_image = analyzer.decode_base64_to_image(encoded)
        
        # 크기 검증
        assert original_image.size == decoded_image.size
        
        # 픽셀 데이터 검증
        original_pixels = list(original_image.getdata())
        decoded_pixels = list(decoded_image.getdata())
        assert original_pixels == decoded_pixels


@settings(max_examples=50, deadline=None)
@given(
    size=image_size_strategy,
    gray_value=st.integers(min_value=0, max_value=255)
)
def test_image_encoding_round_trip_grayscale(size, gray_value):
    """
    **Feature: game-qa-automation, Property 2: 이미지 인코딩 round trip**
    
    For any 유효한 그레이스케일 이미지, base64로 인코딩한 후 디코딩하면 
    원래 이미지와 동일해야 한다.
    
    Validates: Requirements 2.2
    """
    width, height = size
    
    with tempfile.TemporaryDirectory() as tmp_path:
        analyzer = create_analyzer_with_mock(tmp_path)
        
        # 원본 그레이스케일 이미지 생성
        original_image = Image.new('L', (width, height), color=gray_value)
        
        # Round trip
        encoded = analyzer.encode_image_to_base64(original_image)
        decoded_image = analyzer.decode_base64_to_image(encoded)
        
        # 크기 검증
        assert original_image.size == decoded_image.size
        
        # 픽셀 데이터 검증
        original_pixels = list(original_image.getdata())
        decoded_pixels = list(decoded_image.getdata())
        assert original_pixels == decoded_pixels


# ============================================================================
# Property 3: UI 분석 결과 구조 완전성
# ============================================================================

# UI 요소 전략
button_strategy = st.fixed_dictionaries({
    'text': st.text(min_size=1, max_size=20),
    'x': st.integers(min_value=0, max_value=1920),
    'y': st.integers(min_value=0, max_value=1080),
    'width': st.integers(min_value=10, max_value=500),
    'height': st.integers(min_value=10, max_value=200),
    'confidence': st.floats(min_value=0.0, max_value=1.0)
})

icon_strategy = st.fixed_dictionaries({
    'type': st.sampled_from(['settings', 'close', 'menu', 'home', 'back', 'search']),
    'x': st.integers(min_value=0, max_value=1920),
    'y': st.integers(min_value=0, max_value=1080),
    'confidence': st.floats(min_value=0.0, max_value=1.0)
})

text_field_strategy = st.fixed_dictionaries({
    'content': st.text(min_size=1, max_size=50),
    'x': st.integers(min_value=0, max_value=1920),
    'y': st.integers(min_value=0, max_value=1080),
    'confidence': st.floats(min_value=0.0, max_value=1.0)
})

# UI 분석 결과 전략
ui_analysis_result_strategy = st.fixed_dictionaries({
    'buttons': st.lists(button_strategy, min_size=0, max_size=10),
    'icons': st.lists(icon_strategy, min_size=0, max_size=10),
    'text_fields': st.lists(text_field_strategy, min_size=0, max_size=10)
})


@settings(max_examples=100, deadline=None)
@given(ui_data=ui_analysis_result_strategy)
def test_ui_analysis_result_structure_completeness(ui_data):
    """
    **Feature: game-qa-automation, Property 3: UI 분석 결과 구조 완전성**
    
    For any UI 분석 결과, 반환된 JSON은 buttons, icons, text_fields 키를 포함해야 하며,
    각 요소는 필수 좌표 정보(x, y)를 포함해야 한다.
    
    Validates: Requirements 2.7
    """
    # 필수 키 존재 확인
    assert 'buttons' in ui_data, "UI 분석 결과에 'buttons' 키가 없습니다"
    assert 'icons' in ui_data, "UI 분석 결과에 'icons' 키가 없습니다"
    assert 'text_fields' in ui_data, "UI 분석 결과에 'text_fields' 키가 없습니다"
    
    # 각 요소가 리스트인지 확인
    assert isinstance(ui_data['buttons'], list), "'buttons'는 리스트여야 합니다"
    assert isinstance(ui_data['icons'], list), "'icons'는 리스트여야 합니다"
    assert isinstance(ui_data['text_fields'], list), "'text_fields'는 리스트여야 합니다"
    
    # 각 버튼 요소의 필수 좌표 정보 확인
    for i, button in enumerate(ui_data['buttons']):
        assert 'x' in button, f"버튼 {i}에 'x' 좌표가 없습니다"
        assert 'y' in button, f"버튼 {i}에 'y' 좌표가 없습니다"
        assert isinstance(button['x'], (int, float)), f"버튼 {i}의 'x'는 숫자여야 합니다"
        assert isinstance(button['y'], (int, float)), f"버튼 {i}의 'y'는 숫자여야 합니다"
    
    # 각 아이콘 요소의 필수 좌표 정보 확인
    for i, icon in enumerate(ui_data['icons']):
        assert 'x' in icon, f"아이콘 {i}에 'x' 좌표가 없습니다"
        assert 'y' in icon, f"아이콘 {i}에 'y' 좌표가 없습니다"
        assert isinstance(icon['x'], (int, float)), f"아이콘 {i}의 'x'는 숫자여야 합니다"
        assert isinstance(icon['y'], (int, float)), f"아이콘 {i}의 'y'는 숫자여야 합니다"
    
    # 각 텍스트 필드 요소의 필수 좌표 정보 확인
    for i, text_field in enumerate(ui_data['text_fields']):
        assert 'x' in text_field, f"텍스트 필드 {i}에 'x' 좌표가 없습니다"
        assert 'y' in text_field, f"텍스트 필드 {i}에 'y' 좌표가 없습니다"
        assert isinstance(text_field['x'], (int, float)), f"텍스트 필드 {i}의 'x'는 숫자여야 합니다"
        assert isinstance(text_field['y'], (int, float)), f"텍스트 필드 {i}의 'y'는 숫자여야 합니다"


@settings(max_examples=100, deadline=None)
@given(ui_data=ui_analysis_result_strategy)
def test_ui_analysis_result_parsed_correctly(ui_data):
    """
    **Feature: game-qa-automation, Property 3: UI 분석 결과 구조 완전성**
    
    For any 유효한 UI 분석 JSON 응답, _parse_ui_response 메서드는 
    올바른 구조의 결과를 반환해야 한다.
    
    Validates: Requirements 2.7
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        analyzer = create_analyzer_with_mock(tmp_path)
        
        # JSON 문자열로 변환
        response_text = json.dumps(ui_data)
        
        # 파싱
        result = analyzer._parse_ui_response(response_text)
        
        # 필수 키 존재 확인
        assert 'buttons' in result
        assert 'icons' in result
        assert 'text_fields' in result
        
        # 각 요소의 필수 좌표 정보 확인 (유효한 요소만 포함)
        for button in result['buttons']:
            assert 'x' in button
            assert 'y' in button
        
        for icon in result['icons']:
            assert 'x' in icon
            assert 'y' in icon
        
        for text_field in result['text_fields']:
            assert 'x' in text_field
            assert 'y' in text_field


@settings(max_examples=50, deadline=None)
@given(ui_data=ui_analysis_result_strategy)
def test_ui_analysis_result_with_code_block(ui_data):
    """
    **Feature: game-qa-automation, Property 3: UI 분석 결과 구조 완전성**
    
    For any 유효한 UI 분석 결과가 코드 블록으로 감싸져 있어도,
    파싱 결과는 올바른 구조를 가져야 한다.
    
    Validates: Requirements 2.7
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        analyzer = create_analyzer_with_mock(tmp_path)
        
        # 코드 블록으로 감싼 JSON
        response_text = f"```json\n{json.dumps(ui_data)}\n```"
        
        # 파싱
        result = analyzer._parse_ui_response(response_text)
        
        # 필수 키 존재 확인
        assert 'buttons' in result
        assert 'icons' in result
        assert 'text_fields' in result


def test_ui_analysis_result_empty_response():
    """
    **Feature: game-qa-automation, Property 3: UI 분석 결과 구조 완전성**
    
    빈 응답이나 잘못된 JSON에 대해서도 기본 구조를 반환해야 한다.
    
    Validates: Requirements 2.7
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        analyzer = create_analyzer_with_mock(tmp_path)
        
        # 빈 응답
        result = analyzer._parse_ui_response("")
        assert result == {"buttons": [], "icons": [], "text_fields": []}
        
        # 잘못된 JSON
        result = analyzer._parse_ui_response("not valid json")
        assert result == {"buttons": [], "icons": [], "text_fields": []}
        
        # JSON이지만 필수 키 없음
        result = analyzer._parse_ui_response('{"other": "data"}')
        assert 'buttons' in result
        assert 'icons' in result
        assert 'text_fields' in result


@settings(max_examples=50, deadline=None)
@given(
    valid_elements=st.lists(
        st.fixed_dictionaries({
            'text': st.text(min_size=1, max_size=10),
            'x': st.integers(min_value=0, max_value=1000),
            'y': st.integers(min_value=0, max_value=1000)
        }),
        min_size=0,
        max_size=5
    ),
    invalid_elements=st.lists(
        st.fixed_dictionaries({
            'text': st.text(min_size=1, max_size=10)
            # x, y 좌표 없음
        }),
        min_size=0,
        max_size=5
    )
)
def test_validate_elements_filters_invalid(valid_elements, invalid_elements):
    """
    **Feature: game-qa-automation, Property 3: UI 분석 결과 구조 완전성**
    
    For any 요소 리스트, _validate_elements는 필수 필드(x, y)가 없는 요소를 
    필터링하고 유효한 요소만 반환해야 한다.
    
    Validates: Requirements 2.7
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        analyzer = create_analyzer_with_mock(tmp_path)
        
        # 유효한 요소와 무효한 요소 혼합
        mixed_elements = valid_elements + invalid_elements
        
        # 필터링
        result = analyzer._validate_elements(mixed_elements, ['x', 'y'])
        
        # 결과에는 유효한 요소만 포함되어야 함
        assert len(result) == len(valid_elements)
        
        # 모든 결과 요소에 x, y가 있어야 함
        for element in result:
            assert 'x' in element
            assert 'y' in element


# ============================================================================
# Property 4: Vision LLM 재시도 지수 백오프
# ============================================================================

# 재시도 횟수 전략 (1~5회)
retry_count_strategy = st.integers(min_value=1, max_value=5)

# 기본 지연 시간 전략 (0.1~2.0초)
base_delay_strategy = st.floats(min_value=0.1, max_value=2.0)


@settings(max_examples=100, deadline=None)
@given(
    retry_count=retry_count_strategy,
    base_delay=base_delay_strategy
)
def test_exponential_backoff_delay_pattern(retry_count, base_delay):
    """
    **Feature: game-qa-automation, Property 4: Vision LLM 재시도 지수 백오프**
    
    For any Vision LLM 요청 실패 시나리오, 재시도 간격은 지수적으로 증가해야 한다.
    즉, n번째 재시도의 지연 시간은 base_delay * (2 ** (n-1))이어야 한다.
    
    Validates: Requirements 2.5
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        config_path = os.path.join(tmp_path, "config.json")
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "model_id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "retry_delay": base_delay
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(config_path)
        config.load_config()
        
        # Mock Bedrock 클라이언트 - 항상 실패
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("API Error")
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
            
            # sleep 호출 기록
            sleep_calls = []
            
            def mock_sleep(duration):
                sleep_calls.append(duration)
            
            with patch('time.sleep', side_effect=mock_sleep):
                # OCR 폴백도 빈 결과 반환하도록 설정
                with patch.object(analyzer, 'analyze_with_ocr', return_value=[]):
                    test_image = Image.new('RGB', (100, 100), color='white')
                    analyzer.analyze_with_retry(test_image, retry_count=retry_count)
        
        # 재시도 횟수 검증: retry_count번 시도하면 (retry_count - 1)번 sleep
        expected_sleep_count = retry_count - 1
        assert len(sleep_calls) == expected_sleep_count, \
            f"Expected {expected_sleep_count} sleep calls, got {len(sleep_calls)}"
        
        # 지수 백오프 패턴 검증
        for i, actual_delay in enumerate(sleep_calls):
            expected_delay = base_delay * (2 ** i)
            # 부동소수점 비교를 위해 약간의 오차 허용
            assert abs(actual_delay - expected_delay) < 0.001, \
                f"Sleep call {i}: expected {expected_delay}, got {actual_delay}"


@settings(max_examples=100, deadline=None)
@given(retry_count=retry_count_strategy)
def test_retry_count_limit(retry_count):
    """
    **Feature: game-qa-automation, Property 4: Vision LLM 재시도 지수 백오프**
    
    For any 재시도 횟수 설정, Vision LLM 호출은 정확히 해당 횟수만큼만 시도되어야 한다.
    
    Validates: Requirements 2.5
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        config_path = os.path.join(tmp_path, "config.json")
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "retry_delay": 0.01  # 테스트 속도를 위해 짧은 지연
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(config_path)
        config.load_config()
        
        # Mock Bedrock 클라이언트 - 항상 실패
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("API Error")
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
            
            with patch('time.sleep'):
                with patch.object(analyzer, 'analyze_with_ocr', return_value=[]):
                    test_image = Image.new('RGB', (100, 100), color='white')
                    analyzer.analyze_with_retry(test_image, retry_count=retry_count)
        
        # Vision LLM 호출 횟수 검증
        assert mock_bedrock.invoke_model.call_count == retry_count, \
            f"Expected {retry_count} API calls, got {mock_bedrock.invoke_model.call_count}"


@settings(max_examples=50, deadline=None)
@given(
    success_on_attempt=st.integers(min_value=1, max_value=3),
    retry_count=st.integers(min_value=3, max_value=5)
)
def test_retry_stops_on_success(success_on_attempt, retry_count):
    """
    **Feature: game-qa-automation, Property 4: Vision LLM 재시도 지수 백오프**
    
    For any 성공 시나리오, 성공하면 즉시 재시도를 중단하고 결과를 반환해야 한다.
    
    Validates: Requirements 2.5
    """
    # success_on_attempt가 retry_count보다 크면 테스트 스킵
    assume(success_on_attempt <= retry_count)
    
    with tempfile.TemporaryDirectory() as tmp_path:
        config_path = os.path.join(tmp_path, "config.json")
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "retry_delay": 0.01
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(config_path)
        config.load_config()
        
        # Mock 응답 생성
        mock_response = {
            "content": [{"text": json.dumps({"buttons": [], "icons": [], "text_fields": []})}]
        }
        
        # Mock Bedrock 클라이언트 - success_on_attempt번째에 성공
        mock_bedrock = Mock()
        side_effects = [Exception("API Error")] * (success_on_attempt - 1)
        side_effects.append({'body': io.BytesIO(json.dumps(mock_response).encode())})
        mock_bedrock.invoke_model.side_effect = side_effects
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
            
            with patch('time.sleep'):
                test_image = Image.new('RGB', (100, 100), color='white')
                result = analyzer.analyze_with_retry(test_image, retry_count=retry_count)
        
        # 성공 시 호출 횟수 검증
        assert mock_bedrock.invoke_model.call_count == success_on_attempt, \
            f"Expected {success_on_attempt} API calls, got {mock_bedrock.invoke_model.call_count}"
        
        # 성공 결과 검증
        assert result.get("source") == "vision_llm", \
            f"Expected source 'vision_llm', got '{result.get('source')}'"


@settings(max_examples=50, deadline=None)
@given(retry_count=st.integers(min_value=1, max_value=5))
def test_ocr_fallback_after_all_retries_fail(retry_count):
    """
    **Feature: game-qa-automation, Property 4: Vision LLM 재시도 지수 백오프**
    
    For any 모든 재시도 실패 시나리오, 모든 재시도가 실패하면 OCR 폴백을 시도해야 한다.
    
    Validates: Requirements 2.5, 2.6
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        config_path = os.path.join(tmp_path, "config.json")
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "retry_delay": 0.01
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(config_path)
        config.load_config()
        
        # Mock Bedrock 클라이언트 - 항상 실패
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("API Error")
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
            
            # OCR 폴백 호출 추적
            ocr_called = [False]
            original_ocr = analyzer.analyze_with_ocr
            
            def mock_ocr(image):
                ocr_called[0] = True
                return [{"text": "OCR Text", "confidence": 0.9, "bbox": [], "x": 50, "y": 50}]
            
            with patch('time.sleep'):
                with patch.object(analyzer, 'analyze_with_ocr', side_effect=mock_ocr):
                    test_image = Image.new('RGB', (100, 100), color='white')
                    result = analyzer.analyze_with_retry(test_image, retry_count=retry_count)
        
        # Vision LLM이 retry_count번 호출되었는지 확인
        assert mock_bedrock.invoke_model.call_count == retry_count
        
        # OCR 폴백이 호출되었는지 확인
        assert ocr_called[0], "OCR fallback should be called after all retries fail"
        
        # 결과가 OCR 폴백 소스인지 확인
        assert result.get("source") == "ocr_fallback", \
            f"Expected source 'ocr_fallback', got '{result.get('source')}'"


def test_default_retry_count_is_three():
    """
    **Feature: game-qa-automation, Property 4: Vision LLM 재시도 지수 백오프**
    
    기본 재시도 횟수는 3회여야 한다.
    
    Validates: Requirements 2.5
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        config_path = os.path.join(tmp_path, "config.json")
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "retry_delay": 0.01
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(config_path)
        config.load_config()
        
        # Mock Bedrock 클라이언트 - 항상 실패
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("API Error")
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
            
            with patch('time.sleep'):
                with patch.object(analyzer, 'analyze_with_ocr', return_value=[]):
                    test_image = Image.new('RGB', (100, 100), color='white')
                    # retry_count 인자 없이 호출 (기본값 사용)
                    analyzer.analyze_with_retry(test_image)
        
        # 기본 재시도 횟수 3회 검증
        assert mock_bedrock.invoke_model.call_count == 3, \
            f"Default retry count should be 3, got {mock_bedrock.invoke_model.call_count}"


@settings(max_examples=30, deadline=None)
@given(
    base_delay=st.floats(min_value=0.5, max_value=2.0)
)
def test_exponential_backoff_specific_delays(base_delay):
    """
    **Feature: game-qa-automation, Property 4: Vision LLM 재시도 지수 백오프**
    
    For any 기본 지연 시간, 3회 재시도 시 지연 시간은 정확히 
    base_delay, base_delay*2, base_delay*4 패턴을 따라야 한다.
    (첫 번째 실패 후 base_delay, 두 번째 실패 후 base_delay*2)
    
    Validates: Requirements 2.5
    """
    with tempfile.TemporaryDirectory() as tmp_path:
        config_path = os.path.join(tmp_path, "config.json")
        config_data = {
            "aws": {
                "region": "ap-northeast-2",
                "retry_delay": base_delay
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(config_path)
        config.load_config()
        
        # Mock Bedrock 클라이언트 - 항상 실패
        mock_bedrock = Mock()
        mock_bedrock.invoke_model.side_effect = Exception("API Error")
        
        with patch('boto3.client', return_value=mock_bedrock):
            analyzer = UIAnalyzer(config)
            
            sleep_calls = []
            
            def mock_sleep(duration):
                sleep_calls.append(duration)
            
            with patch('time.sleep', side_effect=mock_sleep):
                with patch.object(analyzer, 'analyze_with_ocr', return_value=[]):
                    test_image = Image.new('RGB', (100, 100), color='white')
                    analyzer.analyze_with_retry(test_image, retry_count=3)
        
        # 3회 재시도 시 2번의 sleep 호출
        assert len(sleep_calls) == 2, f"Expected 2 sleep calls, got {len(sleep_calls)}"
        
        # 지수 백오프 패턴 검증: base_delay * 2^0, base_delay * 2^1
        expected_delays = [base_delay * (2 ** i) for i in range(2)]
        
        for i, (actual, expected) in enumerate(zip(sleep_calls, expected_delays)):
            assert abs(actual - expected) < 0.001, \
                f"Sleep call {i}: expected {expected:.3f}, got {actual:.3f}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
