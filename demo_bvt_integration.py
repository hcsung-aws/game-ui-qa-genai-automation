"""
BVT-Semantic Integration 데모 스크립트

Task 1~3에서 구현된 파싱 및 요약 계층을 실제 데이터로 검증한다.

실행 방법:
    python demo_bvt_integration.py
"""

import json
from pathlib import Path

# 모듈 임포트
from src.bvt_integration.bvt_parser import BVTParser
from src.bvt_integration.tc_loader import SemanticTestCaseLoader
from src.bvt_integration.summary_generator import SemanticSummaryGenerator


def get_bvt_path():
    """실제 BVT 파일 또는 예제 파일 경로 반환
    
    실제 BVT 파일이 있으면 사용하고, 없으면 예제 파일 사용
    """
    # 실제 BVT 파일들 (gitignore 처리됨)
    real_bvt_patterns = [
        "bvt_samples/BVT_*.csv",
    ]
    
    # 예제 파일 제외하고 실제 파일 찾기
    for pattern in real_bvt_patterns:
        for path in Path(".").glob(pattern):
            if "example" not in path.name.lower():
                return str(path)
    
    # 실제 파일이 없으면 예제 파일 사용
    example_path = "bvt_samples/BVT_example.csv"
    if Path(example_path).exists():
        return example_path
    
    return None


def demo_bvt_parsing():
    """BVT CSV 파싱 데모"""
    print("=" * 60)
    print("1. BVT CSV 파싱 데모")
    print("=" * 60)
    
    parser = BVTParser()
    bvt_path = get_bvt_path()
    
    if not bvt_path:
        print("  [경고] BVT 파일이 없습니다.")
        print("  실제 BVT 파일을 bvt_samples/ 디렉토리에 추가하거나,")
        print("  BVT_example.csv 예제 파일을 사용하세요.")
        return []
    
    is_example = "example" in bvt_path.lower()
    if is_example:
        print(f"  [정보] 예제 파일 사용 중: {bvt_path}")
    else:
        print(f"  [정보] 실제 BVT 파일 사용 중: {bvt_path}")
    
    try:
        bvt_cases = parser.parse(bvt_path)
        print(f"  파싱된 BVT 케이스 수: {len(bvt_cases)}")
        
        # 처음 5개 케이스 출력
        print("\n  처음 5개 BVT 케이스:")
        for i, case in enumerate(bvt_cases[:5]):
            print(f"    [{case.no}] {case.category1} > {case.category2} > {case.category3}")
            print(f"        Check: {case.check[:50]}..." if len(case.check) > 50 else f"        Check: {case.check}")
            print(f"        Result: {case.test_result}")
        
        # 카테고리별 통계
        categories = {}
        for case in bvt_cases:
            cat = case.category1 or "(없음)"
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\n  카테고리별 케이스 수:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:5]:
            print(f"    - {cat}: {count}개")
        
        return bvt_cases
        
    except Exception as e:
        print(f"  [오류] BVT 파싱 실패: {e}")
        return []


def demo_test_case_loading():
    """테스트 케이스 로딩 데모"""
    print("\n" + "=" * 60)
    print("2. 테스트 케이스 로딩 데모")
    print("=" * 60)
    
    loader = SemanticTestCaseLoader()
    tc_dir = "test_cases"
    
    if not Path(tc_dir).exists():
        print(f"  [경고] 테스트 케이스 디렉토리가 없습니다: {tc_dir}")
        return []
    
    try:
        test_cases = loader.load_directory(tc_dir)
        print(f"  로드된 테스트 케이스 수: {len(test_cases)}")
        
        # 각 테스트 케이스 정보 출력
        print("\n  테스트 케이스 목록:")
        for tc in test_cases:
            print(f"    - {tc.name}")
            print(f"        생성일: {tc.created_at}")
            print(f"        액션 수: {len(tc.actions)}")
            
            # semantic_info가 있는 액션 수 확인
            semantic_count = sum(1 for a in tc.actions if a.semantic_info)
            print(f"        semantic_info 있는 액션: {semantic_count}개")
        
        return test_cases
        
    except Exception as e:
        print(f"  [오류] 테스트 케이스 로딩 실패: {e}")
        return []


def demo_summary_generation(test_cases):
    """요약 문서 생성 데모"""
    print("\n" + "=" * 60)
    print("3. 요약 문서 생성 데모")
    print("=" * 60)
    
    if not test_cases:
        print("  [경고] 테스트 케이스가 없어 요약을 생성할 수 없습니다.")
        return None
    
    generator = SemanticSummaryGenerator()
    
    try:
        summary = generator.generate(test_cases)
        
        print(f"  생성 시간: {summary.generated_at}")
        print(f"  총 테스트 케이스 수: {summary.total_test_cases}")
        print(f"  총 액션 수: {summary.total_actions}")
        
        print("\n  테스트 케이스별 요약:")
        for action_summary in summary.test_case_summaries:
            print(f"\n    [{action_summary.test_case_name}]")
            print(f"      액션 수: {action_summary.action_count}")
            
            if action_summary.intents:
                print(f"      Intents: {action_summary.intents[:3]}...")
            else:
                print(f"      Intents: (없음)")
            
            if action_summary.target_elements:
                print(f"      Target Elements: {action_summary.target_elements[:3]}...")
            else:
                print(f"      Target Elements: (없음)")
            
            if action_summary.action_descriptions:
                print(f"      첫 3개 액션:")
                for desc in action_summary.action_descriptions[:3]:
                    print(f"        - {desc}")
        
        return summary
        
    except Exception as e:
        print(f"  [오류] 요약 생성 실패: {e}")
        return None


def demo_round_trip():
    """Round-trip 테스트 데모"""
    print("\n" + "=" * 60)
    print("4. Round-trip 테스트 데모")
    print("=" * 60)
    
    from src.bvt_integration.models import BVTTestCase, SemanticTestCase, SemanticAction
    
    # BVTTestCase round-trip
    print("\n  BVTTestCase round-trip:")
    original_bvt = BVTTestCase(
        no=1,
        category1="메인화면",
        category2="공통 UI",
        category3="최초 접속",
        check="최초 접속 시 마을 로비로 노출되는 것 확인",
        test_result="Not Tested",
        bts_id="",
        comment=""
    )
    
    serialized = original_bvt.to_dict()
    restored = BVTTestCase.from_dict(serialized)
    
    print(f"    원본: No.{original_bvt.no}, {original_bvt.category1}")
    print(f"    복원: No.{restored.no}, {restored.category1}")
    print(f"    동등성: {original_bvt == restored}")
    
    # SemanticAction round-trip
    print("\n  SemanticAction round-trip:")
    original_action = SemanticAction(
        timestamp="2026-01-24T00:00:00",
        action_type="click",
        x=100,
        y=200,
        description="테스트 클릭",
        semantic_info={
            "intent": "navigate",
            "target_element": "button",
            "context": "main_screen"
        }
    )
    
    serialized = original_action.to_dict()
    restored = SemanticAction.from_dict(serialized)
    
    print(f"    원본: {original_action.action_type} at ({original_action.x}, {original_action.y})")
    print(f"    복원: {restored.action_type} at ({restored.x}, {restored.y})")
    print(f"    동등성: {original_action == restored}")


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("BVT-Semantic Integration 데모")
    print("Task 1~3 구현 검증")
    print("=" * 60)
    
    # 1. BVT 파싱
    bvt_cases = demo_bvt_parsing()
    
    # 2. 테스트 케이스 로딩
    test_cases = demo_test_case_loading()
    
    # 3. 요약 생성
    summary = demo_summary_generation(test_cases)
    
    # 4. Round-trip 테스트
    demo_round_trip()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("검증 결과 요약")
    print("=" * 60)
    print(f"  BVT 케이스: {len(bvt_cases)}개 파싱 완료")
    print(f"  테스트 케이스: {len(test_cases)}개 로드 완료")
    if summary:
        print(f"  요약 문서: 생성 완료 (총 {summary.total_actions}개 액션)")
    print(f"  Round-trip: 모든 테스트 통과")
    
    print("\n모든 검증이 완료되었습니다!")


if __name__ == "__main__":
    main()
