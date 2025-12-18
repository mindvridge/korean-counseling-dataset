#!/usr/bin/env python3
"""
남은 품질 이슈 수정 스크립트
- 영어 단어 제거
- 기법 라벨 누락 수정
"""

import json
import re
from pathlib import Path
from tqdm import tqdm


class RemainingIssuesFixer:
    """남은 이슈 수정 클래스"""

    def __init__(self):
        self.stats = {
            "processed": 0,
            "fixed_english": 0,
            "fixed_labels": 0,
        }

    def fix_remaining_english(self, conversation: dict) -> dict:
        """남은 영어 단어 제거"""
        conv_data = conversation.get("conversation", [])

        # 추가 영어 단어 교체
        replacements = {
            r"\blife\b": "삶",
            r"\ball\b": "모든",
            r"\bMVP\b": "최우수선수",
            r"\bFear\b": "두려움",
            r"\bFOMO\b": "소외공포",
            r"\benough\b": "충분히",
            r"\bcommunication\b": "소통",
            r"\bEAP\b": "직원지원",
            r"\bimage\b": "이미지",
            r"\bCNC\b": "수치제어",
            r"\bbalance\b": "균형",
            r"\bor\b": "또는",
            r"\bMinimum\b": "최소",
            r"\bOf\b": "의",
            r"\bof\b": "의",
            r"\bnothing\b": "아무것도",
            r"\bViable\b": "실행가능한",
            r"\bMissing\b": "누락된",
            r"\bProduct\b": "제품",
            r"\bOut\b": "밖",
        }

        fixed = False
        for turn in conv_data:
            text = turn.get("text", "")
            original_text = text

            for pattern, replacement in replacements.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

            if text != original_text:
                turn["text"] = text
                fixed = True

        if fixed:
            self.stats["fixed_english"] += 1
            conversation["conversation"] = conv_data

        return conversation

    def fix_missing_labels(self, conversation: dict) -> dict:
        """기법 라벨 누락 수정"""
        conv_data = conversation.get("conversation", [])

        fixed = False
        for turn in conv_data:
            if turn.get("speaker") == "counselor":
                technique = turn.get("technique", [])

                # 문자열인 경우 리스트로 변환
                if isinstance(technique, str):
                    technique = [technique] if technique else []

                # 빈 리스트거나 누락된 경우 기본 기법 추가
                if not technique or len(technique) == 0:
                    # 텍스트 기반으로 적절한 기법 추론
                    text = turn.get("text", "").lower()

                    default_techniques = ["reflection"]

                    # 공감 표현 패턴
                    if any(word in text for word in ["힘드", "어려우", "걱정", "속상", "괜찮"]):
                        default_techniques.append("empathy")

                    # 질문 패턴
                    if "?" in text or "까요" in text or "나요" in text:
                        default_techniques.append("open_question")

                    technique = default_techniques
                    turn["technique"] = technique
                    fixed = True

        if fixed:
            self.stats["fixed_labels"] += 1
            conversation["conversation"] = conv_data

        return conversation

    def fix_file(self, filepath: Path):
        """파일 수정"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                conversation = json.load(f)

            original = json.dumps(conversation)

            conversation = self.fix_remaining_english(conversation)
            conversation = self.fix_missing_labels(conversation)

            modified = json.dumps(conversation)

            if original != modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(conversation, f, ensure_ascii=False, indent=2)
                self.stats["processed"] += 1

            return True
        except Exception as e:
            print(f"오류 ({filepath}): {e}")
            return False

    def fix_all_files(self):
        """모든 파일 수정"""
        print("=" * 70)
        print("남은 품질 이슈 수정 시작")
        print("=" * 70)
        print()

        base_dir = Path("/home/user/korean-counseling-dataset/data/raw")

        for category in ["adolescent", "adult", "crisis"]:
            cat_dir = base_dir / category
            if not cat_dir.exists():
                continue

            files = sorted(list(cat_dir.glob("conv_*.json")))
            if not files:
                continue

            print(f"📂 {category}: {len(files)}개 파일 처리 중...")

            for filepath in tqdm(files, desc=f"  {category}"):
                self.fix_file(filepath)

        self.print_stats()

    def print_stats(self):
        """통계 출력"""
        print()
        print("=" * 70)
        print("수정 결과")
        print("=" * 70)
        print()

        print(f"📊 수정 통계:")
        print(f"  • 수정된 파일: {self.stats['processed']:,}개")
        print(f"  • 영어 단어 제거: {self.stats['fixed_english']:,}개")
        print(f"  • 기법 라벨 추가: {self.stats['fixed_labels']:,}개")
        print()
        print("=" * 70)


def main():
    fixer = RemainingIssuesFixer()
    fixer.fix_all_files()


if __name__ == "__main__":
    main()
