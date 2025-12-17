@echo off
chcp 65001 > nul
REM Windows - Parallel processing (10x faster)

echo ========================================================================
echo Korean Counseling Dataset Generation (PARALLEL MODE)
echo ========================================================================
echo Start time: %date% %time%
echo.
echo ⚡ Parallel workers: 10
echo 🚀 Expected speed: 10x faster
echo 📊 Estimated time: 1 day (instead of 10 days)
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

REM Run parallel script (10 workers)
python scripts\generate_batch_parallel.py --batch-size 100 --checkpoint 1000 --total 9800 --workers 10

echo.
echo ========================================================================
echo Process completed
echo ========================================================================
pause
