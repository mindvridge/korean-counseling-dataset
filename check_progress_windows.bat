@echo off
chcp 65001 > nul
REM Windows용 진행 상황 확인 스크립트

echo ========================================================================
echo 한국어 심리상담 데이터셋 생성 진행 상황 (Windows)
echo ========================================================================
echo.

REM 프로세스 확인
echo [프로세스 상태]
tasklist | findstr python
echo.

REM 파일 개수 확인
echo [파일 개수]
if exist data\raw\adolescent\ (
    for /f %%a in ('dir /b data\raw\adolescent\conv_*.json 2^>nul ^| find /c /v ""') do echo   - adolescent: %%a개
)
if exist data\raw\adult\ (
    for /f %%a in ('dir /b data\raw\adult\conv_*.json 2^>nul ^| find /c /v ""') do echo   - adult: %%a개
)
if exist data\raw\crisis\ (
    for /f %%a in ('dir /b data\raw\crisis\conv_*.json 2^>nul ^| find /c /v ""') do echo   - crisis: %%a개
)

echo.
echo [최근 로그 (마지막 20줄)]
echo ------------------------------------------------------------------------
if exist logs\generation_output.log (
    powershell -Command "Get-Content logs\generation_output.log -Tail 20"
) else (
    echo 로그 파일이 없습니다
)

echo.
echo ========================================================================
echo 명령:
echo   - 실시간 로그: powershell -Command "Get-Content logs\generation_output.log -Wait"
echo   - 프로세스 종료: taskkill /IM python.exe /F
echo ========================================================================
pause
