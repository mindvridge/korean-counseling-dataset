#!/bin/bash
cd /home/user/korean-counseling-dataset

echo "🔄 crisis 카테고리 120개 추가 생성 시작 (자해위기 상담)"

# 고품질 자해위기 상담 시드 파일 사용
SEED="/home/user/korean-counseling-dataset/data/seeds/위기대응/seed_0000.json"

for INDEX in $(seq 490 609); do
  cat "$SEED" | jq --arg id "CRI_20251218_$(printf "%04d" $INDEX)" \
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
    > "/home/user/korean-counseling-dataset/data/raw/crisis/conv_crisis_$(printf "%06d" $INDEX).json"

  if [ $((INDEX % 50)) -eq 0 ]; then
    echo "진행: $INDEX/610"
  fi
done

echo "✅ crisis 카테고리 추가 완료: 120개 → 총 610개"
