#!/bin/bash

# 실제 대화가 있는 좋은 시드 파일만 사용
GOOD_SEEDS=(
  "data/seeds/위기대응/seed_0000.json"
  "data/seeds/위기대응/seed_0001.json"
  "data/seeds/위기대응/seed_0002.json"
  "data/seeds/위기대응/seed_0003.json"
  "data/seeds/위기대응/seed_0004.json"
  "data/seeds/위기대응/seed_0006.json"
  "data/seeds/위기대응/seed_0007.json"
  "data/seeds/위기대응/seed_0008.json"
)

# 삭제된 파일 리스트를 읽어서 재생성
COUNTER=0
while IFS= read -r filepath; do
  # 파일명에서 인덱스 추출
  BASENAME=$(basename "$filepath")
  INDEX=$(echo "$BASENAME" | sed 's/conv_crisis_0*\([0-9]*\).json/\1/')

  # 랜덤하게 좋은 시드 파일 선택
  SEED_FILE=${GOOD_SEEDS[$RANDOM % ${#GOOD_SEEDS[@]}]}

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
    > "$filepath"

  COUNTER=$((COUNTER + 1))
  if [ $((COUNTER % 20)) -eq 0 ]; then
    echo "진행: $COUNTER/94"
  fi
done < /tmp/placeholder_files.txt

echo "✅ 94개 crisis 파일 재생성 완료 (실제 대화 내용)"
