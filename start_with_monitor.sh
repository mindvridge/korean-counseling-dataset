#!/bin/bash
#
# 진행 상황을 보면서 데이터셋 생성 실행
#
# 사용법: ./start_with_monitor.sh
# 화면에서 나가려면: Ctrl+C (백그라운드는 계속 실행됨)
#

cd /home/user/korean-counseling-dataset

# API 키 설정
export AIMLAPI_API_KEY='a899ee6960e64af39eade8b5e37dd1e8'

# 로그 디렉토리 생성
mkdir -p logs

# 기존 로그 백업
if [ -f logs/generation_output.log ]; then
    mv logs/generation_output.log logs/generation_output_$(date +%Y%m%d_%H%M%S).log
fi

echo "========================================================================"
echo "한국어 심리상담 데이터셋 생성 시작 (실시간 모니터링)"
echo "========================================================================"
echo "시작 시간: $(date)"
echo ""
echo "📺 실시간 진행 상황이 화면에 표시됩니다"
echo "💡 나가려면: Ctrl+C (백그라운드 작업은 계속됨)"
echo "========================================================================"
echo ""

# Python 스크립트를 백그라운드로 실행하면서 로그 파일에도 저장
python scripts/generate_batch.py \
    --batch-size 100 \
    --checkpoint 1000 \
    --total 9800 \
    2>&1 | tee logs/generation_output.log &

# PID 저장
echo $! > logs/generation.pid
echo "✅ 프로세스 시작됨 (PID: $(cat logs/generation.pid))"
echo ""

# 잠시 대기
sleep 2

# 실시간 로그 표시 (Ctrl+C로 종료 가능)
echo "========================================================================"
echo "📺 실시간 로그 (Ctrl+C로 나가기)"
echo "========================================================================"
echo ""

tail -f logs/generation_output.log
