#!/usr/bin/env python3
"""
배치 대화 생성 스크립트
시드 시나리오를 기반으로 멀티턴 상담 대화를 생성합니다.
"""

import json
import subprocess
import sys
import time
import random
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import argparse

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    DATASET_CONFIG, CATEGORY_CONFIG, PROMPTS_DIR, SEEDS_DIR, RAW_DIR, LOGS_DIR,
    CLAUDE_CMD, MAX_RETRIES, RETRY_DELAY
)


class ConversationGenerator:
    """대화 생성기 클래스"""

    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.template = self._load_template()
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "by_category": {}
        }

    def _load_template(self) -> str:
        """변형 프롬프트 템플릿 로드"""
        prompt_path = PROMPTS_DIR / "variation_prompt.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_seeds(self, category: Optional[str] = None) -> List[Dict]:
        """시드 파일들을 로드"""
        seeds = []

        if category:
            categories = [category]
        else:
            categories = ["adolescent", "adult", "crisis"]

        for cat in categories:
            cat_dir = SEEDS_DIR / cat
            if not cat_dir.exists():
                print(f"경고: {cat} 카테고리 디렉토리가 없습니다.")
                continue

            for seed_file in cat_dir.glob("*.json"):
                with open(seed_file, 'r', encoding='utf-8') as f:
                    seed = json.load(f)
                    seed["_source_file"] = str(seed_file)
                    seeds.append(seed)

        return seeds

    def call_claude(self, prompt: str) -> str:
        """Claude Code CLI 호출"""
        for attempt in range(MAX_RETRIES):
            try:
                result = subprocess.run(
                    [CLAUDE_CMD, "-p", prompt, "--output-format", "text"],
                    capture_output=True,
                    text=True,
                    timeout=180  # 대화 생성은 더 오래 걸릴 수 있음
                )

                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    print(f"오류 (시도 {attempt + 1}): {result.stderr[:100]}")

            except subprocess.TimeoutExpired:
                print(f"타임아웃 (시도 {attempt + 1})")
            except Exception as e:
                print(f"예외 (시도 {attempt + 1}): {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

        return ""

    def extract_json(self, text: str) -> dict:
        """텍스트에서 JSON 추출"""
        try:
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                text = text[start:end].strip()

            return json.loads(text)
        except json.JSONDecodeError:
            try:
                return json.loads(text)
            except:
                return {}

    def generate_conversation(self, seed: Dict) -> Optional[Dict]:
        """시드로부터 대화 생성"""
        category = seed.get("category", "adult")
        topic = seed.get("topic", "")

        # 턴 수 무작위 결정
        min_turns = DATASET_CONFIG.min_turns
        max_turns = DATASET_CONFIG.max_turns

        prompt = self.template.format(
            seed_scenario=json.dumps(seed, ensure_ascii=False, indent=2),
            category=category,
            min_turns=min_turns,
            max_turns=max_turns
        )

        response = self.call_claude(prompt)

        if not response:
            return None

        conversation = self.extract_json(response)

        if conversation and "conversation" in conversation:
            conversation["seed_info"] = {
                "source_file": seed.get("_source_file", ""),
                "category": category,
                "topic": topic
            }
            conversation["generated_at"] = datetime.now().isoformat()
            return conversation

        return None

    def save_conversation(self, conversation: Dict, category: str, index: int) -> Path:
        """대화를 파일로 저장"""
        category_dir = RAW_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        filename = f"conv_{category}_{index:06d}.json"
        filepath = category_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation, f, ensure_ascii=False, indent=2)

        return filepath

    def generate_for_category(self, category: str, target_count: int, start_index: int = 0) -> int:
        """특정 카테고리에 대해 대화 생성"""
        seeds = self.load_seeds(category)

        if not seeds:
            print(f"경고: {category} 카테고리에 시드가 없습니다.")
            return 0

        generated = 0
        current_index = start_index

        print(f"\n[{category}] {target_count}개 대화 생성 중...")
        print(f"  - 사용 가능한 시드: {len(seeds)}개")

        with tqdm(total=target_count, desc=f"{category}") as pbar:
            while generated < target_count:
                # 시드 순환 선택
                seed = seeds[generated % len(seeds)]

                conversation = self.generate_conversation(seed)

                if conversation:
                    self.save_conversation(conversation, category, current_index)
                    generated += 1
                    current_index += 1
                    self.stats["success"] += 1
                    pbar.update(1)
                else:
                    self.stats["failed"] += 1

                self.stats["total"] += 1

                # API 부하 방지
                time.sleep(1)

        return generated

    def generate_batch(self, batch_size: Optional[int] = None):
        """전체 배치 생성"""
        if batch_size is None:
            targets = DATASET_CONFIG.category_targets
        else:
            # 비율에 맞게 배치 크기 분배
            targets = {
                cat: int(batch_size * ratio)
                for cat, ratio in DATASET_CONFIG.category_ratios.items()
            }

        print("=" * 60)
        print("대화 배치 생성 시작")
        print("=" * 60)
        print("\n목표:")
        for cat, count in targets.items():
            print(f"  - {cat}: {count}개")

        for category, target in targets.items():
            self.stats["by_category"][category] = {"target": target, "generated": 0}
            generated = self.generate_for_category(category, target)
            self.stats["by_category"][category]["generated"] = generated

        self._print_summary()

    def _print_summary(self):
        """결과 요약 출력"""
        print("\n" + "=" * 60)
        print("배치 생성 완료")
        print("=" * 60)
        print(f"총 시도: {self.stats['total']}")
        print(f"성공: {self.stats['success']}")
        print(f"실패: {self.stats['failed']}")
        print("\n카테고리별 결과:")
        for cat, cat_stats in self.stats["by_category"].items():
            print(f"  - {cat}: {cat_stats['generated']}/{cat_stats['target']}")

        # 통계 저장
        stats_file = LOGS_DIR / f"batch_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

        print(f"\n통계 저장: {stats_file}")


def count_existing_conversations() -> Dict[str, int]:
    """기존 생성된 대화 수 확인"""
    counts = {}
    for category in ["adolescent", "adult", "crisis"]:
        cat_dir = RAW_DIR / category
        if cat_dir.exists():
            counts[category] = len(list(cat_dir.glob("*.json")))
        else:
            counts[category] = 0
    return counts


def main():
    parser = argparse.ArgumentParser(description="상담 대화 배치 생성")
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=None,
        help="생성할 총 대화 수 (기본값: 전체 목표)"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        choices=["adolescent", "adult", "crisis"],
        default=None,
        help="특정 카테고리만 생성"
    )
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="기존 진행 상태에서 재개"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=3,
        help="병렬 워커 수"
    )

    args = parser.parse_args()

    generator = ConversationGenerator(max_workers=args.workers)

    if args.resume:
        existing = count_existing_conversations()
        print("기존 생성 현황:")
        for cat, count in existing.items():
            print(f"  - {cat}: {count}개")

    if args.category:
        if args.batch_size:
            target = args.batch_size
        else:
            target = DATASET_CONFIG.category_targets[args.category]

        existing_count = count_existing_conversations().get(args.category, 0) if args.resume else 0
        remaining = target - existing_count

        if remaining > 0:
            generator.generate_for_category(
                args.category,
                remaining,
                start_index=existing_count
            )
        else:
            print(f"{args.category} 카테고리는 이미 목표 달성")
    else:
        generator.generate_batch(args.batch_size)


if __name__ == "__main__":
    main()
