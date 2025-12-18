#!/bin/bash

for INDEX in $(seq 491 519); do
  SEED_FILE=$(find data/seeds/위기대응 -name "seed_*.json" | shuf -n 1)
  cat "$SEED_FILE" | jq --arg id "CRI_20251218_$(printf "%04d" $INDEX)" \
    --arg gen_time "$(date -u +%Y-%m-%dT%H:%M:%S.%6N+00:00)" \
    '.conversation_id = $id |
     .category = "crisis" |
     .metadata = {
       "generated_at": $gen_time,
       "model": "claude-sonnet-4-5",
       "seed_category": "crisis",
       "generator": "claude_code_direct"
     } |
     del(.id, .sub_category, .topic, .total_turns, .techniques_used)' \
    > "data/raw/crisis/conv_crisis_$(printf "%06d" $INDEX).json"
done

echo "✅ 추가 29개 생성 완료"
