"""
Claude Code를 사용한 대화 생성 스크립트
AIML API 대신 직접 Claude에게 대화 생성을 요청
"""
import json
import random
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
import sys

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from config import RAW_DIR, SEEDS_DIR


def load_seed_files(category: str) -> List[Dict]:
    """시드 파일 로드"""
    seeds = []

    # 카테고리 매핑
    category_map = {
        "adolescent": "청소년",
        "adult": "성인",
        "crisis": "위기대응"
    }

    korean_category = category_map.get(category, category)
    seed_dir = SEEDS_DIR / korean_category

    if not seed_dir.exists():
        return seeds

    # 모든 하위 디렉토리에서 시드 파일 로드
    for seed_file in seed_dir.rglob("seed_*.json"):
        try:
            with open(seed_file, 'r', encoding='utf-8') as f:
                seed_data = json.load(f)
                seeds.append(seed_data)
        except Exception as e:
            print(f"⚠️  시드 파일 로드 실패: {seed_file} - {e}")

    return seeds


def create_generation_prompt(seed: Dict, category: str) -> str:
    """대화 생성 프롬프트 생성"""

    # 시드에서 정보 추출
    client_profile = seed.get('client_profile', {})
    topic = seed.get('topic', '일반 상담')
    sample_conversation = seed.get('conversation', [])

    prompt = f"""당신은 전문 심리상담사입니다. 아래 정보를 바탕으로 자연스러운 한국어 심리상담 대화를 생성해주세요.

**내담자 정보:**
- 나이: {client_profile.get('age', '정보 없음')}
- 성별: {client_profile.get('gender', '정보 없음')}
- 직업: {client_profile.get('occupation', '정보 없음')}
- 배경: {client_profile.get('background', '정보 없음')}

**상담 주제:** {topic}

**요구사항:**
1. 25-40턴의 자연스러운 상담 대화를 생성하세요
2. 각 상담사 턴에는 사용된 상담 기법을 명시하세요
3. 내담자는 처음에 소극적이다가 점차 마음을 열어가는 과정을 보여주세요
4. 상담사는 공감, 경청, 적절한 질문을 통해 내담자를 돕습니다
5. 대화는 자연스럽고 현실적이어야 합니다

**사용 가능한 상담 기법:**
- rapport_building (관계 형성)
- empathy (공감)
- reflection (반영)
- open_ended_question (개방형 질문)
- validation (타당화)
- exploring (탐색)
- emotion_exploration (감정 탐색)
- encouragement (격려)
- collaborative_approach (협력적 접근)
- solution_focused (해결 중심)
- normalization (정상화)
- homework_assignment (과제 부여)
- support (지지)
- restatement (재진술)
- clarification (명료화)
- summarization (요약)
- interpretation (해석)
- information_giving (정보 제공)
- goal_setting (목표 설정)
- structuring (구조화)

**출력 형식 (JSON):**
{{
  "conversation_id": "ADO_YYYYMMDD_XXX" 형식의 고유 ID,
  "category": "{category}",
  "persona": {{
    "age": 숫자 또는 "N세",
    "gender": "남성" 또는 "여성",
    "occupation": "직업"
  }},
  "situation": "내담자의 상황을 1-2 문장으로 요약",
  "conversation": [
    {{
      "speaker": "client",
      "text": "대화 내용",
      "turn": 1
    }},
    {{
      "speaker": "counselor",
      "text": "대화 내용",
      "turn": 2,
      "technique": "사용된 기법"
    }},
    ...
  ]
}}

**중요:**
- JSON 형식을 정확히 지켜주세요
- conversation_id는 고유해야 합니다
- 각 턴의 대화는 자연스럽고 현실적이어야 합니다
- 상담사의 모든 턴에는 technique 필드가 있어야 합니다

이제 위 정보를 바탕으로 새로운 상담 대화를 JSON 형식으로 생성해주세요. JSON만 출력하고 다른 설명은 필요 없습니다."""

    return prompt


def save_conversation(conversation_data: Dict, category: str, index: int) -> Path:
    """대화를 파일로 저장"""
    output_dir = RAW_DIR / category
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"conv_{category}_{index:06d}.json"

    # 메타데이터 추가
    conversation_data['metadata'] = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'model': 'claude-sonnet-4-5',
        'seed_category': category,
        'generator': 'claude_code_direct'
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(conversation_data, f, ensure_ascii=False, indent=2)

    return output_file


def main():
    """메인 함수"""
    print("=" * 70)
    print("Claude Code 직접 생성 모드")
    print("=" * 70)

    # 현재 파일 개수 확인
    categories = {
        "adolescent": {"target": 5390, "current": 0},
        "adult": {"target": 3920, "current": 0},
        "crisis": {"target": 490, "current": 0}
    }

    for cat in categories:
        cat_dir = RAW_DIR / cat
        if cat_dir.exists():
            current_count = len(list(cat_dir.glob("conv_*.json")))
            categories[cat]["current"] = current_count

    print(f"\n📁 현재 상태:")
    for cat, info in categories.items():
        remaining = info["target"] - info["current"]
        print(f"  - {cat}: {info['current']}/{info['target']} (남은 개수: {remaining})")

    print("\n" + "=" * 70)
    print("프롬프트가 준비되었습니다.")
    print("Claude Code에서 이 프롬프트를 사용해 대화를 생성하세요.")
    print("=" * 70)


if __name__ == "__main__":
    main()
