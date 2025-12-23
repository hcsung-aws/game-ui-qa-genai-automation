#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vision LLM 직접 테스트 스크립트 (비대화형)

config.json의 model_id가 inference profile로 설정되어 있어야 합니다.
"""

import os
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("=" * 60)
    print("  Vision LLM 직접 테스트")
    print("=" * 60)
    
    try:
        from src.config_manager import ConfigManager
        from src.ui_analyzer import UIAnalyzer
        
        # 설정 로드
        config = ConfigManager()
        config.load_config()
        
        # AWS 설정 확인
        region = config.get('aws.region', 'ap-northeast-2')
        model_id = config.get('aws.model_id')
        
        print(f"\n[AWS 설정]")
        print(f"  Region: {region}")
        print(f"  Model ID: {model_id}")
        
        # UIAnalyzer 초기화
        analyzer = UIAnalyzer(config)
        
        if analyzer.bedrock_client is None:
            print("\n✗ FAIL: Bedrock 클라이언트 초기화 실패")
            return False
        
        print("\n✓ PASS: Bedrock 클라이언트 초기화 완료")
        
        # 스크린샷 캡처
        print("\n[스크린샷 캡처]")
        image = analyzer.capture_screenshot()
        print(f"  이미지 크기: {image.size}")
        
        # Vision LLM 분석
        print("\n[Vision LLM 분석 중...]")
        print("  (API 호출 중, 시간이 걸릴 수 있습니다)")
        
        result = analyzer.analyze_with_vision_llm(image)
        
        print("\n[분석 결과]")
        print(f"  버튼: {len(result.get('buttons', []))}개")
        print(f"  아이콘: {len(result.get('icons', []))}개")
        print(f"  텍스트 필드: {len(result.get('text_fields', []))}개")
        
        # 상세 정보 출력
        if result.get('buttons'):
            print("\n  [버튼 목록]")
            for i, btn in enumerate(result['buttons'][:5]):
                print(f"    {i+1}. '{btn.get('text', 'N/A')}' at ({btn.get('x')}, {btn.get('y')})")
        
        if result.get('text_fields'):
            print("\n  [텍스트 필드 목록]")
            for i, tf in enumerate(result['text_fields'][:5]):
                content = tf.get('content', 'N/A')
                if len(content) > 30:
                    content = content[:30] + "..."
                print(f"    {i+1}. '{content}' at ({tf.get('x')}, {tf.get('y')})")
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_path = f"screenshots/vision_llm_result_{timestamp}.json"
        os.makedirs("screenshots", exist_ok=True)
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n결과 저장됨: {result_path}")
        
        print("\n" + "=" * 60)
        print("  ✓ Vision LLM 테스트 성공!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        logger.exception("테스트 실패")
        return False

if __name__ == '__main__':
    main()
