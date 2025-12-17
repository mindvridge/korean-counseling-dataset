#!/bin/bash
#
# 한국어 심리상담 데이터셋 생성 - 서버 독립 실행 스크립트
#
# 사용법:
#   ./start_generation.sh
#
# 실행 후 세션을 종료해도 계속 실행됩니다.
#

cd /home/user/korean-counseling-dataset

# API 키 설정 (환경변수)
export AIMLAPI_API_KEY='a899ee6960e64af39eade8b5e37dd1e8'

# 로그 디렉토리 생성
mkdir -p logs

echo "========================================================================"
echo "한국어 심리상담 데이터셋 생성 시작"
echo "========================================================================"
echo "시작 시간: $(date)"
echo "로그 파일: logs/generation_output.log"
echo "PID 파일: logs/generation.pid"
echo ""
echo "백그라운드에서 실행 중..."
echo "========================================================================"

# nohup으로 백그라운드 실행
nohup python scripts/generate_batch.py \
    --batch-size 100 \
    --checkpoint 1000 \
    --total 9800 \
    > logs/generation_output.log 2>&1 &

# PID 저장
echo $! > logs/generation.pid

echo "프로세스 ID: $(cat logs/generation.pid)"
echo ""
echo "✅ 백그라운드 실행 시작 완료!"
echo ""
echo "모니터링 명령:"
echo "  - 실시간 로그 보기: tail -f logs/generation_output.log"
echo "  - 프로세스 확인: ps -p \$(cat logs/generation.pid)"
echo "  - 프로세스 종료: kill \$(cat logs/generation.pid)"
echo ""
echo "진행 상황 확인:"
echo "  - ls -la data/raw/*/conv_*.json | wc -l"
echo "========================================================================"
