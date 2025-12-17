#!/bin/bash
#
# 데이터셋 생성 중단 스크립트
#

cd /home/user/korean-counseling-dataset

echo "========================================================================"
echo "데이터셋 생성 프로세스 중단"
echo "========================================================================"

if [ ! -f logs/generation.pid ]; then
    echo "❌ PID 파일이 없습니다"
    exit 1
fi

PID=$(cat logs/generation.pid)

if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  프로세스가 이미 종료되었습니다 (PID: $PID)"
    rm logs/generation.pid
    exit 0
fi

echo "프로세스 종료 중 (PID: $PID)..."
kill $PID

# 종료 대기
sleep 2

if ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  프로세스가 종료되지 않았습니다. 강제 종료 시도..."
    kill -9 $PID
    sleep 1
fi

if ! ps -p $PID > /dev/null 2>&1; then
    echo "✅ 프로세스가 성공적으로 종료되었습니다"
    rm logs/generation.pid
else
    echo "❌ 프로세스 종료 실패"
    exit 1
fi

echo ""
echo "현재까지 생성된 파일 개수:"
total=$(find data/raw -name "conv_*.json" 2>/dev/null | wc -l)
echo "  - 전체: $total개 / 9,800개"
echo ""
echo "재시작하려면: ./start_generation.sh"
echo "========================================================================"
