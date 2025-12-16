#!/usr/bin/env python3
"""
포맷 변환 스크립트
필터링된 대화를 다양한 파인튜닝 포맷으로 변환합니다.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from tqdm import tqdm
import argparse

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import FILTERED_DIR, FINAL_DIR, LOGS_DIR


class FormatConverter:
    """포맷 변환 클래스"""

    SYSTEM_PROMPT = """당신은 전문 심리상담사입니다. 내담자의 이야기에 공감하고, 적절한 질문과 반영을 통해 내담자가 자신의 감정과 생각을 탐색할 수 있도록 도와주세요.

상담 원칙:
1. 비판단적이고 수용적인 태도를 유지합니다.
2. 내담자의 감정을 인정하고 반영합니다.
3. 개방형 질문을 통해 탐색을 촉진합니다.
4. 전문적인 경계를 유지합니다.
5. 위기 상황에서는 적절한 자원을 안내합니다."""

    def __init__(self):
        self.stats = {
            "total": 0,
            "converted": 0,
            "by_format": {}
        }

    def load_filtered_data(self) -> List[Dict]:
        """필터링된 데이터 로드"""
        data = []

        for category in ["adolescent", "adult", "crisis"]:
            cat_dir = FILTERED_DIR / category
            if not cat_dir.exists():
                continue

            for filepath in cat_dir.glob("*.json"):
                with open(filepath, 'r', encoding='utf-8') as f:
                    conv = json.load(f)
                    conv["_source_file"] = str(filepath)
                    data.append(conv)

        return data

    def to_chatml(self, conversation: Dict) -> Dict:
        """ChatML 포맷으로 변환 (OpenAI 스타일)"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

        for turn in conversation.get("conversation", []):
            role = "user" if turn.get("speaker") == "client" else "assistant"
            messages.append({
                "role": role,
                "content": turn.get("text", "")
            })

        return {"messages": messages}

    def to_alpaca(self, conversation: Dict) -> List[Dict]:
        """Alpaca 포맷으로 변환 (instruction/input/output)"""
        samples = []
        conv_data = conversation.get("conversation", [])

        # 대화를 instruction-output 쌍으로 변환
        context = []

        for i, turn in enumerate(conv_data):
            if turn.get("speaker") == "client":
                # 내담자 발화 = instruction의 일부
                context.append(f"내담자: {turn.get('text', '')}")
            else:
                # 상담사 응답 = output
                if context:
                    sample = {
                        "instruction": "다음 상담 대화에서 상담사로서 적절한 응답을 제공하세요.",
                        "input": "\n".join(context),
                        "output": turn.get("text", "")
                    }
                    samples.append(sample)
                    context.append(f"상담사: {turn.get('text', '')}")

        return samples

    def to_sharegpt(self, conversation: Dict) -> Dict:
        """ShareGPT 포맷으로 변환"""
        conversations = []

        for turn in conversation.get("conversation", []):
            role = "human" if turn.get("speaker") == "client" else "gpt"
            conversations.append({
                "from": role,
                "value": turn.get("text", "")
            })

        return {
            "id": conversation.get("_source_file", "unknown"),
            "conversations": conversations
        }

    def to_llama_chat(self, conversation: Dict) -> str:
        """LLaMA Chat 포맷으로 변환"""
        parts = [f"<s>[INST] <<SYS>>\n{self.SYSTEM_PROMPT}\n<</SYS>>\n\n"]

        conv_data = conversation.get("conversation", [])
        first_client = True

        for turn in conv_data:
            if turn.get("speaker") == "client":
                if first_client:
                    parts.append(f"{turn.get('text', '')} [/INST] ")
                    first_client = False
                else:
                    parts.append(f"<s>[INST] {turn.get('text', '')} [/INST] ")
            else:
                parts.append(f"{turn.get('text', '')} </s>")

        return "".join(parts)

    def to_simple_pairs(self, conversation: Dict) -> List[Dict]:
        """단순 Q&A 쌍으로 변환"""
        pairs = []
        conv_data = conversation.get("conversation", [])

        for i in range(0, len(conv_data) - 1, 2):
            if conv_data[i].get("speaker") == "client" and \
               i + 1 < len(conv_data) and \
               conv_data[i + 1].get("speaker") == "counselor":
                pairs.append({
                    "question": conv_data[i].get("text", ""),
                    "answer": conv_data[i + 1].get("text", "")
                })

        return pairs

    def convert_all(self, formats: List[str] = None):
        """모든 데이터를 지정된 포맷으로 변환"""
        if formats is None:
            formats = ["chatml", "alpaca", "sharegpt", "llama_chat"]

        print("=" * 60)
        print("포맷 변환 시작")
        print(f"변환 포맷: {', '.join(formats)}")
        print("=" * 60)

        data = self.load_filtered_data()
        print(f"\n로드된 대화 수: {len(data)}")

        FINAL_DIR.mkdir(parents=True, exist_ok=True)

        results = {fmt: [] for fmt in formats}

        for conv in tqdm(data, desc="변환 중"):
            self.stats["total"] += 1

            for fmt in formats:
                if fmt == "chatml":
                    results["chatml"].append(self.to_chatml(conv))
                elif fmt == "alpaca":
                    results["alpaca"].extend(self.to_alpaca(conv))
                elif fmt == "sharegpt":
                    results["sharegpt"].append(self.to_sharegpt(conv))
                elif fmt == "llama_chat":
                    results["llama_chat"].append({
                        "text": self.to_llama_chat(conv)
                    })

        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for fmt, data_list in results.items():
            if not data_list:
                continue

            filename = f"counseling_dataset_{fmt}_{timestamp}.json"
            filepath = FINAL_DIR / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)

            self.stats["by_format"][fmt] = len(data_list)
            print(f"\n[{fmt}] 저장 완료: {filepath}")
            print(f"  - 샘플 수: {len(data_list)}")

        # JSONL 포맷도 저장 (OpenAI 파인튜닝용)
        if "chatml" in formats:
            jsonl_path = FINAL_DIR / f"counseling_dataset_chatml_{timestamp}.jsonl"
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for item in results["chatml"]:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            print(f"\n[chatml-jsonl] 저장 완료: {jsonl_path}")

        self._print_summary()

    def _print_summary(self):
        """결과 요약"""
        print("\n" + "=" * 60)
        print("변환 완료")
        print("=" * 60)
        print(f"처리된 대화: {self.stats['total']}")
        print("\n포맷별 샘플 수:")
        for fmt, count in self.stats["by_format"].items():
            print(f"  - {fmt}: {count}")

        # 통계 저장
        stats_file = LOGS_DIR / f"convert_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)


def create_dataset_info():
    """데이터셋 정보 파일 생성"""
    info = {
        "name": "Korean Counseling Dataset",
        "description": "한국어 심리상담 AI 파인튜닝용 멀티턴 대화 데이터셋",
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "statistics": {
            "target_total": 10000,
            "turns_per_conversation": "25-35",
            "categories": {
                "adolescent": "55%",
                "adult": "40%",
                "crisis": "5%"
            }
        },
        "formats": {
            "chatml": "OpenAI GPT 파인튜닝용 (messages 형식)",
            "alpaca": "Alpaca 스타일 instruction 튜닝용",
            "sharegpt": "ShareGPT 포맷 (LoRA 학습 등)",
            "llama_chat": "LLaMA-2 Chat 템플릿 형식"
        },
        "license": "연구 및 교육 목적으로 사용 가능",
        "contact": ""
    }

    info_path = FINAL_DIR / "dataset_info.json"
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    print(f"데이터셋 정보 저장: {info_path}")


def main():
    parser = argparse.ArgumentParser(description="데이터셋 포맷 변환")
    parser.add_argument(
        "--formats", "-f",
        nargs="+",
        choices=["chatml", "alpaca", "sharegpt", "llama_chat", "all"],
        default=["all"],
        help="변환할 포맷 (기본: all)"
    )
    parser.add_argument(
        "--info-only",
        action="store_true",
        help="데이터셋 정보 파일만 생성"
    )

    args = parser.parse_args()

    if args.info_only:
        create_dataset_info()
        return

    formats = args.formats
    if "all" in formats:
        formats = ["chatml", "alpaca", "sharegpt", "llama_chat"]

    converter = FormatConverter()
    converter.convert_all(formats)
    create_dataset_info()


if __name__ == "__main__":
    main()
