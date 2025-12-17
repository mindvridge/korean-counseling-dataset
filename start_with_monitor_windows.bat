@echo off
chcp 65001 > nul
REM Windows용 실시간 모니터링 스크립트

echo ========================================================================
echo 한국어 심리상담 데이터셋 생성 시작 (실시간 모니터링)
echo ========================================================================
echo 시작 시간: %date% %time%
echo.
echo 실시간 진행 상황이 화면에 표시됩니다
echo 중단하려면: Ctrl+C
echo ========================================================================
echo.

REM 로그 디렉토리 생성
if not exist logs mkdir logs

REM API 키 설정
set AIMLAPI_API_KEY=a899ee6960e64af39eade8b5e37dd1e8

REM Python 인코딩 설정
set PYTHONIOENCODING=utf-8

REM Python 스크립트 직접 실행 (화면에 실시간 표시)
python scripts\generate_batch.py --batch-size 100 --checkpoint 1000 --total 9800

echo.
echo ========================================================================
echo 프로세스가 종료되었습니다
echo ========================================================================
pause
