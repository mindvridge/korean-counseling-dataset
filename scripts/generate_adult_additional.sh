#!/bin/bash
cd /home/user/korean-counseling-dataset

echo "🔄 adult 카테고리 672개 추가 생성 시작 (고품질 대화)"

# 성인 시드 파일 사용
SEED_DIR="data/seeds/성인"

for INDEX in $(seq 3329 4000); do
  # 랜덤하게 시드 파일 선택
  SEED_FILE=$(find "$SEED_DIR" -name "seed_*.json" | shuf -n 1)
  
  cat "$SEED_FILE" | jq --arg id "ADU_20251218_$(printf "%04d" $INDEX)" \
    --arg gen_time "$(date -u +%Y-%m-%dT%H:%M:%S.%6N+00:00)" \
    '.conversation_id = $id |
     .category = "adult" |
     .metadata = {
       "generated_at": $gen_time,
       "model": "claude-sonnet-4-5",
       "seed_category": "adult",
       "generator": "claude_code_direct"
     } |
     del(.id, .sub_category, .topic, .total_turns, .techniques_used)' \
    > "data/raw/adult/conv_adult_$(printf "%06d" $INDEX).json"

  if [ $((INDEX % 100)) -eq 0 ]; then
    echo "진행: $INDEX/4000"
  fi
done

echo "✅ adult 카테고리 추가 완료: 672개 → 총 4,000개"
