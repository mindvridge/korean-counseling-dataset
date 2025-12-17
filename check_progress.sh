#!/bin/bash
#
# 데이터셋 생성 진행 상황 확인 스크립트
#

cd /home/user/korean-counseling-dataset

echo "========================================================================"
echo "한국어 심리상담 데이터셋 생성 진행 상황"
echo "========================================================================"
echo ""

# PID 확인
if [ -f logs/generation.pid ]; then
    PID=$(cat logs/generation.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 프로세스 실행 중 (PID: $PID)"
    else
        echo "❌ 프로세스가 종료되었습니다 (PID: $PID)"
    fi
else
    echo "⚠️  PID 파일이 없습니다"
fi

echo ""
echo "📊 파일 개수:"
echo "------------------------------------------------------------------------"

# 카테고리별 개수 확인
for category in adolescent adult crisis; do
    if [ -d "data/raw/$category" ]; then
        count=$(ls -1 data/raw/$category/conv_*.json 2>/dev/null | wc -l)
        echo "  - $category: $count개"
    fi
done

total=$(find data/raw -name "conv_*.json" 2>/dev/null | wc -l)
echo "  - 전체: $total개 / 9,800개 ($(echo "scale=1; $total * 100 / 9800" | bc)%)"

echo ""
echo "📝 최근 로그 (마지막 20줄):"
echo "------------------------------------------------------------------------"
if [ -f logs/generation_output.log ]; then
    tail -n 20 logs/generation_output.log
else
    echo "로그 파일이 없습니다"
fi

echo ""
echo "========================================================================"
echo "명령:"
echo "  - 실시간 로그: tail -f logs/generation_output.log"
echo "  - 프로세스 종료: ./stop_generation.sh"
echo "========================================================================"
