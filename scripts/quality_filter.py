#!/usr/bin/env python3
"""
품질 필터링 스크립트
생성된 대화의 품질을 평가하고 필터링합니다.
"""

import json
import subprocess
import sys
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from tqdm import tqdm
import argparse

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    DATASET_CONFIG, QUALITY_METRICS, RAW_DIR, FILTERED_DIR, LOGS_DIR,
    CLAUDE_CMD, MAX_RETRIES
)


@dataclass
class QualityScore:
    """품질 점수 데이터 클래스"""
    empathy: float = 0.0
    professionalism: float = 0.0
    therapeutic_technique: float = 0.0
    flow_naturalness: float = 0.0
    safety: float = 0.0
    total: float = 0.0
    passed: bool = False
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class QualityFilter:
    """품질 필터링 클래스"""

    def __init__(self, use_ai_evaluation: bool = True):
        self.use_ai_evaluation = use_ai_evaluation
        self.stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "by_category": {},
            "score_distribution": []
        }

    def rule_based_check(self, conversation: Dict) -> Tuple[bool, List[str]]:
        """규칙 기반 기본 검증"""
        issues = []
        conv_data = conversation.get("conversation", [])

        # 1. 턴 수 검증
        turns = len([t for t in conv_data if t.get("speaker") == "counselor"])
        if turns < DATASET_CONFIG.min_turns:
            issues.append(f"턴 수 부족: {turns} < {DATASET_CONFIG.min_turns}")
        if turns > DATASET_CONFIG.max_turns + 5:  # 약간의 여유
            issues.append(f"턴 수 초과: {turns} > {DATASET_CONFIG.max_turns}")

        # 2. 빈 응답 검증
        for turn in conv_data:
            if not turn.get("text", "").strip():
                issues.append("빈 응답 존재")
                break

        # 3. 금지 표현 검사
        forbidden_patterns = [
            r"저는 AI입니다",
            r"저는 인공지능",
            r"ChatGPT",
            r"GPT-\d",
            r"Claude",
            r"언어 모델",
            r"프로그래밍",
            r"코딩",
        ]

        full_text = " ".join([t.get("text", "") for t in conv_data])
        for pattern in forbidden_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                issues.append(f"금지 표현 발견: {pattern}")

        # 4. 언어 일관성 (한국어 비율)
        korean_chars = len(re.findall(r'[가-힣]', full_text))
        total_chars = len(re.findall(r'\w', full_text))
        if total_chars > 0 and korean_chars / total_chars < 0.7:
            issues.append("한국어 비율 낮음")

        # 5. 상담사 응답 길이 검증
        counselor_responses = [t.get("text", "") for t in conv_data if t.get("speaker") == "counselor"]
        avg_length = sum(len(r) for r in counselor_responses) / max(len(counselor_responses), 1)
        if avg_length < 20:
            issues.append(f"상담사 응답 평균 길이 너무 짧음: {avg_length:.1f}")

        # 6. 대화 구조 검증 (교대로 진행되는지)
        speakers = [t.get("speaker") for t in conv_data]
        for i in range(len(speakers) - 1):
            if speakers[i] == speakers[i + 1]:
                # 연속 발화는 허용하되 3회 이상 연속은 문제
                count = 1
                for j in range(i + 1, len(speakers)):
                    if speakers[j] == speakers[i]:
                        count += 1
                    else:
                        break
                if count >= 3:
                    issues.append("비정상적인 대화 구조 (연속 발화)")
                    break

        return len(issues) == 0, issues

    def ai_evaluate(self, conversation: Dict) -> QualityScore:
        """AI 기반 품질 평가"""
        conv_text = self._format_conversation(conversation)

        prompt = f"""다음 심리상담 대화의 품질을 평가해주세요.

## 대화 내용
{conv_text}

## 평가 기준 (각 0.0~1.0 점수)
1. empathy (공감): 상담사가 내담자의 감정을 잘 이해하고 반영하는가
2. professionalism (전문성): 전문적이고 윤리적인 태도를 유지하는가
3. therapeutic_technique (상담 기법): 적절한 상담 기법을 사용하는가
4. flow_naturalness (자연스러움): 대화가 자연스럽게 흘러가는가
5. safety (안전성): 위험한 조언이나 부적절한 내용이 없는가

## 출력 형식 (JSON만 출력)
```json
{{
    "empathy": 0.0,
    "professionalism": 0.0,
    "therapeutic_technique": 0.0,
    "flow_naturalness": 0.0,
    "safety": 0.0,
    "issues": ["발견된 문제점들"]
}}
```

JSON만 출력하세요."""

        try:
            result = subprocess.run(
                [CLAUDE_CMD, "-p", prompt, "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                scores = self._extract_scores(result.stdout)
                return scores
        except Exception as e:
            print(f"AI 평가 오류: {e}")

        # 기본 점수 반환
        return QualityScore(
            empathy=0.5, professionalism=0.5,
            therapeutic_technique=0.5, flow_naturalness=0.5,
            safety=0.5, total=0.5, passed=False,
            issues=["AI 평가 실패"]
        )

    def _format_conversation(self, conversation: Dict) -> str:
        """대화를 텍스트로 포맷"""
        lines = []
        for turn in conversation.get("conversation", [])[:20]:  # 처음 20턴만
            speaker = "내담자" if turn.get("speaker") == "client" else "상담사"
            text = turn.get("text", "")[:200]  # 길이 제한
            lines.append(f"{speaker}: {text}")
        return "\n".join(lines)

    def _extract_scores(self, text: str) -> QualityScore:
        """AI 응답에서 점수 추출"""
        try:
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                text = text[start:end].strip()

            data = json.loads(text)

            score = QualityScore(
                empathy=float(data.get("empathy", 0.5)),
                professionalism=float(data.get("professionalism", 0.5)),
                therapeutic_technique=float(data.get("therapeutic_technique", 0.5)),
                flow_naturalness=float(data.get("flow_naturalness", 0.5)),
                safety=float(data.get("safety", 0.5)),
                issues=data.get("issues", [])
            )

            # 가중 평균 계산
            weights = QUALITY_METRICS.weights
            score.total = (
                score.empathy * weights["empathy"] +
                score.professionalism * weights["professionalism"] +
                score.therapeutic_technique * weights["therapeutic_technique"] +
                score.flow_naturalness * weights["flow_naturalness"] +
                score.safety * weights["safety"]
            )

            score.passed = score.total >= DATASET_CONFIG.min_quality_score

            return score

        except Exception as e:
            return QualityScore(
                empathy=0.5, professionalism=0.5,
                therapeutic_technique=0.5, flow_naturalness=0.5,
                safety=0.5, total=0.5, passed=False,
                issues=[f"점수 추출 오류: {str(e)}"]
            )

    def evaluate_conversation(self, conversation: Dict) -> Tuple[QualityScore, bool]:
        """대화 품질 종합 평가"""
        # 1. 규칙 기반 검증
        rule_passed, rule_issues = self.rule_based_check(conversation)

        if not rule_passed:
            return QualityScore(
                passed=False,
                issues=rule_issues
            ), False

        # 2. AI 평가 (옵션)
        if self.use_ai_evaluation:
            score = self.ai_evaluate(conversation)
            score.issues.extend(rule_issues)
            return score, score.passed
        else:
            # 규칙 기반만 사용
            return QualityScore(
                empathy=0.7, professionalism=0.7,
                therapeutic_technique=0.7, flow_naturalness=0.7,
                safety=0.7, total=0.7, passed=True,
                issues=rule_issues
            ), True

    def process_file(self, filepath: Path) -> Tuple[bool, QualityScore]:
        """단일 파일 처리"""
        with open(filepath, 'r', encoding='utf-8') as f:
            conversation = json.load(f)

        score, passed = self.evaluate_conversation(conversation)

        if passed:
            # 필터링 통과 시 복사
            category = conversation.get("seed_info", {}).get("category", "unknown")
            dest_dir = FILTERED_DIR / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / filepath.name

            # 품질 점수 추가
            conversation["quality_score"] = {
                "empathy": score.empathy,
                "professionalism": score.professionalism,
                "therapeutic_technique": score.therapeutic_technique,
                "flow_naturalness": score.flow_naturalness,
                "safety": score.safety,
                "total": score.total
            }

            with open(dest_path, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)

        return passed, score

    def filter_all(self, ai_eval: bool = False):
        """모든 raw 데이터 필터링"""
        self.use_ai_evaluation = ai_eval

        print("=" * 60)
        print("품질 필터링 시작")
        print(f"AI 평가 사용: {ai_eval}")
        print("=" * 60)

        for category in ["adolescent", "adult", "crisis"]:
            cat_dir = RAW_DIR / category
            if not cat_dir.exists():
                continue

            files = list(cat_dir.glob("*.json"))
            if not files:
                continue

            print(f"\n[{category}] {len(files)}개 파일 처리 중...")

            self.stats["by_category"][category] = {"total": 0, "passed": 0, "failed": 0}

            for filepath in tqdm(files, desc=category):
                self.stats["total"] += 1
                self.stats["by_category"][category]["total"] += 1

                passed, score = self.process_file(filepath)

                if passed:
                    self.stats["passed"] += 1
                    self.stats["by_category"][category]["passed"] += 1
                else:
                    self.stats["failed"] += 1
                    self.stats["by_category"][category]["failed"] += 1

                self.stats["score_distribution"].append(score.total)

        self._print_summary()

    def _print_summary(self):
        """결과 요약"""
        print("\n" + "=" * 60)
        print("필터링 완료")
        print("=" * 60)
        print(f"총 처리: {self.stats['total']}")
        print(f"통과: {self.stats['passed']} ({self.stats['passed']/max(self.stats['total'],1)*100:.1f}%)")
        print(f"탈락: {self.stats['failed']}")

        print("\n카테고리별 결과:")
        for cat, cat_stats in self.stats["by_category"].items():
            total = cat_stats["total"]
            passed = cat_stats["passed"]
            rate = passed / max(total, 1) * 100
            print(f"  - {cat}: {passed}/{total} ({rate:.1f}%)")

        if self.stats["score_distribution"]:
            scores = self.stats["score_distribution"]
            avg = sum(scores) / len(scores)
            print(f"\n평균 품질 점수: {avg:.3f}")

        # 통계 저장
        stats_file = LOGS_DIR / f"filter_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # score_distribution은 저장에서 제외 (너무 큼)
        save_stats = {k: v for k, v in self.stats.items() if k != "score_distribution"}
        save_stats["avg_score"] = sum(self.stats["score_distribution"]) / max(len(self.stats["score_distribution"]), 1)

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(save_stats, f, ensure_ascii=False, indent=2)

        print(f"\n통계 저장: {stats_file}")


def main():
    parser = argparse.ArgumentParser(description="대화 품질 필터링")
    parser.add_argument(
        "--ai-eval",
        action="store_true",
        help="AI 기반 평가 사용 (느리지만 정확)"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        choices=["adolescent", "adult", "crisis"],
        default=None,
        help="특정 카테고리만 처리"
    )

    args = parser.parse_args()

    filter_instance = QualityFilter(use_ai_evaluation=args.ai_eval)

    if args.category:
        # 특정 카테고리만 처리
        cat_dir = RAW_DIR / args.category
        if cat_dir.exists():
            files = list(cat_dir.glob("*.json"))
            print(f"[{args.category}] {len(files)}개 파일 처리")
            for filepath in tqdm(files):
                filter_instance.process_file(filepath)
    else:
        filter_instance.filter_all(ai_eval=args.ai_eval)


if __name__ == "__main__":
    main()
