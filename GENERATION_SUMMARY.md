# 한국어 심리상담 데이터셋 생성 완료 보고서

## 📊 생성 개요

- **전체 생성 개수**: 9,800개
- **생성 일시**: 2025-12-17
- **생성 방식**: 10개 배치로 분할 생성

## 📈 카테고리별 분포

| 카테고리 | 개수 | 비율 | 목표 비율 | 달성도 |
|---------|------|------|----------|--------|
| 청소년 (adolescent) | 5,402개 | 55.1% | 55% | ✅ 100.2% |
| 성인 (adult) | 3,909개 | 39.9% | 40% | ✅ 99.8% |
| 위기대응 (crisis) | 489개 | 5.0% | 5% | ✅ 100.0% |
| **합계** | **9,800개** | **100%** | **100%** | ✅ **완료** |

## 📁 파일 구조

```
data/raw/
├── adolescent/
│   ├── conv_adolescent_000001.json
│   ├── conv_adolescent_000002.json
│   └── ... (총 5,402개)
├── adult/
│   ├── conv_adult_000001.json
│   ├── conv_adult_000002.json
│   └── ... (총 3,909개)
└── crisis/
    ├── conv_crisis_000001.json
    ├── conv_crisis_000002.json
    └── ... (총 489개)
```

## 💾 디스크 사용량

- 청소년(adolescent): 57MB
- 성인(adult): 40MB
- 위기대응(crisis): 5.0MB
- **전체**: 101MB

## 🎯 데이터 특징

### 대화 구조
- **대화 턴 수**: 25-35턴 (가변)
- **화자**: 내담자(client)와 상담자(counselor) 교대
- **언어**: 한국어

### 상담 기법
다음 10가지 이상의 전문 상담 기법 포함:
- empathy (공감)
- reflection (반영)
- validation (타당화)
- open_question (개방형 질문)
- emotion_labeling (감정 명명)
- goal_setting (목표 설정)
- confrontation (직면)
- information_giving (정보 제공)
- encouragement (격려)
- restatement (재진술)

### 메타데이터
각 대화 파일은 다음 정보를 포함:
- `metadata`: 카테고리, 주제, 총 턴 수, 품질 지표
- `seed_info`: 시드 파일 참조 정보
- `generated_at`: 생성 시각 (ISO 8601)
- `conversation`: 대화 내용 배열

## 📝 JSON 파일 형식 예시

```json
{
  "metadata": {
    "category": "adolescent",
    "topic": "전학 후 적응 어려움과 외로움",
    "total_turns": 26,
    "quality_indicators": ["empathy", "reflection", "validation", ...]
  },
  "seed_info": {
    "source_file": "data/seeds/청소년/또래관계/seed_0009.json",
    "category": "adolescent",
    "topic": "또래관계"
  },
  "generated_at": "2025-12-17T01:46:30.000Z",
  "conversation": [
    {
      "turn": 1,
      "speaker": "client",
      "text": "안녕하세요... 전학 온 지 한 달 됐는데 아직도 친구가 없어요."
    },
    {
      "turn": 1,
      "speaker": "counselor",
      "text": "안녕하세요. 전학 온 지 한 달이 됐는데 친구를 사귀기가 어려워서 오셨군요...",
      "technique": ["empathy", "reflection", "open_question"]
    },
    ...
  ]
}
```

## 🔄 생성 프로세스

### 배치별 생성 내역

| 배치 | 범위 | 개수 | 누적 | 진행률 |
|------|------|------|------|--------|
| 배치 1-7 | 1-1,880 | 1,880개 | 1,880개 | 19.2% |
| 배치 8 | 1,881-3,880 | 2,000개 | 3,880개 | 39.6% |
| 배치 9 | 3,881-6,800 | 2,920개 | 6,800개 | 69.4% |
| 배치 10 | 6,801-9,800 | 3,000개 | 9,800개 | 100% |

### 사용된 스크립트
- `scripts/generate_batch_8.py`
- `scripts/generate_batch_9.py`
- `scripts/generate_batch_10.py`
- `scripts/final_statistics.py`

## ✅ 품질 검증

### 샘플 파일 검증 결과
- ✓ conv_adolescent_000001.json: 26턴, 주제='전학 후 적응 어려움과 외로움'
- ✓ conv_adolescent_000004.json: 26턴, 주제='SNS 중독과 학업 병행 어려움'
- ✓ conv_crisis_009800.json: 32턴, 주제='급성 정신병적 증상'

### 검증 항목
- [x] 파일 개수 정확성 (9,800개)
- [x] 카테고리 분포 정확성 (55%/40%/5%)
- [x] JSON 구조 유효성
- [x] 메타데이터 완전성
- [x] 대화 턴 수 범위 (25-35턴)
- [x] 상담 기법 라벨링
- [x] UTF-8 인코딩

## 🎓 활용 방안

이 데이터셋은 다음 용도로 활용 가능합니다:
1. **AI 상담 챗봇 파인튜닝**
2. **상담 기법 분류 모델 학습**
3. **감정 분석 및 NLU 연구**
4. **한국어 대화 생성 모델 학습**
5. **심리상담 교육 자료**

## 📌 주요 주제

### 청소년 (adolescent)
- 학업 스트레스, 또래 관계, 가족 갈등
- 진로 선택, 정체성 혼란, SNS 중독
- 학교 폭력, 시험 불안, 외모 콤플렉스

### 성인 (adult)
- 직장 내 갈등, 워라밸, 번아웃
- 결혼/육아 스트레스, 경력 전환
- 경제적 압박, 부모 부양, 중년 위기

### 위기대응 (crisis)
- 자살 충동, 자해, 급성 불안
- 트라우마, 패닉 장애, PTSD
- 정신병적 증상, 대인관계 단절

## 🚀 다음 단계

- [ ] 데이터 품질 검수
- [ ] 추가 필터링 및 정제
- [ ] 파인튜닝 데이터 형식 변환
- [ ] 학습 데이터셋 분할 (train/val/test)
- [ ] 모델 학습 및 평가

---

**생성 완료일**: 2025-12-17
**생성 도구**: Claude Code
**참조 시드 데이터**: 200개 한국어 심리상담 시나리오
