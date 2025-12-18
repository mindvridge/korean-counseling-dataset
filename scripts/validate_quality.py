#!/usr/bin/env python3
"""
품질 검증 스크립트 - 사용자 정의 기준
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
from tqdm import tqdm


class QualityValidator:
    """품질 검증 클래스"""

    def __init__(self):
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "failure_types": defaultdict(int),
            "by_category": defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0, "failures": defaultdict(int)})
        }

    def validate_turn_count(self, conversation: Dict) -> Tuple[bool, str]:
        """턴 수 검증: 25-35턴"""
        conv_data = conversation.get("conversation", [])
        # 상담사와 내담자 각각의 턴 수 계산
        counselor_turns = len([t for t in conv_data if t.get("speaker") == "counselor"])

        if counselor_turns < 25:
            return False, f"턴수부족({counselor_turns}턴)"
        if counselor_turns > 35:
            return False, f"턴수초과({counselor_turns}턴)"
        return True, ""

    def validate_technique_labels(self, conversation: Dict) -> Tuple[bool, str]:
        """기법 라벨 검증: 모든 상담사 발화에 존재"""
        conv_data = conversation.get("conversation", [])
        counselor_turns = [t for t in conv_data if t.get("speaker") == "counselor"]

        for i, turn in enumerate(counselor_turns, 1):
            technique = turn.get("technique", [])
            if not technique or len(technique) == 0:
                return False, f"기법라벨누락(턴{i})"
        return True, ""

    def validate_no_english(self, conversation: Dict) -> Tuple[bool, str]:
        """영어 혼입 검증: 없음 (단, 상담 기법 용어는 제외)"""
        conv_data = conversation.get("conversation", [])

        # 허용되는 영어 패턴 (상담 기법, 숫자 등)
        allowed_patterns = [
            r'\d+',  # 숫자
            r'[A-Z]{1,3}[_-]?\d+',  # ID 패턴 (ADO_20251218_1234)
        ]

        for turn in conv_data:
            text = turn.get("text", "")

            # 영어 단어 찾기
            english_words = re.findall(r'\b[A-Za-z]+\b', text)

            for word in english_words:
                # 허용 패턴 체크
                is_allowed = False
                for pattern in allowed_patterns:
                    if re.match(pattern, word):
                        is_allowed = True
                        break

                if not is_allowed and len(word) > 1:  # 단일 문자는 허용
                    return False, f"영어혼입({word})"

        return True, ""

    def validate_conversation_structure(self, conversation: Dict) -> Tuple[bool, str]:
        """대화 구조 검증: 내담자로 시작, 상담사로 종료"""
        conv_data = conversation.get("conversation", [])

        if not conv_data:
            return False, "대화없음"

        # 첫 발화자 확인
        first_speaker = conv_data[0].get("speaker")
        if first_speaker != "client":
            return False, f"시작오류({first_speaker})"

        # 마지막 발화자 확인
        last_speaker = conv_data[-1].get("speaker")
        if last_speaker != "counselor":
            return False, f"종료오류({last_speaker})"

        return True, ""

    def validate_empathy_count(self, conversation: Dict) -> Tuple[bool, str]:
        """공감 표현 검증: 3개 이상"""
        conv_data = conversation.get("conversation", [])
        empathy_count = 0

        for turn in conv_data:
            if turn.get("speaker") == "counselor":
                technique = turn.get("technique", [])
                if "empathy" in technique:
                    empathy_count += 1

        if empathy_count < 3:
            return False, f"공감부족({empathy_count}회)"

        return True, ""

    def validate_no_inappropriate(self, conversation: Dict) -> Tuple[bool, str]:
        """부적절한 표현 검증"""
        conv_data = conversation.get("conversation", [])

        inappropriate_patterns = [
            r"바보",
            r"멍청",
            r"꺼져",
            r"죽어",
            r"미쳤",
            r"정신병",
            r"AI",
            r"인공지능",
            r"ChatGPT",
            r"Claude",
            r"GPT",
            r"언어모델",
            r"프로그램",
            r"알고리즘",
        ]

        full_text = " ".join([t.get("text", "") for t in conv_data])

        for pattern in inappropriate_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                return False, f"부적절표현({pattern})"

        return True, ""

    def validate_crisis_resources(self, conversation: Dict) -> Tuple[bool, str]:
        """위기 대응 검증: crisis 카테고리에서 자원 언급"""
        category = conversation.get("category", "")

        # crisis 카테고리가 아니면 통과
        if category != "crisis":
            return True, ""

        conv_data = conversation.get("conversation", [])
        full_text = " ".join([t.get("text", "") for t in conv_data if t.get("speaker") == "counselor"])

        # 위기 자원 키워드
        resource_keywords = [
            r"1393",  # 자살예방상담전화
            r"1577-0199",  # 정신건강위기상담
            r"위기상담",
            r"응급",
            r"병원",
            r"의료",
            r"전문가",
            r"정신과",
            r"119",
        ]

        has_resource = False
        for keyword in resource_keywords:
            if re.search(keyword, full_text):
                has_resource = True
                break

        if not has_resource:
            return False, "위기자원누락"

        return True, ""

    def validate_conversation(self, conversation: Dict, filepath: Path) -> Tuple[bool, List[str]]:
        """종합 검증"""
        failures = []

        # 1. 턴 수
        passed, error = self.validate_turn_count(conversation)
        if not passed:
            failures.append(error)

        # 2. 기법 라벨
        passed, error = self.validate_technique_labels(conversation)
        if not passed:
            failures.append(error)

        # 3. 영어 혼입
        passed, error = self.validate_no_english(conversation)
        if not passed:
            failures.append(error)

        # 4. 대화 구조
        passed, error = self.validate_conversation_structure(conversation)
        if not passed:
            failures.append(error)

        # 5. 공감 표현
        passed, error = self.validate_empathy_count(conversation)
        if not passed:
            failures.append(error)

        # 6. 부적절한 표현
        passed, error = self.validate_no_inappropriate(conversation)
        if not passed:
            failures.append(error)

        # 7. 위기 자원
        passed, error = self.validate_crisis_resources(conversation)
        if not passed:
            failures.append(error)

        return len(failures) == 0, failures

    def validate_file(self, filepath: Path) -> Tuple[bool, List[str]]:
        """파일 검증"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                conversation = json.load(f)

            return self.validate_conversation(conversation, filepath)
        except Exception as e:
            return False, [f"파일오류({str(e)})"]

    def validate_all(self):
        """전체 검증"""
        print("=" * 70)
        print("품질 검증 시작")
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

            print(f"📂 {category}: {len(files)}개 파일 검증 중...")

            for filepath in tqdm(files, desc=f"  {category}"):
                self.results["total"] += 1
                self.results["by_category"][category]["total"] += 1

                passed, failures = self.validate_file(filepath)

                if passed:
                    self.results["passed"] += 1
                    self.results["by_category"][category]["passed"] += 1
                else:
                    self.results["failed"] += 1
                    self.results["by_category"][category]["failed"] += 1

                    # 실패 유형 카운트
                    for failure in failures:
                        self.results["failure_types"][failure] += 1
                        self.results["by_category"][category]["failures"][failure] += 1

        self.print_summary()

    def print_summary(self):
        """결과 요약 출력"""
        print()
        print("=" * 70)
        print("검증 결과")
        print("=" * 70)
        print()

        # 전체 통계
        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"📊 전체 통계:")
        print(f"  • 총 파일: {total:,}개")
        print(f"  • 통과: {passed:,}개 ({pass_rate:.1f}%)")
        print(f"  • 실패: {failed:,}개 ({100-pass_rate:.1f}%)")
        print()

        # 카테고리별 통계
        print(f"📁 카테고리별 통계:")
        for category in ["adolescent", "adult", "crisis"]:
            if category in self.results["by_category"]:
                stats = self.results["by_category"][category]
                cat_total = stats["total"]
                cat_passed = stats["passed"]
                cat_rate = (cat_passed / cat_total * 100) if cat_total > 0 else 0

                print(f"  • {category:12s}: {cat_passed:,}/{cat_total:,} ({cat_rate:.1f}%) 통과")
        print()

        # 실패 유형별 통계
        if self.results["failure_types"]:
            print(f"❌ 실패 유형별 통계 (중복 포함):")
            sorted_failures = sorted(
                self.results["failure_types"].items(),
                key=lambda x: x[1],
                reverse=True
            )

            for failure_type, count in sorted_failures:
                percentage = (count / total * 100) if total > 0 else 0
                print(f"  • {failure_type:20s}: {count:,}건 ({percentage:.1f}%)")
            print()

        # 카테고리별 실패 유형
        print(f"📂 카테고리별 실패 유형:")
        for category in ["adolescent", "adult", "crisis"]:
            if category in self.results["by_category"]:
                failures = self.results["by_category"][category]["failures"]
                if failures:
                    print(f"\n  [{category}]")
                    sorted_cat_failures = sorted(
                        failures.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    for failure_type, count in sorted_cat_failures[:5]:  # 상위 5개만
                        print(f"    - {failure_type}: {count}건")

        print()
        print("=" * 70)

        # 결과 파일 저장
        output_file = Path("/home/user/korean-counseling-dataset/validation_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            # defaultdict를 일반 dict로 변환
            save_data = {
                "total": self.results["total"],
                "passed": self.results["passed"],
                "failed": self.results["failed"],
                "pass_rate": pass_rate,
                "failure_types": dict(self.results["failure_types"]),
                "by_category": {
                    k: {
                        "total": v["total"],
                        "passed": v["passed"],
                        "failed": v["failed"],
                        "failures": dict(v["failures"])
                    }
                    for k, v in self.results["by_category"].items()
                }
            }
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        print(f"📄 결과 저장: {output_file}")


def main():
    validator = QualityValidator()
    validator.validate_all()


if __name__ == "__main__":
    main()
