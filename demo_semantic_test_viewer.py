"""
의미론적 테스트 케이스 뷰어

semantic_info가 포함된 테스트 케이스를 분석하고 시각화한다.

실행 방법:
    python demo_semantic_test_viewer.py [테스트케이스_경로]
    
예시:
    python demo_semantic_test_viewer.py test_cases/sr-semantic-test-001_semantic.json
"""

import json
import sys
from pathlib import Path
from typing import Optional

# 모듈 임포트
from src.bvt_integration.tc_loader import SemanticTestCaseLoader
from src.bvt_integration.summary_generator import SemanticSummaryGenerator
from src.bvt_integration.bvt_parser import BVTParser


def print_header(title: str, char: str = "="):
    """헤더 출력"""
    print(f"\n{char * 70}")
    print(f"  {title}")
    print(f"{char * 70}")


def print_subheader(title: str):
    """서브헤더 출력"""
    print(f"\n  {'-' * 50}")
    print(f"  {title}")
    print(f"  {'-' * 50}")


def view_test_case(file_path: str):
    """테스트 케이스 상세 보기"""
    print_header(f"테스트 케이스 분석: {Path(file_path).name}")
    
    loader = SemanticTestCaseLoader()
    test_case = loader.load_file(file_path)
    
    if not test_case:
        print("  [오류] 테스트 케이스를 로드할 수 없습니다.")
        return None
    
    # 기본 정보
    print_subheader("기본 정보")
    print(f"    이름: {test_case.name}")
    print(f"    생성일: {test_case.created_at}")
    print(f"    총 액션 수: {len(test_case.actions)}")
    
    # semantic_info 통계
    semantic_actions = [a for a in test_case.actions if a.semantic_info]
    print(f"    semantic_info 있는 액션: {len(semantic_actions)}개")
    
    # 액션 타입별 통계
    action_types = {}
    for action in test_case.actions:
        action_types[action.action_type] = action_types.get(action.action_type, 0) + 1
    
    print(f"\n    액션 타입별 분포:")
    for atype, count in sorted(action_types.items(), key=lambda x: -x[1]):
        print(f"      - {atype}: {count}개")
    
    return test_case


def view_semantic_info(test_case):
    """semantic_info 상세 보기"""
    print_header("의미론적 정보 분석", "-")
    
    semantic_actions = [a for a in test_case.actions if a.semantic_info]
    
    if not semantic_actions:
        print("  semantic_info가 있는 액션이 없습니다.")
        return
    
    # Intent 분석
    print_subheader("Intent 분석")
    intents = {}
    for action in semantic_actions:
        intent = action.semantic_info.get("intent", "unknown")
        intents[intent] = intents.get(intent, 0) + 1
    
    for intent, count in sorted(intents.items(), key=lambda x: -x[1]):
        print(f"    - {intent}: {count}회")
    
    # Target Element 분석
    print_subheader("Target Element 분석")
    elements = []
    for action in semantic_actions:
        target = action.semantic_info.get("target_element", {})
        if target:
            elem_type = target.get("type", "unknown")
            elem_text = target.get("text", "")
            confidence = target.get("confidence", 0)
            elements.append({
                "type": elem_type,
                "text": elem_text,
                "confidence": confidence,
                "description": target.get("description", "")
            })
    
    print(f"    총 {len(elements)}개의 타겟 요소 감지됨\n")
    
    for i, elem in enumerate(elements, 1):
        conf_bar = "█" * int(elem["confidence"] * 10) + "░" * (10 - int(elem["confidence"] * 10))
        print(f"    [{i}] {elem['type']}: \"{elem['text']}\"")
        print(f"        설명: {elem['description']}")
        print(f"        신뢰도: [{conf_bar}] {elem['confidence']:.0%}")
        print()


def view_action_timeline(test_case):
    """액션 타임라인 보기"""
    print_header("액션 타임라인", "-")
    
    for i, action in enumerate(test_case.actions):
        # 액션 타입에 따른 아이콘
        icons = {
            "click": "🖱️",
            "wait": "⏳",
            "key_press": "⌨️",
            "scroll": "📜"
        }
        icon = icons.get(action.action_type, "❓")
        
        # semantic_info 여부
        has_semantic = "✅" if action.semantic_info else "❌"
        
        # 기본 정보
        print(f"  {icon} [{i:02d}] {action.action_type.upper()}")
        print(f"       설명: {action.description}")
        print(f"       semantic_info: {has_semantic}")
        
        # semantic_info가 있으면 상세 출력
        if action.semantic_info:
            intent = action.semantic_info.get("intent", "unknown")
            target = action.semantic_info.get("target_element", {})
            target_text = target.get("text", "") if target else ""
            confidence = target.get("confidence", 0) if target else 0
            
            print(f"       → Intent: {intent}")
            if target_text:
                print(f"       → Target: \"{target_text}\" (신뢰도: {confidence:.0%})")
        
        print()


def generate_summary_report(test_case):
    """요약 리포트 생성"""
    print_header("요약 리포트 생성", "-")
    
    generator = SemanticSummaryGenerator()
    summary = generator.generate([test_case])
    
    print(f"  생성 시간: {summary.generated_at}")
    print(f"  총 테스트 케이스: {summary.total_test_cases}")
    print(f"  총 액션: {summary.total_actions}")
    
    if summary.test_case_summaries:
        action_summary = summary.test_case_summaries[0]
        
        print_subheader("ActionSummary 내용")
        print(f"    테스트 케이스: {action_summary.test_case_name}")
        print(f"    액션 수: {action_summary.action_count}")
        
        if action_summary.intents:
            print(f"\n    Intents ({len(action_summary.intents)}개):")
            for intent in action_summary.intents:
                print(f"      - {intent}")
        
        if action_summary.target_elements:
            print(f"\n    Target Elements ({len(action_summary.target_elements)}개):")
            for elem in action_summary.target_elements:
                print(f"      - {elem}")
        
        if action_summary.screen_states:
            print(f"\n    Screen States ({len(action_summary.screen_states)}개):")
            for state in action_summary.screen_states:
                print(f"      - {state}")
    
    return summary


def find_bvt_matches(test_case, bvt_path: str = None):
    """BVT 매칭 후보 찾기 (간단한 텍스트 매칭)"""
    print_header("BVT 매칭 후보 탐색 (Preview)", "-")
    
    # BVT 파일 경로 결정
    if bvt_path is None:
        # 실제 BVT 파일 찾기 (예제 제외)
        for path in Path("bvt_samples").glob("BVT_*.csv"):
            if "example" not in path.name.lower():
                bvt_path = str(path)
                break
        
        # 실제 파일이 없으면 예제 사용
        if bvt_path is None:
            bvt_path = "bvt_samples/BVT_example.csv"
    
    if not Path(bvt_path).exists():
        print(f"  [경고] BVT 파일이 없습니다: {bvt_path}")
        return
    
    is_example = "example" in bvt_path.lower()
    if is_example:
        print(f"  [정보] 예제 파일 사용 중: {bvt_path}")
    else:
        print(f"  [정보] 실제 BVT 파일 사용 중: {bvt_path}")
    
    parser = BVTParser()
    bvt_cases = parser.parse(bvt_path)
    
    # 테스트 케이스에서 키워드 추출
    keywords = set()
    for action in test_case.actions:
        if action.semantic_info:
            target = action.semantic_info.get("target_element", {})
            if target:
                text = target.get("text", "")
                if text:
                    keywords.add(text.lower())
    
    print(f"  추출된 키워드: {keywords}")
    print()
    
    # 간단한 텍스트 매칭으로 후보 찾기
    matches = []
    for bvt_case in bvt_cases:
        check_lower = bvt_case.check.lower()
        for keyword in keywords:
            if keyword in check_lower:
                matches.append({
                    "bvt_no": bvt_case.no,
                    "category": f"{bvt_case.category1} > {bvt_case.category2} > {bvt_case.category3}",
                    "check": bvt_case.check,
                    "matched_keyword": keyword
                })
                break
    
    if matches:
        print(f"  {len(matches)}개의 잠재적 매칭 발견:\n")
        for match in matches[:10]:  # 최대 10개만 표시
            print(f"    [BVT #{match['bvt_no']}]")
            print(f"      Category: {match['category']}")
            print(f"      Check: {match['check'][:60]}...")
            print(f"      매칭 키워드: \"{match['matched_keyword']}\"")
            print()
    else:
        print("  매칭되는 BVT 항목이 없습니다.")
        print("  (참고: 이것은 간단한 키워드 매칭입니다. Task 5에서 구현될 MatchingAnalyzer가 더 정교한 매칭을 수행합니다.)")


def export_to_markdown(test_case, output_path: str = None):
    """Markdown 리포트로 내보내기"""
    if output_path is None:
        output_path = f"reports/{test_case.name}_analysis.md"
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    generator = SemanticSummaryGenerator()
    summary = generator.generate([test_case])
    action_summary = summary.test_case_summaries[0] if summary.test_case_summaries else None
    
    md_content = f"""# 테스트 케이스 분석 리포트

## 기본 정보

| 항목 | 값 |
|------|-----|
| 이름 | {test_case.name} |
| 생성일 | {test_case.created_at} |
| 총 액션 수 | {len(test_case.actions)} |
| semantic_info 있는 액션 | {len([a for a in test_case.actions if a.semantic_info])} |

## 액션 타임라인

| # | 타입 | 설명 | Intent | Target |
|---|------|------|--------|--------|
"""
    
    for i, action in enumerate(test_case.actions):
        intent = ""
        target = ""
        if action.semantic_info:
            intent = action.semantic_info.get("intent", "")
            target_elem = action.semantic_info.get("target_element", {})
            target = target_elem.get("text", "") if target_elem else ""
        
        md_content += f"| {i} | {action.action_type} | {action.description} | {intent} | {target} |\n"
    
    if action_summary:
        md_content += f"""
## 요약 정보

### Intents
{chr(10).join(f'- {i}' for i in action_summary.intents) if action_summary.intents else '- (없음)'}

### Target Elements
{chr(10).join(f'- {e}' for e in action_summary.target_elements) if action_summary.target_elements else '- (없음)'}

### Screen States
{chr(10).join(f'- {s}' for s in action_summary.screen_states) if action_summary.screen_states else '- (없음)'}
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"\n  Markdown 리포트 저장됨: {output_path}")
    return output_path


def main():
    """메인 함수"""
    # 기본 파일 경로
    default_path = "test_cases/sr-semantic-test-001_semantic.json"
    
    # 명령줄 인자로 파일 경로 받기
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = default_path
    
    if not Path(file_path).exists():
        print(f"[오류] 파일이 존재하지 않습니다: {file_path}")
        print(f"\n사용법: python {sys.argv[0]} [테스트케이스_경로]")
        return
    
    print("\n" + "=" * 70)
    print("  의미론적 테스트 케이스 뷰어")
    print("  BVT-Semantic Integration 검증 도구")
    print("=" * 70)
    
    # 1. 테스트 케이스 로드 및 기본 정보
    test_case = view_test_case(file_path)
    if not test_case:
        return
    
    # 2. semantic_info 상세 분석
    view_semantic_info(test_case)
    
    # 3. 액션 타임라인
    view_action_timeline(test_case)
    
    # 4. 요약 리포트 생성
    generate_summary_report(test_case)
    
    # 5. BVT 매칭 후보 탐색
    find_bvt_matches(test_case)
    
    # 6. Markdown 리포트 내보내기
    print_header("리포트 내보내기", "-")
    export_to_markdown(test_case)
    
    print("\n" + "=" * 70)
    print("  분석 완료!")
    print("=" * 70)


if __name__ == "__main__":
    main()
