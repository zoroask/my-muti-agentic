@echo off
REM Copies the TCG Coach agents and skill into this project's .claude folder.
REM Run once from the repo root (double-click works).
cd /d "%~dp0"
if not exist ".claude\agents" mkdir ".claude\agents"
if not exist ".claude\skills" mkdir ".claude\skills"
copy /Y "claude-config\agents\*.md" ".claude\agents\" >nul
REM Skills are folders (<name>\SKILL.md); remove flat copies left by older installs.
del /Q ".claude\skills\*.md" 2>nul
xcopy /E /I /Y /Q "claude-config\skills" ".claude\skills" >nul
echo TCG Coach installed:
dir /b ".claude\agents" ".claude\skills"
pause
