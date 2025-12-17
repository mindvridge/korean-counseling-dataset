@echo off
chcp 65001 > nul
REM Windows - Real-time monitoring script

echo ========================================================================
echo Korean Counseling Dataset Generation (Real-time Monitoring)
echo ========================================================================
echo Start time: %date% %time%
echo.
echo Real-time progress will be displayed
echo To stop: Ctrl+C
echo ========================================================================
echo.

REM Create logs directory
if not exist logs mkdir logs

REM Set API key
set AIMLAPI_API_KEY=a899ee6960e64af39eade8b5e37dd1e8

REM Set Python encoding
set PYTHONIOENCODING=utf-8

REM Run Python script (real-time display)
python scripts\generate_batch.py --batch-size 100 --checkpoint 1000 --total 9800

echo.
echo ========================================================================
echo Process completed
echo ========================================================================
pause
