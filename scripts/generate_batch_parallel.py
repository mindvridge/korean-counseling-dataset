#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
병렬 대화 생성 스크립트 (AIML API 사용)
ThreadPoolExecutor로 여러 대화를 동시에 생성하여 속도 향상
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
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Windows 환경에서 UTF-8 인코딩 강제 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    DATASET_CONFIG, CATEGORY_CONFIG, PROMPTS_DIR, SEEDS_DIR, RAW_DIR, LOGS_DIR,
    MAX_RETRIES, RETRY_DELAY
)


class ParallelConversationGenerator:
    """병렬 대화 생성기"""

    def __init__(self, batch_size: int = 100, checkpoint_interval: int = 1000, max_workers: int = 10):
        self.api_key = os.environ.get("AIMLAPI_API_KEY")
        if not self.api_key:
            raise ValueError("AIMLAPI_API_KEY 환경변수가 설정되지 않았습니다")

        self.api_base = "https://api.aimlapi.com/v1"
        self.model = "claude-sonnet-4-5"
        self.batch_size = batch_size
        self.checkpoint_interval = checkpoint_interval
        self.max_workers = max_workers

        # Thread-safe 카운터
        self.lock = threading.Lock()
        self.total_generated = 0
        self.total_errors = 0

        print(f"병렬 작업자 수: {max_workers}개")
        print(f"예상 속도 향상: 약 {max_workers}배")

    def call_aiml_api(self, prompt: str, retry_count: int = 0) -> Optional[str]:
        """AIML API 호출 (재시도 로직 포함)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192,
            "temperature": 0.7
        }

        try:
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
            if retry_count < MAX_RETRIES:
                wait_time = RETRY_DELAY * (2 ** retry_count)
                time.sleep(wait_time)
                return self.call_aiml_api(prompt, retry_count + 1)
            else:
                with self.lock:
                    self.total_errors += 1
                return None

    def load_seeds(self, category: str) -> List[Dict]:
        """시드 파일 로드"""
        seeds = []

        # 카테고리 매핑 (영어 -> 한국어)
        category_map = {
            "adolescent": "청소년",
            "adult": "성인",
            "crisis": "위기대응"
        }

        korean_category = category_map.get(category, category)
        seed_dir = SEEDS_DIR / korean_category

        for seed_file in seed_dir.rglob("*.json"):
            try:
                with open(seed_file, 'r', encoding='utf-8') as f:
                    seed = json.load(f)
                    seeds.append(seed)
            except Exception:
                continue

        return seeds

    def create_generation_prompt(self, seed: Dict) -> str:
        """대화 생성 프롬프트 생성"""
        category = seed.get('category', '일반')
        persona = seed.get('persona', {})
        situation = seed.get('situation', '')

        prompt = f"""다음 시드 시나리오를 참고하여 새로운 심리상담 대화를 생성해주세요.

시드 정보:
- 카테고리: {category}
- 내담자 페르소나: {persona.get('age', '미상')}세, {persona.get('gender', '미상')}, {persona.get('occupation', '미상')}
- 상황: {situation}

요구사항:
1. 시드와 다른 새로운 페르소나와 상황 만들기
2. 25-35턴의 자연스러운 상담 대화
3. 상담 기법 레이블 포함 (empathy, reflection, validation 등)
4. JSON 형식으로 반환

JSON 형식:
{{
    "conversation_id": "unique_id",
    "category": "{category}",
    "persona": {{"age": 나이, "gender": "성별", "occupation": "직업"}},
    "situation": "새로운 상황 설명",
    "conversation": [
        {{"speaker": "client", "text": "...", "turn": 1}},
        {{"speaker": "counselor", "text": "...", "turn": 2, "technique": "empathy"}}
    ]
}}

반드시 완전한 JSON만 반환하세요. 추가 설명 없이 JSON만 출력하세요."""

        return prompt

    def parse_json_response(self, response: str) -> Optional[Dict]:
        """JSON 응답 파싱"""
        if not response:
            return None

        try:
            # JSON 블록 추출
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            data = json.loads(response)
            return data

        except json.JSONDecodeError:
            return None

    def generate_single_conversation(self, seed: Dict, category: str, index: int) -> Optional[str]:
        """단일 대화 생성 (워커 스레드용)"""
        try:
            # 프롬프트 생성
            prompt = self.create_generation_prompt(seed)

            # API 호출
            response = self.call_aiml_api(prompt)
            if not response:
                return None

            # JSON 파싱
            conversation_data = self.parse_json_response(response)
            if not conversation_data:
                return None

            # 파일 저장
            output_file = RAW_DIR / category / f"conv_{category}_{index:06d}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            conversation_data['metadata'] = {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'model': self.model,
                'seed_category': seed.get('category', 'unknown')
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)

            with self.lock:
                self.total_generated += 1

            return str(output_file)

        except Exception as e:
            with self.lock:
                self.total_errors += 1
            return None

    def generate_batch_parallel(self, category: str, start_index: int, count: int):
        """병렬로 배치 생성"""
        seeds = self.load_seeds(category)
        if not seeds:
            print(f"⚠️  {category} 시드 파일 없음")
            return

        print(f"\n📦 시드 파일 {len(seeds)}개 로드됨")
        print(f"🔄 {count}개 대화 생성 시작 (병렬 {self.max_workers}개)")

        # 작업 목록 생성
        tasks = []
        for i in range(count):
            index = start_index + i
            seed = random.choice(seeds)
            tasks.append((seed, category, index))

        # 병렬 실행
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.generate_single_conversation, seed, cat, idx): idx
                for seed, cat, idx in tasks
            }

            # 진행 상황 표시
            with tqdm(total=count, desc="생성", unit="개") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    pbar.update(1)

                    # 주기적으로 통계 표시
                    if pbar.n % 10 == 0:
                        pbar.set_postfix({
                            '완료': self.total_generated,
                            '오류': self.total_errors
                        })

    def generate_all(self, total_count: int = 9800):
        """전체 생성 프로세스"""
        print("\n" + "="*70)
        print("🚀 한국어 심리상담 데이터셋 생성 시작 (병렬 처리)")
        print("="*70)
        print(f"📊 총 목표: {total_count:,}개")
        print(f"🤖 모델: {self.model}")
        print(f"⚡ 병렬 작업자: {self.max_workers}개")
        print(f"📦 배치 크기: {self.batch_size}개")
        print(f"💾 체크포인트 간격: {self.checkpoint_interval}개")
        print("="*70)

        # 카테고리별 목표 계산
        targets = {
            'adolescent': int(total_count * 0.55),
            'adult': int(total_count * 0.40),
            'crisis': int(total_count * 0.05)
        }

        # 기존 파일 개수 확인
        existing = {}
        for category in targets:
            category_dir = RAW_DIR / category
            if category_dir.exists():
                existing[category] = len(list(category_dir.glob("conv_*.json")))
            else:
                existing[category] = 0

        print(f"\n📁 기존 파일 개수:")
        for category, count in existing.items():
            target = targets[category]
            remaining = max(0, target - count)
            print(f"  - {category}: {count}개 (목표: {target}개, 남은 개수: {remaining}개)")

        # 카테고리별 생성
        for category, target in targets.items():
            remaining = max(0, target - existing[category])
            if remaining == 0:
                continue

            print(f"\n{'='*70}")
            print(f"📝 카테고리: {category}")
            print(f"🎯 목표: {remaining}개 (시작 인덱스: {existing[category]})")
            print(f"{'='*70}")

            # 배치 단위로 생성
            batches = (remaining + self.batch_size - 1) // self.batch_size

            for batch_num in range(batches):
                batch_start = existing[category] + (batch_num * self.batch_size)
                batch_count = min(self.batch_size, remaining - (batch_num * self.batch_size))

                print(f"\n🔄 배치 {batch_num + 1}/{batches} ({batch_count}개)")

                self.generate_batch_parallel(category, batch_start, batch_count)

                # 체크포인트
                if (batch_num + 1) * self.batch_size % self.checkpoint_interval == 0:
                    print(f"\n💾 체크포인트: {self.total_generated}개 생성 완료")

        print(f"\n{'='*70}")
        print(f"✅ 전체 생성 완료!")
        print(f"📊 총 생성: {self.total_generated}개")
        print(f"⚠️  총 오류: {self.total_errors}개")
        print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(description='병렬 대화 생성')
    parser.add_argument('--batch-size', type=int, default=100, help='배치 크기')
    parser.add_argument('--checkpoint', type=int, default=1000, help='체크포인트 간격')
    parser.add_argument('--total', type=int, default=9800, help='총 생성 개수')
    parser.add_argument('--workers', type=int, default=10, help='병렬 작업자 수 (기본: 10)')

    args = parser.parse_args()

    try:
        generator = ParallelConversationGenerator(
            batch_size=args.batch_size,
            checkpoint_interval=args.checkpoint,
            max_workers=args.workers
        )
        generator.generate_all(total_count=args.total)

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
