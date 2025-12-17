#!/usr/bin/env python3
"""
시드 데이터 생성 스크립트
Claude Code CLI를 사용하여 카테고리별 상담 대화 데이터를 생성합니다.
"""

import json
import subprocess
import sys
import time
import uuid
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    DATASET_CONFIG, PROMPTS_DIR, SEEDS_DIR, LOGS_DIR,
    CLAUDE_CMD, MAX_RETRIES, RETRY_DELAY
)

# 카테고리별 설정
CATEGORY_CONFIG = {
    "청소년_학업스트레스": {
        "category": "adolescent",
        "sub_category": "학업스트레스",
        "description": "10대~20대 초반 청소년의 학업 관련 스트레스, 성적 압박, 시험 불안 등",
        "topics": [
            "성적 하락으로 인한 스트레스",
            "수능/입시 압박감",
            "부모님의 성적 기대 부담",
            "학원/과외 스케줄 과부하",
            "공부 집중력 저하",
            "시험 불안",
            "학습 동기 상실",
            "자퇴 고민"
        ],
        "count": 40
    },
    "청소년_또래관계": {
        "category": "adolescent",
        "sub_category": "또래관계",
        "description": "10대~20대 초반 청소년의 친구 관계, 왕따, 따돌림, 학교 폭력 등",
        "topics": [
            "친구와의 갈등",
            "왕따/따돌림 경험",
            "SNS 갈등",
            "친구 그룹에서 소외감",
            "학교 폭력 피해",
            "새 학교 적응 어려움",
            "질투심과 경쟁",
            "우정의 배신감"
        ],
        "count": 30
    },
    "청소년_가족갈등": {
        "category": "adolescent",
        "sub_category": "가족갈등",
        "description": "10대~20대 초반 청소년과 부모/가족 간의 갈등",
        "topics": [
            "부모님과의 소통 단절",
            "간섭과 통제에 대한 반발",
            "부모님 이혼/별거 스트레스",
            "형제자매 갈등",
            "가정폭력 경험",
            "부모님의 비교 발언"
        ],
        "count": 20
    },
    "청소년_진로고민": {
        "category": "adolescent",
        "sub_category": "진로고민",
        "description": "10대~20대 초반 청소년의 진로, 직업, 미래에 대한 고민",
        "topics": [
            "진로 결정 어려움",
            "꿈이 없는 불안",
            "부모님과 진로 갈등",
            "적성 찾기 고민",
            "취업 불안"
        ],
        "count": 10
    },
    "청소년_정체성": {
        "category": "adolescent",
        "sub_category": "정체성",
        "description": "10대~20대 초반 청소년의 자아정체성, 가치관, 외모 등에 대한 고민",
        "topics": [
            "자아정체성 혼란",
            "외모 콤플렉스",
            "성정체성 고민",
            "자존감 저하",
            "나만의 가치관 찾기"
        ],
        "count": 10
    },
    "성인_직장스트레스": {
        "category": "adult",
        "sub_category": "직장스트레스",
        "description": "20대 중반 이상 성인의 직장 내 스트레스, 번아웃, 업무 관련 어려움",
        "topics": [
            "업무 과부하와 번아웃",
            "직장 내 갈등",
            "상사와의 관계 어려움",
            "성과 압박 스트레스",
            "이직/퇴사 고민",
            "직장 내 괴롭힘",
            "워라밸 문제",
            "승진 누락 스트레스"
        ],
        "count": 30
    },
    "성인_대인관계": {
        "category": "adult",
        "sub_category": "대인관계",
        "description": "20대 중반 이상 성인의 대인관계, 연애, 결혼 관련 어려움",
        "topics": [
            "연인과의 갈등",
            "이별 후유증",
            "결혼 생활 문제",
            "친구 관계 어려움",
            "사회적 고립감",
            "대인기피",
            "신뢰 문제",
            "결혼/비혼 고민"
        ],
        "count": 24
    },
    "성인_우울불안": {
        "category": "adult",
        "sub_category": "우울불안",
        "description": "20대 중반 이상 성인의 우울감, 불안, 무기력 등 정서적 어려움",
        "topics": [
            "만성 우울감",
            "범불안",
            "무기력과 의욕 상실",
            "사회불안",
            "공황 증상",
            "수면 문제"
        ],
        "count": 16
    },
    "성인_가족관계": {
        "category": "adult",
        "sub_category": "가족관계",
        "description": "20대 중반 이상 성인의 원가족, 배우자 가족, 자녀 관계 어려움",
        "topics": [
            "부모님과의 갈등",
            "시댁/처가 스트레스",
            "육아 스트레스",
            "가족 간 소통 문제",
            "부모 돌봄 부담"
        ],
        "count": 10
    },
    "위기대응": {
        "category": "crisis",
        "sub_category": "위기대응",
        "description": "즉각적인 개입이 필요한 위기 상황 (자해, 자살 충동, 극심한 정서적 고통)",
        "topics": [
            "자해 충동",
            "극심한 우울감과 무망감",
            "공황 발작",
            "트라우마 플래시백",
            "급성 스트레스 반응"
        ],
        "count": 10
    }
}


def load_prompt_template() -> str:
    """프롬프트 템플릿 로드"""
    prompt_path = PROMPTS_DIR / "seed_prompt.txt"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def call_claude(prompt: str, retries: int = MAX_RETRIES) -> str:
    """Claude Code CLI 호출"""
    for attempt in range(retries):
        try:
            result = subprocess.run(
                [CLAUDE_CMD, "-p", prompt, "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=300  # 대화 생성은 시간이 더 걸림
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"\n오류 (시도 {attempt + 1}/{retries}): {result.stderr[:100]}")

        except subprocess.TimeoutExpired:
            print(f"\n타임아웃 (시도 {attempt + 1}/{retries})")
        except Exception as e:
            print(f"\n예외 발생 (시도 {attempt + 1}/{retries}): {e}")

        if attempt < retries - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))

    return ""


def extract_json(text: str) -> dict:
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


def generate_seed(
    template: str,
    category_key: str,
    config: dict,
    topic: str,
    index: int
) -> dict:
    """단일 시드 데이터 생성"""
    seed_id = f"{category_key}_{index:04d}_{uuid.uuid4().hex[:8]}"

    prompt = template.format(
        category=config["category"],
        category_description=config["description"],
        sub_category=config["sub_category"],
        topic=topic,
        min_turns=DATASET_CONFIG.min_turns,
        max_turns=DATASET_CONFIG.max_turns
    )

    response = call_claude(prompt)

    if not response:
        return {}

    seed_data = extract_json(response)

    if seed_data:
        # 메타데이터 보강
        seed_data["id"] = seed_id
        seed_data["category"] = config["category"]
        seed_data["sub_category"] = config["sub_category"]
        seed_data["category_key"] = category_key
        seed_data["topic"] = topic
        seed_data["generated_at"] = datetime.now().isoformat()

        # technique 라벨 검증
        if "conversation" in seed_data:
            techniques_used = set()
            for turn in seed_data["conversation"]:
                if turn.get("speaker") == "counselor":
                    techs = turn.get("technique", [])
                    if isinstance(techs, list):
                        techniques_used.update(techs)
            seed_data["techniques_used"] = list(techniques_used)

    return seed_data


def save_seed(seed: dict, category_key: str, index: int) -> Path:
    """시드를 파일로 저장"""
    # 카테고리별 디렉토리
    category_dir = SEEDS_DIR / category_key.replace("_", "/")
    category_dir.mkdir(parents=True, exist_ok=True)

    filename = f"seed_{index:04d}.json"
    filepath = category_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)

    return filepath


def validate_seed(seed: dict) -> tuple:
    """시드 데이터 유효성 검증"""
    issues = []

    # 대화 존재 확인
    if "conversation" not in seed:
        issues.append("대화 데이터 없음")
        return False, issues

    conv = seed["conversation"]

    # 턴 수 확인
    counselor_turns = len([t for t in conv if t.get("speaker") == "counselor"])
    if counselor_turns < DATASET_CONFIG.min_turns:
        issues.append(f"턴 수 부족: {counselor_turns}")

    if counselor_turns > DATASET_CONFIG.max_turns + 5:
        issues.append(f"턴 수 초과: {counselor_turns}")

    # technique 라벨 확인
    missing_technique = 0
    for turn in conv:
        if turn.get("speaker") == "counselor":
            if not turn.get("technique"):
                missing_technique += 1

    if missing_technique > 0:
        issues.append(f"technique 라벨 누락: {missing_technique}개")

    return len(issues) == 0, issues


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("시드 데이터 생성 시작")
    print("=" * 60)

    # 로그 디렉토리 생성
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    SEEDS_DIR.mkdir(parents=True, exist_ok=True)

    template = load_prompt_template()

    stats = {
        "total_target": sum(c["count"] for c in CATEGORY_CONFIG.values()),
        "total_generated": 0,
        "total_valid": 0,
        "total_invalid": 0,
        "by_category": {}
    }

    print(f"\n목표: 총 {stats['total_target']}개 시드 생성")
    print("\n카테고리별 분포:")
    for key, config in CATEGORY_CONFIG.items():
        print(f"  - {key}: {config['count']}개")

    print("\n" + "-" * 60)

    for category_key, config in CATEGORY_CONFIG.items():
        print(f"\n[{category_key}] {config['count']}개 생성 중...")

        stats["by_category"][category_key] = {
            "target": config["count"],
            "generated": 0,
            "valid": 0,
            "invalid": 0
        }

        topics = config["topics"]
        target_count = config["count"]

        # 주제별로 분배
        seeds_per_topic = target_count // len(topics)
        remainder = target_count % len(topics)

        current_index = 0

        with tqdm(total=target_count, desc=category_key[:20]) as pbar:
            for topic_idx, topic in enumerate(topics):
                count = seeds_per_topic + (1 if topic_idx < remainder else 0)

                for _ in range(count):
                    seed = generate_seed(
                        template=template,
                        category_key=category_key,
                        config=config,
                        topic=topic,
                        index=current_index
                    )

                    stats["total_generated"] += 1
                    stats["by_category"][category_key]["generated"] += 1

                    if seed:
                        is_valid, issues = validate_seed(seed)

                        if is_valid:
                            save_seed(seed, category_key, current_index)
                            stats["total_valid"] += 1
                            stats["by_category"][category_key]["valid"] += 1
                            current_index += 1
                        else:
                            # 유효하지 않아도 일단 저장 (검토용)
                            seed["validation_issues"] = issues
                            save_seed(seed, category_key, current_index)
                            stats["total_invalid"] += 1
                            stats["by_category"][category_key]["invalid"] += 1
                            current_index += 1
                    else:
                        stats["total_invalid"] += 1
                        stats["by_category"][category_key]["invalid"] += 1

                    pbar.update(1)

                    # API 부하 방지
                    time.sleep(1)

    # 결과 요약
    print("\n" + "=" * 60)
    print("시드 생성 완료")
    print("=" * 60)
    print(f"\n총 목표: {stats['total_target']}")
    print(f"총 생성: {stats['total_generated']}")
    print(f"유효: {stats['total_valid']}")
    print(f"무효/오류: {stats['total_invalid']}")

    print("\n카테고리별 결과:")
    for cat_key, cat_stats in stats["by_category"].items():
        print(f"  [{cat_key}]")
        print(f"    목표: {cat_stats['target']}, 유효: {cat_stats['valid']}, 무효: {cat_stats['invalid']}")

    # 통계 저장
    stats_file = LOGS_DIR / f"seed_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n통계 저장: {stats_file}")
    print(f"시드 저장 위치: {SEEDS_DIR}")


if __name__ == "__main__":
    main()
