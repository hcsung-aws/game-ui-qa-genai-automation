"""
BVT-Semantic Integration 전체 데모 스크립트

Task 1~9에서 구현된 모든 계층을 실제 데이터로 검증한다.

실행 방법:
    python demo_bvt_full_integration.py

결과물:
    - reports/demo_matching_report.json  (JSON 형식 매칭 리포트)
    - reports/demo_matching_report.md    (Markdown 형식 매칭 리포트)
    - reports/demo_updated_bvt.csv       (업데이트된 BVT 파일)
"""

import json
import os
from pathlib import Path
from datetime import datetime

# 모듈 임포트
from src.bvt_integration.bvt_parser import BVTParser
from src.bvt_integration.tc_loader import SemanticTestCaseLoader
from src.bvt_integration.summary_generator import SemanticSummaryGenerator
from src.bvt_integration.text_similarity import TextSimilarityCalculator
from src.bvt_integration.matching_analyzer import MatchingAnalyzer
from src.bvt_integration.auto_play_generator import AutoPlayGenerator
from src.bvt_integration.bvt_updater import BVTUpdater
from src.bvt_integration.report_generator import ReportGenerator
from src.bvt_integration.models import PlayTestResult, TestStatus


def get_bvt_path():
    """BVT 파일 경로 반환"""
    # 실제 BVT 파일 찾기
    for path in Path("bvt_samples").glob("BVT_*.csv"):
        if "example" not in path.name.lower():
            return str(path)
    
    # 예제 파일 사용
    example_path = "bvt_samples/BVT_example.csv"
    if Path(example_path).exists():
        return example_path
    
    return None


def print_section(title):
    """섹션 헤더 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_step1_parsing():
    """Step 1: BVT 파싱"""
    print_section("Step 1: BVT CSV 파싱")
    
    parser = BVTParser()
    bvt_path = get_bvt_path()
    
    if not bvt_path:
        print("  [오류] BVT 파일을 찾을 수 없습니다.")
        return []
    
    print(f"  파일: {bvt_path}")
    bvt_cases = parser.parse(bvt_path)
    print(f"  파싱된 케이스 수: {len(bvt_cases)}")
    
    # 샘플 출력
    print("\n  샘플 BVT 케이스 (처음 3개):")
    for case in bvt_cases[:3]:
        category = " > ".join(filter(None, [case.category1, case.category2, case.category3]))
        print(f"    [{case.no}] {category}")
        check_preview = case.check[:60] + "..." if len(case.check) > 60 else case.check
        print(f"        Check: {check_preview}")
    
    return bvt_cases


def demo_step2_loading():
    """Step 2: 테스트 케이스 로딩"""
    print_section("Step 2: 테스트 케이스 로딩")
    
    loader = SemanticTestCaseLoader()
    tc_dir = "test_cases"
    
    if not Path(tc_dir).exists():
        print(f"  [오류] 디렉토리가 없습니다: {tc_dir}")
        return []
    
    test_cases = loader.load_directory(tc_dir)
    print(f"  로드된 테스트 케이스 수: {len(test_cases)}")
    
    for tc in test_cases:
        print(f"    - {tc.name}: {len(tc.actions)}개 액션")
    
    return test_cases


def demo_step3_summary(test_cases):
    """Step 3: 요약 문서 생성"""
    print_section("Step 3: Semantic Summary 생성")
    
    if not test_cases:
        print("  [경고] 테스트 케이스가 없습니다.")
        return None
    
    generator = SemanticSummaryGenerator()
    summary = generator.generate(test_cases)
    
    print(f"  총 테스트 케이스: {summary.total_test_cases}")
    print(f"  총 액션 수: {summary.total_actions}")
    
    print("\n  테스트 케이스별 요약:")
    for action_summary in summary.test_case_summaries:
        print(f"    [{action_summary.test_case_name}]")
        print(f"      - 액션 수: {action_summary.action_count}")
        if action_summary.intents:
            print(f"      - Intents: {len(action_summary.intents)}개")
        if action_summary.action_descriptions:
            print(f"      - 첫 액션: {action_summary.action_descriptions[0][:50]}...")
    
    return summary


def demo_step4_matching(bvt_cases, summary):
    """Step 4: 매칭 분석"""
    print_section("Step 4: BVT-테스트케이스 매칭 분석")
    
    if not bvt_cases or not summary:
        print("  [경고] BVT 케이스 또는 요약이 없습니다.")
        return []
    
    similarity_calc = TextSimilarityCalculator()
    analyzer = MatchingAnalyzer(similarity_calc)
    
    match_results = analyzer.analyze(bvt_cases, summary)
    
    # 통계
    high_conf = [r for r in match_results if r.is_high_confidence]
    low_conf = [r for r in match_results if r.is_matched and not r.is_high_confidence]
    unmatched = [r for r in match_results if not r.is_matched]
    
    print(f"  총 BVT 항목: {len(match_results)}")
    print(f"  고신뢰도 매칭: {len(high_conf)}")
    print(f"  저신뢰도 매칭: {len(low_conf)}")
    print(f"  미매칭: {len(unmatched)}")
    
    # 고신뢰도 매칭 상세
    if high_conf:
        print("\n  고신뢰도 매칭 상세:")
        for result in high_conf[:5]:
            print(f"    BVT #{result.bvt_case.no}: {result.bvt_case.check[:40]}...")
            print(f"      -> {result.matched_test_case} (신뢰도: {result.confidence_score:.2f})")
            if result.action_range:
                print(f"      -> 액션 범위: {result.action_range.start_index}-{result.action_range.end_index}")
    
    return match_results


def demo_step5_play_test_generation(match_results, test_cases):
    """Step 5: 플레이 테스트 생성"""
    print_section("Step 5: 플레이 테스트 케이스 생성")
    
    high_conf_results = [r for r in match_results if r.is_high_confidence]
    
    if not high_conf_results:
        print("  [정보] 고신뢰도 매칭이 없어 플레이 테스트를 생성하지 않습니다.")
        return []
    
    generator = AutoPlayGenerator(screenshot_dir="screenshots/demo")
    
    # 테스트 케이스 캐시
    for tc in test_cases:
        generator.cache_test_case(tc)
    
    play_tests = []
    print(f"  생성할 플레이 테스트: {len(high_conf_results)}개")
    
    for result in high_conf_results[:3]:  # 처음 3개만 생성
        play_test = generator.generate(result)
        if play_test:
            play_tests.append(play_test)
            print(f"    - {play_test.name}")
            print(f"      BVT #{play_test.bvt_reference.no}: {play_test.bvt_reference.check[:40]}...")
            print(f"      액션 수: {len(play_test.actions)}")
    
    return play_tests


def demo_step6_report_generation(match_results):
    """Step 6: 리포트 생성"""
    print_section("Step 6: 매칭 리포트 생성")
    
    if not match_results:
        print("  [경고] 매칭 결과가 없습니다.")
        return None
    
    generator = ReportGenerator()
    report = generator.generate(match_results)
    
    print(f"  총 BVT 항목: {report.total_bvt_items}")
    print(f"  매칭된 항목: {report.matched_items}")
    print(f"  미매칭 항목: {report.unmatched_items}")
    print(f"  커버리지: {report.coverage_percentage:.1f}%")
    
    # 파일 저장
    os.makedirs("reports", exist_ok=True)
    
    # JSON 리포트
    json_path = "reports/demo_matching_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(generator.to_json(report))
    print(f"\n  JSON 리포트 저장: {json_path}")
    
    # Markdown 리포트
    md_path = "reports/demo_matching_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(generator.to_markdown(report))
    print(f"  Markdown 리포트 저장: {md_path}")
    
    return report


def demo_step7_bvt_update(bvt_cases, match_results):
    """Step 7: BVT 업데이트 (시뮬레이션)"""
    print_section("Step 7: BVT 업데이트 (시뮬레이션)")
    
    if not bvt_cases:
        print("  [경고] BVT 케이스가 없습니다.")
        return
    
    updater = BVTUpdater()
    
    # 시뮬레이션된 테스트 결과 생성
    # 고신뢰도 매칭은 PASS, 저신뢰도는 FAIL로 시뮬레이션
    simulated_results = []
    for result in match_results:
        if result.is_high_confidence:
            simulated_results.append(PlayTestResult(
                play_test_name=f"play_test_{result.bvt_case.no}",
                bvt_no=result.bvt_case.no,
                status=TestStatus.PASS,
                executed_actions=5,
                failed_actions=0,
                screenshots=[],
                error_message=None,
                execution_time=1.0
            ))
        elif result.is_matched:
            simulated_results.append(PlayTestResult(
                play_test_name=f"play_test_{result.bvt_case.no}",
                bvt_no=result.bvt_case.no,
                status=TestStatus.FAIL,
                executed_actions=5,
                failed_actions=2,
                screenshots=[],
                error_message="Low confidence match - manual verification needed",
                execution_time=1.5
            ))
    
    print(f"  시뮬레이션된 테스트 결과: {len(simulated_results)}개")
    
    # BVT 업데이트
    updated_cases = updater.update(bvt_cases, simulated_results)
    
    # 결과 통계
    pass_count = sum(1 for c in updated_cases if c.test_result == "PASS")
    fail_count = sum(1 for c in updated_cases if c.test_result == "Fail")
    not_tested = sum(1 for c in updated_cases if c.test_result == "Not Tested")
    
    print(f"  업데이트 결과:")
    print(f"    - PASS: {pass_count}")
    print(f"    - Fail: {fail_count}")
    print(f"    - Not Tested: {not_tested}")
    
    # 파일 저장
    output_path = updater.save(updated_cases, "reports")
    print(f"\n  업데이트된 BVT 저장: {output_path}")
    
    return updated_cases


def demo_text_similarity():
    """텍스트 유사도 계산 데모"""
    print_section("보너스: 텍스트 유사도 계산 예시")
    
    calc = TextSimilarityCalculator()
    
    test_pairs = [
        ("최초 접속 시 메인 로비로 노출", "메인 로비 화면 진입"),
        ("상점 버튼 터치 시 메뉴 이동", "상점 메뉴 입장 확인"),
        ("프로필 아이콘 노출", "설정 메뉴 열기"),
        ("채팅 기능 동작 확인", "채팅 UI 노출"),
    ]
    
    print("  텍스트 쌍별 유사도:")
    for text1, text2 in test_pairs:
        score = calc.calculate(text1, text2)
        print(f"    '{text1[:20]}...' vs '{text2[:20]}...'")
        print(f"      -> 유사도: {score:.3f}")


def main():
    """메인 함수"""
    print("\n" + "=" * 70)
    print("  BVT-Semantic Integration 전체 데모")
    print("  Task 1~9 구현 검증")
    print("=" * 70)
    print(f"  실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: BVT 파싱
    bvt_cases = demo_step1_parsing()
    
    # Step 2: 테스트 케이스 로딩
    test_cases = demo_step2_loading()
    
    # Step 3: 요약 생성
    summary = demo_step3_summary(test_cases)
    
    # Step 4: 매칭 분석
    match_results = demo_step4_matching(bvt_cases, summary)
    
    # Step 5: 플레이 테스트 생성
    play_tests = demo_step5_play_test_generation(match_results, test_cases)
    
    # Step 6: 리포트 생성
    report = demo_step6_report_generation(match_results)
    
    # Step 7: BVT 업데이트
    updated_cases = demo_step7_bvt_update(bvt_cases, match_results)
    
    # 보너스: 텍스트 유사도
    demo_text_similarity()
    
    # 최종 요약
    print_section("최종 요약")
    print(f"  BVT 케이스: {len(bvt_cases)}개 파싱")
    print(f"  테스트 케이스: {len(test_cases)}개 로드")
    if summary:
        print(f"  총 액션: {summary.total_actions}개")
    print(f"  매칭 결과: {len(match_results)}개")
    if report:
        print(f"  커버리지: {report.coverage_percentage:.1f}%")
    
    print("\n  생성된 파일:")
    print("    - reports/demo_matching_report.json")
    print("    - reports/demo_matching_report.md")
    print("    - reports/BVT_updated_*.csv")
    
    print("\n" + "=" * 70)
    print("  데모 완료!")
    print("=" * 70)


if __name__ == "__main__":
    main()
