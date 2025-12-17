#!/usr/bin/env python3
"""
Claude Code 세션을 활용한 직접 대화 생성 스크립트
API 키 없이 현재 세션에서 데이터 생성
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PROMPTS_DIR, SEEDS_DIR, RAW_DIR, LOGS_DIR

def load_template() -> str:
    """변형 프롬프트 템플릿 로드"""
    prompt_path = PROMPTS_DIR / "variation_prompt.txt"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_seeds(category: str) -> List[Dict]:
    """시드 파일들을 로드"""
    seeds = []

    category_map = {
        "adolescent": "청소년",
        "adult": "성인",
        "crisis": "위기대응"
    }

    cat_name = category_map.get(category, category)
    cat_dir = SEEDS_DIR / cat_name

    if not cat_dir.exists():
        print(f"경고: {cat_name} 카테고리 디렉토리가 없습니다.")
        return []

    for seed_file in cat_dir.rglob("*.json"):
        with open(seed_file, 'r', encoding='utf-8') as f:
            seed = json.load(f)
            seed["_source_file"] = str(seed_file)
            seed["category"] = category
            seeds.append(seed)

    return seeds

def get_next_index(category: str) -> int:
    """다음 파일 인덱스 확인"""
    category_dir = RAW_DIR / category
    if not category_dir.exists():
        return 0

    existing = list(category_dir.glob("*.json"))
    if not existing:
        return 0

    indices = []
    for f in existing:
        try:
            idx = int(f.stem.split('_')[-1])
            indices.append(idx)
        except:
            continue

    return max(indices) + 1 if indices else 0

def save_conversation(conversation: Dict, category: str, index: int) -> Path:
    """대화를 파일로 저장"""
    category_dir = RAW_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)

    filename = f"conv_{category}_{index:06d}.json"
    filepath = category_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(conversation, f, ensure_ascii=False, indent=2)

    return filepath

def create_prompt(seed: Dict, template: str) -> str:
    """시드로부터 프롬프트 생성"""
    category = seed.get("category", "adult")

    prompt = template.format(
        seed_scenario=json.dumps(seed, ensure_ascii=False, indent=2),
        category=category,
        min_turns=25,
        max_turns=35
    )

    return prompt

def main():
    import argparse

    parser = argparse.ArgumentParser(description="직접 대화 생성")
    parser.add_argument("--category", "-c", type=str, required=True,
                        choices=["adolescent", "adult", "crisis"])
    parser.add_argument("--count", "-n", type=int, default=10,
                        help="생성할 대화 수")
    parser.add_argument("--start-seed", type=int, default=0,
                        help="시작 시드 인덱스")

    args = parser.parse_args()

    # 시드 로드
    seeds = load_seeds(args.category)
    if not seeds:
        print(f"시드가 없습니다: {args.category}")
        return

    print(f"\n{'='*60}")
    print(f"카테고리: {args.category}")
    print(f"사용 가능한 시드: {len(seeds)}개")
    print(f"생성 목표: {args.count}개")
    print(f"{'='*60}\n")

    # 시작 인덱스
    start_index = get_next_index(args.category)
    print(f"시작 인덱스: {start_index}")

    # 템플릿 로드
    template = load_template()

    # 프롬프트 파일 생성 (Claude Code가 처리할 수 있도록)
    prompts_output = LOGS_DIR / f"prompts_{args.category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    with open(prompts_output, 'w', encoding='utf-8') as f:
        for i in range(args.count):
            seed_idx = (args.start_seed + i) % len(seeds)
            seed = seeds[seed_idx]

            f.write(f"\n{'='*60}\n")
            f.write(f"대화 #{i+1} (시드: {seed_idx}, 파일 인덱스: {start_index + i})\n")
            f.write(f"{'='*60}\n\n")
            f.write(create_prompt(seed, template))
            f.write(f"\n\n저장 경로: data/raw/{args.category}/conv_{args.category}_{start_index + i:06d}.json\n")
            f.write("\n" + "="*60 + "\n")

    print(f"\n✅ 프롬프트 파일 생성 완료: {prompts_output}")
    print(f"\n다음 단계:")
    print(f"1. 프롬프트를 읽어서 각각 처리")
    print(f"2. 결과를 JSON으로 저장")
    print(f"3. data/raw/{args.category}/ 디렉토리에 저장\n")

if __name__ == "__main__":
    main()
