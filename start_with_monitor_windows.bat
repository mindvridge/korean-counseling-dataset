@echo off
chcp 65001 > nul
REM Windows용 실시간 모니터링 스크립트

echo ========================================================================
echo 한국어 심리상담 데이터셋 생성 시작 (실시간 모니터링)
echo ========================================================================
echo 시작 시간: %date% %time%
echo.
echo 실시간 진행 상황이 화면에 표시됩니다
echo 중단하려면: Ctrl+C (프로세스는 계속 실행됨)
echo ========================================================================
echo.

REM 로그 디렉토리 생성
if not exist logs mkdir logs

REM 기존 로그 백업
if exist logs\generation_output.log (
    ren logs\generation_output.log generation_output_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
)

REM API 키 설정
set AIMLAPI_API_KEY=a899ee6960e64af39eade8b5e37dd1e8

REM Python 인코딩 설정
set PYTHONIOENCODING=utf-8

echo Python 스크립트 실행 중... (화면에 진행 상황 표시)
echo.
echo ========================================================================
echo.

REM Python 스크립트를 포그라운드로 실행하면서 로그에도 저장
REM PowerShell의 Tee-Object 기능 사용
powershell -Command "& { $env:AIMLAPI_API_KEY='a899ee6960e64af39eade8b5e37dd1e8'; $env:PYTHONIOENCODING='utf-8'; python scripts\generate_batch.py --batch-size 100 --checkpoint 1000 --total 9800 2>&1 | Tee-Object -FilePath logs\generation_output.log }"

echo.
echo ========================================================================
echo 프로세스가 종료되었습니다
echo 로그 파일: logs\generation_output.log
echo ========================================================================
pause
