#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 2 수동 테스트 스크립트

이 스크립트는 Phase 2의 핵심 기능을 실제 환경에서 테스트합니다.
- 시나리오 1: 스크린샷 캡처
- 시나리오 3: Vision LLM UI 분석

실행 방법:
    python test_phase2_manual.py

Requirements: 2.1, 2.3, 2.4, 2.7
"""

import os
import sys
import json
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """테스트 섹션 헤더 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(success: bool, message: str):
    """테스트 결과 출력"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {message}")


def test_screenshot_capture():
    """시나리오 1: 스크린샷 캡처 기능 테스트
    
    Requirements: 2.1
    """
    print_header("시나리오 1: 스크린샷 캡처 기능")
    
    try:
        from src.config_manager import ConfigManager
        from src.ui_analyzer import UIAnalyzer
        
        # 설정 로드
        config = ConfigManager()
        config.load_config()
        print_result(True, "설정 파일 로드 완료")
        
        # UIAnalyzer 초기화 (Bedrock 클라이언트 초기화 시도)
        analyzer = UIAnalyzer(config)
        print_result(True, "UIAnalyzer 초기화 완료")
        
        # 스크린샷 디렉토리 확인
        screenshot_dir = config.get('automation.screenshot_dir', 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # 스크린샷 캡처
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"{screenshot_dir}/manual_test_{timestamp}.png"
        
        print(f"\n스크린샷 캡처 중...")
        image = analyzer.capture_screenshot(save_path)
        
        # 결과 검증
        print(f"\n=== 캡처 결과 ===")
        print(f"이미지 크기: {image.size}")
        print(f"이미지 모드: {image.mode}")
        print(f"저장 경로: {save_path}")
        
        # 파일 존재 확인
        file_exists = os.path.exists(save_path)
        print_result(file_exists, f"스크린샷 파일 생성됨: {save_path}")
        
        if file_exists:
            file_size = os.path.getsize(save_path)
            print(f"파일 크기: {file_size:,} bytes")
        
        # 검증 항목 체크리스트
        print("\n=== 검증 항목 ===")
        print_result(image is not None, "스크린샷 객체가 생성됨")
        print_result(image.size[0] > 0 and image.size[1] > 0, "이미지 크기가 유효함")
        print_result(file_exists, "스크린샷 파일이 저장됨")
        print_result(image.mode in ['RGB', 'RGBA'], f"이미지 모드가 유효함 ({image.mode})")
        
        return True
        
    except Exception as e:
        print_result(False, f"스크린샷 캡처 실패: {e}")
        logger.exception("스크린샷 캡처 중 오류 발생")
        return False


def test_vision_llm_analysis():
    """시나리오 3: Vision LLM UI 분석 테스트
    
    Requirements: 2.3, 2.4, 2.7
    
    주의: 이 테스트는 실제 AWS Bedrock API를 호출합니다.
    - AWS 자격 증명이 설정되어 있어야 합니다.
    - API 호출 비용이 발생할 수 있습니다.
    """
    print_header("시나리오 3: Vision LLM UI 분석")
    
    try:
        from src.config_manager import ConfigManager
        from src.ui_analyzer import UIAnalyzer
        
        # 설정 로드
        config = ConfigManager()
        config.load_config()
        
        # AWS 설정 확인
        region = config.get('aws.region', 'ap-northeast-2')
        model_id = config.get('aws.model_id', 'anthropic.claude-sonnet-4-5-20250929-v1:0')
        
        print(f"\n=== AWS 설정 ===")
        print(f"Region: {region}")
        print(f"Model ID: {model_id}")
        
        # UIAnalyzer 초기화
        analyzer = UIAnalyzer(config)
        
        # Bedrock 클라이언트 확인
        if analyzer.bedrock_client is None:
            print_result(False, "Bedrock 클라이언트 초기화 실패")
            print("\n[해결 방법]")
            print("1. AWS CLI 설정 확인: aws configure")
            print("2. 환경 변수 설정:")
            print("   $env:AWS_ACCESS_KEY_ID = 'your_access_key'")
            print("   $env:AWS_SECRET_ACCESS_KEY = 'your_secret_key'")
            return False
        
        print_result(True, "Bedrock 클라이언트 초기화 완료")
        
        # 스크린샷 캡처
        print(f"\n스크린샷 캡처 중...")
        image = analyzer.capture_screenshot()
        print(f"캡처된 이미지 크기: {image.size}")
        
        # Vision LLM 분석
        print(f"\nVision LLM 분석 중... (시간이 걸릴 수 있습니다)")
        
        try:
            result = analyzer.analyze_with_vision_llm(image)
            
            print(f"\n=== UI 분석 결과 ===")
            print(f"버튼: {len(result.get('buttons', []))}개")
            print(f"아이콘: {len(result.get('icons', []))}개")
            print(f"텍스트 필드: {len(result.get('text_fields', []))}개")
            
            # 상세 정보 출력
            if result.get('buttons'):
                print(f"\n[버튼 목록]")
                for i, btn in enumerate(result['buttons'][:5]):  # 최대 5개만 출력
                    print(f"  {i+1}. '{btn.get('text', 'N/A')}' at ({btn.get('x')}, {btn.get('y')})")
            
            if result.get('icons'):
                print(f"\n[아이콘 목록]")
                for i, icon in enumerate(result['icons'][:5]):
                    print(f"  {i+1}. '{icon.get('type', 'N/A')}' at ({icon.get('x')}, {icon.get('y')})")
            
            if result.get('text_fields'):
                print(f"\n[텍스트 필드 목록]")
                for i, tf in enumerate(result['text_fields'][:5]):
                    content = tf.get('content', 'N/A')
                    if len(content) > 30:
                        content = content[:30] + "..."
                    print(f"  {i+1}. '{content}' at ({tf.get('x')}, {tf.get('y')})")
            
            # 검증 항목 체크리스트
            print("\n=== 검증 항목 ===")
            print_result('buttons' in result, "응답에 'buttons' 키 포함됨")
            print_result('icons' in result, "응답에 'icons' 키 포함됨")
            print_result('text_fields' in result, "응답에 'text_fields' 키 포함됨")
            
            # 좌표 정보 검증
            all_elements = result.get('buttons', []) + result.get('icons', []) + result.get('text_fields', [])
            coords_valid = all('x' in e and 'y' in e for e in all_elements) if all_elements else True
            print_result(coords_valid, "모든 UI 요소에 좌표 정보(x, y) 포함됨")
            
            # 결과 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_path = f"screenshots/analysis_result_{timestamp}.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n분석 결과 저장됨: {result_path}")
            
            return True
            
        except Exception as api_error:
            print_result(False, f"Vision LLM API 호출 실패: {api_error}")
            
            # 오류 유형별 안내
            error_str = str(api_error)
            if "AccessDeniedException" in error_str:
                print("\n[해결 방법]")
                print("1. AWS 콘솔에서 Bedrock 모델 접근 권한 요청")
                print("2. IAM 정책에 'bedrock:InvokeModel' 권한 추가")
            elif "NoCredentialsError" in error_str:
                print("\n[해결 방법]")
                print("1. AWS CLI 설정: aws configure")
                print("2. 환경 변수 설정 확인")
            elif "ExpiredTokenException" in error_str:
                print("\n[해결 방법]")
                print("1. AWS 자격 증명 갱신 필요")
            
            return False
        
    except ImportError as e:
        print_result(False, f"모듈 import 실패: {e}")
        return False
    except Exception as e:
        print_result(False, f"테스트 실패: {e}")
        logger.exception("Vision LLM 분석 중 오류 발생")
        return False


def test_base64_encoding():
    """시나리오 2: Base64 인코딩/디코딩 테스트
    
    Requirements: 2.2
    """
    print_header("시나리오 2: Base64 인코딩/디코딩")
    
    try:
        from src.config_manager import ConfigManager
        from src.ui_analyzer import UIAnalyzer
        
        config = ConfigManager()
        config.load_config()
        analyzer = UIAnalyzer(config)
        
        # 스크린샷 캡처
        print("스크린샷 캡처 중...")
        original = analyzer.capture_screenshot()
        print(f"원본 이미지 크기: {original.size}")
        print(f"원본 이미지 모드: {original.mode}")
        
        # Base64 인코딩
        print("\nBase64 인코딩 중...")
        encoded = analyzer.encode_image_to_base64(original)
        print(f"인코딩된 문자열 길이: {len(encoded):,} 문자")
        
        # Base64 디코딩
        print("\nBase64 디코딩 중...")
        decoded = analyzer.decode_base64_to_image(encoded)
        print(f"디코딩된 이미지 크기: {decoded.size}")
        print(f"디코딩된 이미지 모드: {decoded.mode}")
        
        # 검증
        print("\n=== 검증 항목 ===")
        size_match = original.size == decoded.size
        mode_match = original.mode == decoded.mode
        
        print_result(len(encoded) > 0, "Base64 인코딩 성공")
        print_result(size_match, f"크기 일치: {original.size} == {decoded.size}")
        print_result(mode_match, f"모드 일치: {original.mode} == {decoded.mode}")
        
        return size_match and mode_match
        
    except Exception as e:
        print_result(False, f"테스트 실패: {e}")
        return False


def main():
    """메인 함수 - 테스트 시나리오 선택 및 실행"""
    print("\n" + "=" * 60)
    print("  Phase 2 수동 테스트 스크립트")
    print("=" * 60)
    print("""
이 스크립트는 Phase 2의 핵심 기능을 실제 환경에서 테스트합니다.

테스트 시나리오:
  1. 스크린샷 캡처 (Requirements 2.1)
  2. Base64 인코딩/디코딩 (Requirements 2.2)
  3. Vision LLM UI 분석 (Requirements 2.3, 2.4, 2.7)
     ⚠️  AWS 자격 증명 필요, API 비용 발생 가능
  4. 모든 테스트 실행
  0. 종료
""")
    
    results = {}
    
    while True:
        try:
            choice = input("\n테스트 번호를 선택하세요 (0-4): ").strip()
            
            if choice == '0':
                print("\n테스트를 종료합니다.")
                break
            elif choice == '1':
                results['screenshot'] = test_screenshot_capture()
            elif choice == '2':
                results['base64'] = test_base64_encoding()
            elif choice == '3':
                print("\n⚠️  주의: 이 테스트는 실제 AWS Bedrock API를 호출합니다.")
                print("   - AWS 자격 증명이 설정되어 있어야 합니다.")
                print("   - API 호출 비용이 발생할 수 있습니다.")
                confirm = input("\n계속하시겠습니까? (y/n): ").strip().lower()
                if confirm == 'y':
                    results['vision_llm'] = test_vision_llm_analysis()
                else:
                    print("테스트를 건너뜁니다.")
            elif choice == '4':
                print("\n모든 테스트를 실행합니다...")
                results['screenshot'] = test_screenshot_capture()
                results['base64'] = test_base64_encoding()
                
                print("\n⚠️  Vision LLM 테스트는 AWS API를 호출합니다.")
                confirm = input("Vision LLM 테스트도 실행하시겠습니까? (y/n): ").strip().lower()
                if confirm == 'y':
                    results['vision_llm'] = test_vision_llm_analysis()
            else:
                print("잘못된 선택입니다. 0-4 사이의 숫자를 입력하세요.")
                continue
            
            # 결과 요약 출력
            if results:
                print_header("테스트 결과 요약")
                for test_name, passed in results.items():
                    status = "✓ PASS" if passed else "✗ FAIL"
                    print(f"  {test_name}: {status}")
                
        except KeyboardInterrupt:
            print("\n\n테스트가 중단되었습니다.")
            break
        except Exception as e:
            print(f"\n오류 발생: {e}")
            continue


if __name__ == '__main__':
    main()
