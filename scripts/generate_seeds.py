#!/usr/bin/env python3
"""
시드 시나리오 생성 스크립트
Claude Code CLI를 사용하여 각 카테고리별 시드 시나리오를 생성합니다.
"""

import json
import subprocess
import sys
import time
import random
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    DATASET_CONFIG, CATEGORY_CONFIG, PROMPTS_DIR, SEEDS_DIR, LOGS_DIR,
    CLAUDE_CMD, MAX_RETRIES, RETRY_DELAY
)


def load_prompt_template() -> str:
    """시드 프롬프트 템플릿 로드"""
    prompt_path = PROMPTS_DIR / "seed_prompt.txt"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_topics_for_category(category: str) -> list:
    """카테고리별 주제 목록 반환"""
    topic_map = {
        "adolescent": CATEGORY_CONFIG.adolescent_topics,
        "adult": CATEGORY_CONFIG.adult_topics,
        "crisis": CATEGORY_CONFIG.crisis_topics
    }
    return topic_map.get(category, [])


def call_claude(prompt: str, retries: int = MAX_RETRIES) -> str:
    """
    Claude Code CLI를 호출하여 응답을 받습니다.

    Args:
        prompt: 전송할 프롬프트
        retries: 재시도 횟수

    Returns:
        Claude의 응답 텍스트
    """
    for attempt in range(retries):
        try:
            result = subprocess.run(
                [CLAUDE_CMD, "-p", prompt, "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"오류 (시도 {attempt + 1}/{retries}): {result.stderr}")

        except subprocess.TimeoutExpired:
            print(f"타임아웃 (시도 {attempt + 1}/{retries})")
        except Exception as e:
            print(f"예외 발생 (시도 {attempt + 1}/{retries}): {e}")

        if attempt < retries - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))

    return ""


def extract_json(text: str) -> dict:
    """텍스트에서 JSON 추출"""
    try:
        # JSON 블록 찾기
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
        # 직접 파싱 시도
        try:
            return json.loads(text)
        except:
            return {}


def generate_seed(category: str, topic: str, template: str) -> dict:
    """단일 시드 시나리오 생성"""
    prompt = template.format(category=category, topic=topic)
    response = call_claude(prompt)

    if not response:
        return {}

    seed_data = extract_json(response)

    if seed_data:
        seed_data["category"] = category
        seed_data["topic"] = topic
        seed_data["generated_at"] = datetime.now().isoformat()

    return seed_data


def save_seed(seed: dict, category: str, index: int):
    """시드를 파일로 저장"""
    category_dir = SEEDS_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)

    filename = f"seed_{category}_{index:04d}.json"
    filepath = category_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)

    return filepath


def setup_logging():
    """로깅 설정"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"seed_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    return log_file


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("시드 시나리오 생성 시작")
    print("=" * 60)

    log_file = setup_logging()
    template = load_prompt_template()

    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "by_category": {}
    }

    categories = ["adolescent", "adult", "crisis"]

    for category in categories:
        print(f"\n[{category}] 카테고리 시드 생성 중...")
        topics = get_topics_for_category(category)
        seeds_per_category = DATASET_CONFIG.seeds_per_category

        stats["by_category"][category] = {"success": 0, "failed": 0}

        # 각 주제별로 시드 생성
        seeds_per_topic = seeds_per_category // len(topics)
        remainder = seeds_per_category % len(topics)

        seed_index = 0

        for topic_idx, topic in enumerate(tqdm(topics, desc=f"{category}")):
            # 마지막 주제에 나머지 할당
            count = seeds_per_topic + (1 if topic_idx < remainder else 0)

            for _ in range(count):
                stats["total"] += 1

                seed = generate_seed(category, topic, template)

                if seed:
                    save_seed(seed, category, seed_index)
                    stats["success"] += 1
                    stats["by_category"][category]["success"] += 1
                    seed_index += 1
                else:
                    stats["failed"] += 1
                    stats["by_category"][category]["failed"] += 1

                # API 부하 방지
                time.sleep(0.5)

    # 결과 요약
    print("\n" + "=" * 60)
    print("시드 생성 완료")
    print("=" * 60)
    print(f"총 시도: {stats['total']}")
    print(f"성공: {stats['success']}")
    print(f"실패: {stats['failed']}")
    print("\n카테고리별 결과:")
    for cat, cat_stats in stats["by_category"].items():
        print(f"  - {cat}: 성공 {cat_stats['success']}, 실패 {cat_stats['failed']}")

    # 통계 저장
    stats_file = LOGS_DIR / f"seed_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n통계 저장: {stats_file}")


if __name__ == "__main__":
    main()
