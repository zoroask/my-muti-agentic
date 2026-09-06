@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

if /i "%~1"=="/silent" goto :silent_search
if /i "%~1"=="/setup" goto :setup

python tui_dashboard.py
goto :end

:setup
echo n| python setup.py
echo.
echo Setup finished - check the output above for any warnings.
pause
goto :end

:silent_search
rem For Windows Task Scheduler: run.bat /silent
echo Run started: %date% %time% >> scheduler_run.log
python job_scheduler.py --once >> scheduler_run.log 2>&1
echo Run finished: %date% %time% >> scheduler_run.log
echo. >> scheduler_run.log
goto :end

:end
exit /b 0
