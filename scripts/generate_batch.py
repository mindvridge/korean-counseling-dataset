#!/usr/bin/env python3
"""
배치 대화 생성 스크립트 (AIML API 사용)
시드 시나리오를 기반으로 멀티턴 상담 대화를 생성합니다.
"""

import json
import os
import sys
import time
import random
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional
from tqdm import tqdm
import argparse

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    DATASET_CONFIG, CATEGORY_CONFIG, PROMPTS_DIR, SEEDS_DIR, RAW_DIR, LOGS_DIR,
    MAX_RETRIES, RETRY_DELAY
)


class AIMLConversationGenerator:
    """AIML API를 사용한 대화 생성기"""

    def __init__(self, batch_size: int = 100, checkpoint_interval: int = 1000):
        self.batch_size = batch_size
        self.checkpoint_interval = checkpoint_interval
        self.template = self._load_template()

        # AIML API 설정
        self.api_key = os.environ.get("AIMLAPI_API_KEY")
        if not self.api_key:
            raise ValueError("AIMLAPI_API_KEY 환경변수가 설정되지 않았습니다.")

        self.api_base = "https://api.aimlapi.com/v1"
        self.model = "claude-sonnet-4-5"

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

        # 카테고리 매핑 (영어 -> 한국어)
        category_map = {
            "adolescent": "청소년",
            "adult": "성인",
            "crisis": "위기대응"
        }

        if category:
            categories = [category_map.get(category, category)]
        else:
            categories = ["청소년", "성인", "위기대응"]

        for cat in categories:
            cat_dir = SEEDS_DIR / cat
            if not cat_dir.exists():
                print(f"경고: {cat} 카테고리 디렉토리가 없습니다.")
                continue

            # 하위 디렉토리 재귀 탐색
            for seed_file in cat_dir.rglob("*.json"):
                with open(seed_file, 'r', encoding='utf-8') as f:
                    seed = json.load(f)
                    seed["_source_file"] = str(seed_file)
                    seed["category"] = list(category_map.keys())[list(category_map.values()).index(cat)]
                    seeds.append(seed)

        return seeds

    def call_aiml_api(self, prompt: str) -> str:
        """AIML API 호출 (OpenAI 호환 형식)"""
        for attempt in range(MAX_RETRIES):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 8192,
                    "temperature": 0.7
                }

                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120
                )

                response.raise_for_status()
                result = response.json()

                return result['choices'][0]['message']['content']

            except requests.exceptions.RequestException as e:
                print(f"API 오류 (시도 {attempt + 1}/{MAX_RETRIES}): {str(e)[:200]}")

                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    print(f"  {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"  최대 재시도 횟수 초과. 실패.")
                    raise

        return None

    def generate_conversation(self, seed: Dict) -> Optional[Dict]:
        """시드로부터 대화 생성"""
        try:
            # 프롬프트 생성
            prompt = self.template.replace("{{SEED_DATA}}", json.dumps(seed, ensure_ascii=False, indent=2))

            # API 호출
            response = self.call_aiml_api(prompt)

            if not response:
                return None

            # JSON 파싱
            # 마크다운 코드 블록 제거
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            conversation = json.loads(response)

            # 메타데이터 추가
            conversation["seed_info"] = {
                "source_file": seed.get("_source_file", "unknown"),
                "category": seed.get("category", "unknown"),
                "topic": seed.get("topic", "unknown")
            }
            conversation["generated_at"] = datetime.now(timezone.utc).isoformat()

            return conversation

        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {str(e)[:100]}")
            print(f"응답 시작: {response[:200] if response else 'None'}")
            return None
        except Exception as e:
            print(f"대화 생성 오류: {str(e)[:100]}")
            return None

    def save_conversation(self, conversation: Dict, category: str, index: int):
        """대화를 JSON 파일로 저장"""
        output_dir = RAW_DIR / category
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"conv_{category}_{index:06d}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conversation, f, ensure_ascii=False, indent=2)

    def _save_checkpoint(self, category: str, count: int, current_index: int):
        """체크포인트 저장"""
        checkpoint = {
            "category": category,
            "count": count,
            "current_index": current_index,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        checkpoint_file = LOGS_DIR / f"checkpoint_{category}_{count}.json"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 체크포인트 저장: {checkpoint_file.name}")

    def generate_for_category(self, category: str, target_count: int, start_index: int = 0):
        """특정 카테고리의 대화 생성"""
        print(f"\n{'='*70}")
        print(f"📝 카테고리: {category}")
        print(f"🎯 목표: {target_count}개 (시작 인덱스: {start_index})")
        print(f"{'='*70}\n")

        # 시드 로드
        seeds = self.load_seeds(category)
        if not seeds:
            print(f"❌ {category} 카테고리의 시드가 없습니다.")
            return

        print(f"📦 시드 파일 {len(seeds)}개 로드됨\n")

        generated = 0
        failed = 0
        current_index = start_index

        # 배치 단위로 생성
        num_batches = (target_count + self.batch_size - 1) // self.batch_size

        for batch_num in range(num_batches):
            batch_start = batch_num * self.batch_size
            batch_end = min(batch_start + self.batch_size, target_count)
            batch_size = batch_end - batch_start

            print(f"\n🔄 배치 {batch_num + 1}/{num_batches} ({batch_size}개)")

            for i in tqdm(range(batch_size), desc=f"  생성"):
                # 랜덤 시드 선택
                seed = random.choice(seeds)

                # 대화 생성
                conversation = self.generate_conversation(seed)

                if conversation:
                    self.save_conversation(conversation, category, current_index)
                    generated += 1
                    self.stats["success"] += 1
                else:
                    failed += 1
                    self.stats["failed"] += 1

                current_index += 1
                self.stats["total"] += 1

                # Rate limiting (1.2초 간격)
                time.sleep(1.2)

                # 체크포인트 저장
                if generated > 0 and generated % self.checkpoint_interval == 0:
                    self._save_checkpoint(category, generated, current_index)
                    print(f"\n  📊 진행: {generated}/{target_count} ({generated/target_count*100:.1f}%)")

        # 최종 통계
        print(f"\n{'='*70}")
        print(f"✅ {category} 완료!")
        print(f"  - 성공: {generated}개")
        print(f"  - 실패: {failed}개")
        print(f"  - 총계: {generated + failed}개")
        print(f"{'='*70}")

    def generate_all(self, total_count: int = 9800):
        """모든 카테고리의 대화 생성"""
        print(f"\n{'='*70}")
        print(f"🚀 한국어 심리상담 데이터셋 생성 시작")
        print(f"{'='*70}")
        print(f"📊 총 목표: {total_count:,}개")
        print(f"🤖 모델: {self.model}")
        print(f"📦 배치 크기: {self.batch_size}개")
        print(f"💾 체크포인트 간격: {self.checkpoint_interval}개")
        print(f"⏱️  Rate limit: 1.2초 간격")
        print(f"{'='*70}\n")

        # 카테고리별 목표 개수 계산
        category_targets = {
            "adolescent": int(total_count * 0.55),  # 5,390개
            "adult": int(total_count * 0.40),       # 3,920개
            "crisis": int(total_count * 0.05)       # 490개
        }

        # 기존 파일 확인
        existing_counts = {}
        for category in ["adolescent", "adult", "crisis"]:
            cat_dir = RAW_DIR / category
            if cat_dir.exists():
                existing_counts[category] = len(list(cat_dir.glob("conv_*.json")))
            else:
                existing_counts[category] = 0

        print("📁 기존 파일 개수:")
        for cat, count in existing_counts.items():
            target = category_targets[cat]
            remaining = target - count
            print(f"  - {cat}: {count}개 (목표: {target}개, 남은 개수: {remaining}개)")

        # 각 카테고리 생성
        for category, target in category_targets.items():
            existing = existing_counts[category]

            if existing >= target:
                print(f"\n✅ {category}: 이미 목표 달성 ({existing}/{target})")
                continue

            remaining = target - existing
            self.generate_for_category(category, remaining, start_index=existing)

        # 최종 통계
        print(f"\n{'='*70}")
        print(f"🎉 전체 생성 완료!")
        print(f"{'='*70}")
        print(f"📊 최종 통계:")
        print(f"  - 총 생성: {self.stats['total']}개")
        print(f"  - 성공: {self.stats['success']}개")
        print(f"  - 실패: {self.stats['failed']}개")
        print(f"  - 성공률: {self.stats['success']/self.stats['total']*100:.1f}%")
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="AIML API를 사용한 심리상담 대화 생성")
    parser.add_argument("--batch-size", type=int, default=100, help="배치 크기 (기본: 100)")
    parser.add_argument("--checkpoint", type=int, default=1000, help="체크포인트 간격 (기본: 1000)")
    parser.add_argument("--total", type=int, default=9800, help="총 생성 개수 (기본: 9800)")

    args = parser.parse_args()

    # API 키 확인
    if not os.environ.get("AIMLAPI_API_KEY"):
        print("❌ 오류: AIMLAPI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("  export AIMLAPI_API_KEY='your-api-key-here'")
        sys.exit(1)

    # 생성기 생성 및 실행
    generator = AIMLConversationGenerator(
        batch_size=args.batch_size,
        checkpoint_interval=args.checkpoint
    )

    try:
        generator.generate_all(total_count=args.total)
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        print(f"현재까지 생성: {generator.stats['success']}개")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
