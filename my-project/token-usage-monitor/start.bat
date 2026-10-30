@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>&1 || (echo Python not found. & goto :fail)

if not exist backend\.venv\Scripts\python.exe python -m venv backend\.venv || goto :fail
if not exist backend\.venv\Lib\site-packages\uvicorn (
  backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt || goto :fail
)

if not exist backend\dist\index.html (
  where npm >nul 2>&1 || (echo npm not found. & goto :fail)
  pushd frontend
  if not exist node_modules call npm install || (popd & goto :fail)
  call npm run build || (popd & goto :fail)
  popd
)

start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8000"
cd backend
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
exit /b 0

:fail
echo Setup failed. See messages above.
pause
exit /b 1
