# 한국어 심리상담 AI 파인튜닝 데이터셋 생성기

한국어 심리상담 AI 모델 파인튜닝을 위한 고품질 멀티턴 대화 데이터셋을 생성하는 도구입니다.

## 목표

- **10,000개** 고품질 멀티턴 대화 데이터셋 생성
- 대화당 **25-35턴** 구성
- 카테고리 분포:
  - 청소년 상담 (adolescent): **55%**
  - 성인 상담 (adult): **40%**
  - 위기대응 (crisis): **5%**

## 디렉토리 구조

```
korean-counseling-dataset/
├── config.py              # 설정 파일
├── prompts/
│   ├── seed_prompt.txt    # 시드 생성 프롬프트
│   └── variation_prompt.txt  # 대화 생성 프롬프트
├── scripts/
│   ├── generate_seeds.py  # 시드 시나리오 생성
│   ├── generate_batch.py  # 대화 배치 생성
│   ├── quality_filter.py  # 품질 필터링
│   └── convert_format.py  # 포맷 변환
├── data/
│   ├── seeds/             # 시드 시나리오
│   ├── raw/               # 생성된 원본 대화
│   ├── filtered/          # 필터링된 대화
│   └── final/             # 최종 변환된 데이터셋
└── logs/                  # 로그 및 통계
```

## 사전 요구사항

- Python 3.8+
- Claude Code CLI 설치 및 인증 완료

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

### 1. 시드 시나리오 생성

각 카테고리별 상담 시나리오의 기초가 되는 시드를 생성합니다.

```bash
python scripts/generate_seeds.py
```

### 2. 대화 배치 생성

시드를 기반으로 멀티턴 상담 대화를 생성합니다.

```bash
# 전체 목표 수량 생성
python scripts/generate_batch.py

# 특정 배치 크기만 생성
python scripts/generate_batch.py --batch-size 100

# 특정 카테고리만 생성
python scripts/generate_batch.py --category adolescent

# 중단된 작업 재개
python scripts/generate_batch.py --resume
```

### 3. 품질 필터링

생성된 대화의 품질을 평가하고 기준에 미달하는 데이터를 필터링합니다.

```bash
# 규칙 기반 필터링 (빠름)
python scripts/quality_filter.py

# AI 기반 평가 포함 (느리지만 정확)
python scripts/quality_filter.py --ai-eval
```

### 4. 포맷 변환

필터링된 데이터를 다양한 파인튜닝 포맷으로 변환합니다.

```bash
# 모든 포맷으로 변환
python scripts/convert_format.py

# 특정 포맷만 변환
python scripts/convert_format.py --formats chatml alpaca
```

**지원 포맷:**
- `chatml`: OpenAI GPT 파인튜닝용 (messages 형식)
- `alpaca`: Alpaca 스타일 instruction 튜닝용
- `sharegpt`: ShareGPT 포맷 (LoRA 학습 등)
- `llama_chat`: LLaMA-2 Chat 템플릿 형식

## 설정 커스터마이징

`config.py`에서 다양한 설정을 조정할 수 있습니다:

```python
# 데이터셋 크기
total_conversations = 10000

# 턴 수 범위
min_turns = 25
max_turns = 35

# 카테고리 비율
category_ratios = {
    "adolescent": 0.55,
    "adult": 0.40,
    "crisis": 0.05
}

# 품질 기준
min_quality_score = 0.7
```

## 품질 평가 기준

### 필수 요소
- 공감적 반응
- 개방형 질문
- 감정 반영
- 적절한 경계 설정
- 전문적 태도

### 평가 지표 (가중치)
- 공감 (empathy): 25%
- 전문성 (professionalism): 20%
- 상담 기법 (therapeutic_technique): 20%
- 자연스러움 (flow_naturalness): 15%
- 안전성 (safety): 20%

## 상담 주제

### 청소년 상담
- 학업 스트레스와 성적 압박
- 또래 관계 및 학교 폭력
- 부모님과의 갈등
- 진로 고민과 미래 불안
- 자아정체성 혼란 등

### 성인 상담
- 직장 내 스트레스와 번아웃
- 대인관계 어려움
- 연애/결혼 문제
- 가족 갈등
- 우울감과 무기력 등

### 위기대응
- 자해 충동
- 극심한 우울감
- 공황 발작
- 트라우마 플래시백
- 급성 스트레스 반응

## 라이선스

연구 및 교육 목적으로 사용 가능합니다.

## 주의사항

- 생성된 데이터는 AI가 만든 합성 데이터입니다.
- 실제 상담 서비스를 대체할 수 없습니다.
- 위기 상황에서는 전문 상담 기관에 연락하세요.
  - 자살예방상담전화: 1393
  - 정신건강위기상담전화: 1577-0199
