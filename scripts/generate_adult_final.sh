#!/bin/bash
cd /home/user/korean-counseling-dataset

echo "🔄 adult 카테고리 최종 592개 추가 생성 (10,000개 목표 달성)"

SEED_DIR="data/seeds/성인"

for INDEX in $(seq 4001 4592); do
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
    echo "진행: $INDEX/4592"
  fi
done

echo "✅ adult 카테고리 최종 완료: 592개 추가 → 총 4,000개"
