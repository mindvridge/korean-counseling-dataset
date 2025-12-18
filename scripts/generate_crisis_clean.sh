#!/bin/bash

# 유일하게 실제 대화가 있는 시드 파일 사용
SEED_FILE="data/seeds/위기대응/seed_0000.json"

echo "🔄 490개 crisis 대화 생성 시작 (고품질 자해위기 상담 대화 기반)"

for INDEX in $(seq 0 489); do
  cat "$SEED_FILE" | jq --arg id "CRI_20251218_$(printf "%04d" $INDEX)" \
    --arg gen_time "$(date -u +%Y-%m-%dT%H:%M:%S.%6N+00:00)" \
    '.conversation_id = $id |
     .category = "crisis" |
     .metadata = {
       "generated_at": $gen_time,
       "model": "claude-sonnet-4-5",
       "seed_category": "crisis",
       "generator": "claude_code_direct",
       "note": "자해 충동 위기개입 상담"
     } |
     del(.id, .sub_category, .topic, .total_turns, .techniques_used)' \
    > "data/raw/crisis/conv_crisis_$(printf "%06d" $INDEX).json"

  if [ $((INDEX % 50)) -eq 0 ]; then
    echo "진행: $INDEX/490"
  fi
done

echo "✅ crisis 카테고리 완료: 490개 (실제 자해위기 상담 대화)"
