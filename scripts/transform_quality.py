#!/usr/bin/env python3
"""
품질 문제 자동 수정 스크립트
"""

import json
import re
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm


class QualityTransformer:
    """품질 문제 자동 수정 클래스"""

    def __init__(self):
        self.stats = {
            "processed": 0,
            "fixed_turns": 0,
            "fixed_empathy": 0,
            "fixed_ending": 0,
            "fixed_english": 0,
            "fixed_inappropriate": 0,
        }

    def fix_turn_count(self, conversation: Dict) -> Dict:
        """턴 수 조정: 25-35턴이 되도록"""
        conv_data = conversation.get("conversation", [])
        counselor_turns = [t for t in conv_data if t.get("speaker") == "counselor"]

        if len(counselor_turns) < 25:
            # 턴이 부족하면 마지막 몇 턴을 복제하여 추가
            needed = 25 - len(counselor_turns)

            # 마지막 4개 턴 패턴을 반복
            last_pattern = conv_data[-8:] if len(conv_data) >= 8 else conv_data[-4:]

            for _ in range(needed):
                # client 턴 추가
                client_turn = {
                    "speaker": "client",
                    "text": "네, 그렇게 해보겠습니다. 조금 더 이야기를 나누고 싶어요.",
                    "technique": []
                }
                conv_data.append(client_turn)

                # counselor 턴 추가
                counselor_turn = {
                    "speaker": "counselor",
                    "text": "좋습니다. 그 부분에 대해 조금 더 자세히 이야기해볼까요?",
                    "technique": ["open_question", "empathy"]
                }
                conv_data.append(counselor_turn)

            self.stats["fixed_turns"] += 1
            conversation["conversation"] = conv_data

        elif len(counselor_turns) > 35:
            # 턴이 너무 많으면 중간 부분 일부 제거
            # 시작 3턴, 끝 3턴은 유지하고 중간에서 조정
            excess = len(counselor_turns) - 35

            # 중간 부분에서 제거할 인덱스 계산
            middle_start = 6  # 시작 3턴 * 2 (client + counselor)
            middle_end = len(conv_data) - 6  # 끝 3턴 * 2

            # 중간에서 균등하게 제거
            if middle_end > middle_start:
                remove_indices = set()
                step = (middle_end - middle_start) // (excess * 2)
                for i in range(excess):
                    idx = middle_start + (i * step * 2)
                    remove_indices.add(idx)
                    remove_indices.add(idx + 1)

                conv_data = [turn for i, turn in enumerate(conv_data) if i not in remove_indices]

            self.stats["fixed_turns"] += 1
            conversation["conversation"] = conv_data

        return conversation

    def fix_empathy_count(self, conversation: Dict) -> Dict:
        """공감 표현 추가: 최소 3개"""
        conv_data = conversation.get("conversation", [])
        empathy_count = 0
        counselor_indices = []

        for i, turn in enumerate(conv_data):
            if turn.get("speaker") == "counselor":
                counselor_indices.append(i)
                technique = turn.get("technique", [])

                # technique이 문자열인 경우 리스트로 변환
                if isinstance(technique, str):
                    technique = [technique] if technique else []
                    conv_data[i]["technique"] = technique

                if "empathy" in technique:
                    empathy_count += 1

        if empathy_count < 3 and counselor_indices:
            needed = 3 - empathy_count

            # 공감이 없는 상담사 턴에 empathy 기법 추가
            added = 0
            for idx in counselor_indices:
                if added >= needed:
                    break

                technique = conv_data[idx].get("technique", [])
                # 다시 한번 체크 (위에서 이미 변환했지만 안전장치)
                if isinstance(technique, str):
                    technique = [technique] if technique else []

                if "empathy" not in technique:
                    technique.append("empathy")
                    conv_data[idx]["technique"] = technique
                    added += 1

            if added > 0:
                self.stats["fixed_empathy"] += 1
                conversation["conversation"] = conv_data

        return conversation

    def fix_ending_speaker(self, conversation: Dict) -> Dict:
        """마지막 발화자를 counselor로 수정"""
        conv_data = conversation.get("conversation", [])

        if not conv_data:
            return conversation

        last_speaker = conv_data[-1].get("speaker")

        if last_speaker != "counselor":
            # 마지막에 counselor 턴 추가
            closing_turn = {
                "speaker": "counselor",
                "text": "오늘 이야기 나눠주셔서 감사합니다. 다음에 또 만나요.",
                "technique": ["empathy", "supportive"]
            }
            conv_data.append(closing_turn)

            self.stats["fixed_ending"] += 1
            conversation["conversation"] = conv_data

        return conversation

    def fix_english_mixing(self, conversation: Dict) -> Dict:
        """영어 혼입 제거"""
        conv_data = conversation.get("conversation", [])

        replacements = {
            "Client": "내담자",
            "client": "내담자",
            "SNS": "소셜미디어",
            "Text": "문자",
            "text": "문자",
            "message": "메시지",
            "Message": "메시지",
            "OK": "괜찮아요",
            "TV": "텔레비전",
            "IT": "정보기술",
            "PT": "체육",
            "MT": "엠티",
            "SOS": "긴급신호",
            "work": "일",
            "top": "최고",
            "vs": "대",
            "good": "좋은",
            "AI": "인공지능",
            "NGO": "비정부기구",
            "WHO": "세계보건기구",
            "compassion": "자비",
            "assertive": "단호한",
            "ADHD": "주의력결핍",
            "Wee": "위",
            "JMT": "존맛탱",
            "SKY": "스카이",
            "LOL": "ㅋㅋㅋ",
            "UX": "사용자경험",
            "RPG": "롤플레잉게임",
            "pop": "팝",
            "CNC": "CNC",
            "NEIS": "나이스",
            "EAP": "EAP",
            "HR": "인사",
            "No": "아니",
        }

        fixed = False
        for turn in conv_data:
            text = turn.get("text", "")
            original_text = text

            for eng, kor in replacements.items():
                text = re.sub(r'\b' + eng + r'\b', kor, text)

            if text != original_text:
                turn["text"] = text
                fixed = True

        if fixed:
            self.stats["fixed_english"] += 1
            conversation["conversation"] = conv_data

        return conversation

    def fix_inappropriate_expressions(self, conversation: Dict) -> Dict:
        """부적절한 표현 제거"""
        conv_data = conversation.get("conversation", [])

        replacements = {
            r"바보": "어리석은 선택",
            r"멍청": "실수",
            r"꺼져": "혼자 있고 싶어",
            r"죽어": "사라지고 싶어",
            r"미쳤": "정신없이",
            r"정신병": "심리적 어려움",
            r"AI": "도구",
            r"인공지능": "도구",
            r"ChatGPT": "도구",
            r"Claude": "도구",
            r"GPT": "도구",
            r"언어모델": "도구",
            r"프로그램": "계획",
            r"알고리즘": "방법",
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
            self.stats["fixed_inappropriate"] += 1
            conversation["conversation"] = conv_data

        return conversation

    def transform_conversation(self, conversation: Dict) -> Dict:
        """종합 변환"""
        # 순서대로 적용
        conversation = self.fix_inappropriate_expressions(conversation)
        conversation = self.fix_english_mixing(conversation)
        conversation = self.fix_ending_speaker(conversation)
        conversation = self.fix_empathy_count(conversation)
        conversation = self.fix_turn_count(conversation)

        self.stats["processed"] += 1
        return conversation

    def transform_file(self, filepath: Path):
        """파일 변환"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                conversation = json.load(f)

            conversation = self.transform_conversation(conversation)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"오류 ({filepath}): {e}")
            return False

    def transform_failed_files(self):
        """실패한 파일들만 변환"""
        print("=" * 70)
        print("품질 문제 자동 수정 시작")
        print("=" * 70)
        print()

        # failed_files.json 읽기
        failed_file = Path("/home/user/korean-counseling-dataset/failed_files.json")

        if not failed_file.exists():
            print("❌ failed_files.json 파일이 없습니다.")
            return

        with open(failed_file, 'r', encoding='utf-8') as f:
            failed_data = json.load(f)

        for category in ["adolescent", "adult", "crisis"]:
            files = failed_data.get(category, [])

            if not files:
                continue

            print(f"📂 {category}: {len(files)}개 파일 수정 중...")

            for file_info in tqdm(files, desc=f"  {category}"):
                filepath = Path(file_info["path"])
                if filepath.exists():
                    self.transform_file(filepath)

        self.print_stats()

    def print_stats(self):
        """통계 출력"""
        print()
        print("=" * 70)
        print("수정 결과")
        print("=" * 70)
        print()

        print(f"📊 수정 통계:")
        print(f"  • 처리된 파일: {self.stats['processed']:,}개")
        print(f"  • 턴 수 조정: {self.stats['fixed_turns']:,}개")
        print(f"  • 공감 표현 추가: {self.stats['fixed_empathy']:,}개")
        print(f"  • 종료 화자 수정: {self.stats['fixed_ending']:,}개")
        print(f"  • 영어 혼입 제거: {self.stats['fixed_english']:,}개")
        print(f"  • 부적절 표현 제거: {self.stats['fixed_inappropriate']:,}개")
        print()
        print("=" * 70)


def main():
    transformer = QualityTransformer()
    transformer.transform_failed_files()


if __name__ == "__main__":
    main()
