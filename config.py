"""
한국어 심리상담 AI 파인튜닝 데이터셋 생성 설정
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List

# 기본 경로 설정
BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"
SCRIPTS_DIR = BASE_DIR / "scripts"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# 데이터 하위 디렉토리
SEEDS_DIR = DATA_DIR / "seeds"
RAW_DIR = DATA_DIR / "raw"
FILTERED_DIR = DATA_DIR / "filtered"
FINAL_DIR = DATA_DIR / "final"


@dataclass
class DatasetConfig:
    """데이터셋 생성 설정"""

    # 목표 데이터셋 크기
    total_conversations: int = 10000

    # 대화당 턴 수 범위
    min_turns: int = 25
    max_turns: int = 35

    # 카테고리별 비율
    category_ratios: Dict[str, float] = field(default_factory=lambda: {
        "adolescent": 0.55,  # 청소년 (55%)
        "adult": 0.40,       # 성인 (40%)
        "crisis": 0.05       # 위기대응 (5%)
    })

    # 카테고리별 목표 수
    @property
    def category_targets(self) -> Dict[str, int]:
        return {
            cat: int(self.total_conversations * ratio)
            for cat, ratio in self.category_ratios.items()
        }

    # 배치 크기
    batch_size: int = 10

    # 품질 필터링 기준
    min_quality_score: float = 0.7

    # 시드 수 (카테고리당)
    seeds_per_category: int = 50

    # 세부 카테고리별 시드 분포 (200개 기준)
    seed_distribution: Dict[str, int] = field(default_factory=lambda: {
        "청소년_학업스트레스": 40,
        "청소년_또래관계": 30,
        "청소년_가족갈등": 20,
        "청소년_진로고민": 10,
        "청소년_정체성": 10,
        "성인_직장스트레스": 30,
        "성인_대인관계": 24,
        "성인_우울불안": 16,
        "성인_가족관계": 10,
        "위기대응": 10
    })


# 상담 기법 라벨 정의
COUNSELING_TECHNIQUES = [
    "반영(reflection)",
    "공감(empathy)",
    "개방형질문(open_question)",
    "폐쇄형질문(closed_question)",
    "명료화(clarification)",
    "요약(summarization)",
    "재진술(restatement)",
    "감정명명(emotion_labeling)",
    "타당화(validation)",
    "직면(confrontation)",
    "해석(interpretation)",
    "정보제공(information_giving)",
    "자기개방(self_disclosure)",
    "침묵(silence)",
    "격려(encouragement)",
    "구조화(structuring)",
    "즉시성(immediacy)",
    "목표설정(goal_setting)"
]


@dataclass
class CategoryConfig:
    """카테고리별 세부 설정"""

    # 청소년 상담 주제
    adolescent_topics: List[str] = field(default_factory=lambda: [
        "학업 스트레스와 성적 압박",
        "또래 관계 및 학교 폭력",
        "부모님과의 갈등",
        "진로 고민과 미래 불안",
        "자아정체성 혼란",
        "SNS/인터넷 중독",
        "외모 콤플렉스",
        "이성 관계 고민",
        "왕따/따돌림 경험",
        "가정환경 스트레스"
    ])

    # 성인 상담 주제
    adult_topics: List[str] = field(default_factory=lambda: [
        "직장 내 스트레스와 번아웃",
        "대인관계 어려움",
        "연애/결혼 문제",
        "가족 갈등",
        "우울감과 무기력",
        "불안과 공황",
        "자존감 저하",
        "경제적 어려움으로 인한 스트레스",
        "육아 스트레스",
        "중년 위기와 정체성"
    ])

    # 위기대응 상황
    crisis_topics: List[str] = field(default_factory=lambda: [
        "자해 충동",
        "극심한 우울감",
        "공황 발작",
        "트라우마 플래시백",
        "급성 스트레스 반응"
    ])


@dataclass
class QualityMetrics:
    """품질 평가 지표"""

    # 필수 요소
    required_elements: List[str] = field(default_factory=lambda: [
        "공감적 반응",
        "개방형 질문",
        "감정 반영",
        "적절한 경계 설정",
        "전문적 태도"
    ])

    # 금지 요소
    forbidden_elements: List[str] = field(default_factory=lambda: [
        "조언 강요",
        "판단적 언어",
        "비전문적 표현",
        "개인정보 요구",
        "부적절한 자기 개방"
    ])

    # 평가 기준 가중치
    weights: Dict[str, float] = field(default_factory=lambda: {
        "empathy": 0.25,
        "professionalism": 0.20,
        "therapeutic_technique": 0.20,
        "flow_naturalness": 0.15,
        "safety": 0.20
    })


# 기본 설정 인스턴스
DATASET_CONFIG = DatasetConfig()
CATEGORY_CONFIG = CategoryConfig()
QUALITY_METRICS = QualityMetrics()


# Claude Code 실행 설정
CLAUDE_CMD = "claude"  # Claude Code CLI 명령어
MAX_RETRIES = 3
RETRY_DELAY = 2  # 초
