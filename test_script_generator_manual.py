"""
ScriptGenerator 수동 테스트

생성된 스크립트가 올바르게 동작하는지 확인
"""

from datetime import datetime
from src.config_manager import ConfigManager
from src.input_monitor import Action
from src.script_generator import ScriptGenerator


def main():
    print("=== ScriptGenerator 수동 테스트 ===\n")
    
    # ConfigManager 생성
    config = ConfigManager()
    if not config.config:
        config.create_default_config()
    
    # ScriptGenerator 생성
    generator = ScriptGenerator(config)
    
    # 테스트 액션 생성
    test_actions = [
        Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=640,
            y=400,
            description='게임 시작 버튼 클릭',
            button='left'
        ),
        Action(
            timestamp=datetime.now().isoformat(),
            action_type='wait',
            x=0,
            y=0,
            description='2.0초 대기'
        ),
        Action(
            timestamp=datetime.now().isoformat(),
            action_type='key_press',
            x=0,
            y=0,
            description='플레이어 이름 입력',
            key='TestPlayer'
        ),
        Action(
            timestamp=datetime.now().isoformat(),
            action_type='wait',
            x=0,
            y=0,
            description='1.5초 대기'
        ),
        Action(
            timestamp=datetime.now().isoformat(),
            action_type='click',
            x=800,
            y=500,
            description='확인 버튼 클릭',
            button='left'
        ),
    ]
    
    # 스크립트 생성
    output_path = 'test_cases/test_replay_manual.py'
    print(f"스크립트 생성 중: {output_path}")
    generator.generate_replay_script(test_actions, output_path)
    print(f"✓ 스크립트 생성 완료\n")
    
    # 생성된 스크립트 내용 일부 출력
    print("=== 생성된 스크립트 내용 (일부) ===")
    with open(output_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # 처음 30줄만 출력
        for i, line in enumerate(lines[:30], 1):
            print(f"{i:3d}: {line}", end='')
    
    print("\n...")
    print(f"\n전체 내용은 {output_path} 파일을 확인하세요.")
    print("\n=== 테스트 완료 ===")


if __name__ == '__main__':
    main()
