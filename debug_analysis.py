#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""실패 케이스 분석 - bounding_box 포함 여부 확인"""

from PIL import Image
from src.config_manager import ConfigManager
from src.ui_analyzer import UIAnalyzer

config = ConfigManager('config.json')
config.load_config()
analyzer = UIAnalyzer(config)

# 실패 케이스: action_0001_before.png, 클릭 좌표 (432, 559)
test_cases = [
    ('screenshots/action_0001_before.png', 432, 559),
    ('screenshots/action_0005_before.png', 452, 142),
    ('screenshots/action_0009_before.png', 61, 67),
]

for filepath, click_x, click_y in test_cases:
    print("=" * 70)
    print(f"파일: {filepath}")
    print(f"클릭 좌표: ({click_x}, {click_y})")
    
    image = Image.open(filepath)
    print(f"이미지 크기: {image.size}")
    
    result = analyzer.analyze_with_retry(image)
    
    # 모든 요소 수집
    all_elements = []
    for btn in result.get('buttons', []):
        btn['_type'] = 'button'
        all_elements.append(btn)
    for icon in result.get('icons', []):
        icon['_type'] = 'icon'
        all_elements.append(icon)
    for tf in result.get('text_fields', []):
        tf['_type'] = 'text_field'
        all_elements.append(tf)
    
    print(f"감지된 요소: {len(all_elements)}개")
    
    # 클릭 좌표가 bounding_box 내부에 있는 요소 찾기
    contained = []
    for elem in all_elements:
        bbox = elem.get('bounding_box', {})
        bx = bbox.get('x', 0)
        by = bbox.get('y', 0)
        bw = bbox.get('width', 0)
        bh = bbox.get('height', 0)
        
        if bx <= click_x <= bx + bw and by <= click_y <= by + bh:
            contained.append(elem)
    
    if contained:
        print(f"✓ 클릭 좌표가 포함된 요소:")
        for elem in contained:
            name = elem.get('text', elem.get('type', elem.get('content', 'unknown')))
            print(f"  - [{elem['_type']}] '{name}' bbox: {elem.get('bounding_box')}")
    else:
        print(f"✗ 클릭 좌표가 포함된 요소 없음")
        
        # 가장 가까운 요소 찾기
        closest = None
        min_dist = float('inf')
        for elem in all_elements:
            ex, ey = elem.get('x', 0), elem.get('y', 0)
            dist = ((ex - click_x)**2 + (ey - click_y)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest = elem
        
        if closest:
            name = closest.get('text', closest.get('type', closest.get('content', 'unknown')))
            print(f"  가장 가까운 요소: [{closest['_type']}] '{name}' at ({closest.get('x')}, {closest.get('y')}), 거리: {min_dist:.1f}px")
            print(f"  bbox: {closest.get('bounding_box')}")
    
    print()
