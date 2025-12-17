@echo off
chcp 65001 > nul
REM Windows용 데이터셋 생성 스크립트

echo ========================================================================
echo 한국어 심리상담 데이터셋 생성 시작 (Windows)
echo ========================================================================
echo 시작 시간: %date% %time%
echo 로그 파일: logs\generation_output.log
echo.

REM 로그 디렉토리 생성
if not exist logs mkdir logs

REM API 키 설정
set AIMLAPI_API_KEY=a899ee6960e64af39eade8b5e37dd1e8

REM Python 인코딩 설정
set PYTHONIOENCODING=utf-8

echo 백그라운드에서 실행 중...
echo.

REM Python 스크립트 실행 (백그라운드)
start /B python scripts\generate_batch.py --batch-size 100 --checkpoint 1000 --total 9800 > logs\generation_output.log 2>&1

echo ========================================================================
echo 프로세스가 백그라운드에서 시작되었습니다!
echo.
echo 진행 상황 확인:
echo   - type logs\generation_output.log
echo   - check_progress_windows.bat
echo.
echo 프로세스 확인:
echo   - tasklist ^| findstr python
echo.
echo ========================================================================
pause
