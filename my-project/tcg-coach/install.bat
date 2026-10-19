@echo off
REM Copies the TCG Coach agents and skill into this project's .claude folder.
REM Run once from D:\my-muti-agentic\my-project\tcg-coach (double-click works).
cd /d "%~dp0"
if not exist ".claude\agents" mkdir ".claude\agents"
if not exist ".claude\skills" mkdir ".claude\skills"
copy /Y "claude-config\agents\*.md" ".claude\agents\" >nul
copy /Y "claude-config\skills\*.md" ".claude\skills\" >nul
echo TCG Coach installed:
dir /b ".claude\agents" ".claude\skills"
pause
