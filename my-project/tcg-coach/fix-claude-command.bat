@echo off
REM Makes the "claude" command work in PowerShell / CMD (Claude Code CLI).
REM 1) If Claude Code is already installed but not on PATH, adds its folder to your user PATH.
REM 2) If it is not installed, runs the official installer: https://claude.ai/install.ps1
REM Nothing needs administrator rights. Close this window when it says DONE, then open a NEW terminal.
setlocal
set "CLAUDE_DIR=%USERPROFILE%\.local\bin"

if exist "%CLAUDE_DIR%\claude.exe" (
  echo Claude Code is installed at %CLAUDE_DIR%
) else (
  echo Claude Code not found - running the official installer from https://claude.ai/install.ps1 ...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"
)

if not exist "%CLAUDE_DIR%\claude.exe" (
  echo.
  echo Could not find claude.exe after installing. Please copy any error above and send it to Claude.
  pause
  exit /b 1
)

REM Add the folder to the USER PATH only if it is missing (no admin rights, no length truncation).
powershell -NoProfile -Command "$d=[Environment]::ExpandEnvironmentVariables('%CLAUDE_DIR%'); $p=[Environment]::GetEnvironmentVariable('Path','User'); if (-not $p) {$p=''}; if (($p -split ';') -notcontains $d) { [Environment]::SetEnvironmentVariable('Path', ($p.TrimEnd(';') + ';' + $d).TrimStart(';'), 'User'); 'Added to your PATH: ' + $d } else { 'Already on your PATH: ' + $d }"

echo.
"%CLAUDE_DIR%\claude.exe" --version
echo.
echo DONE. Now close this window, open a NEW PowerShell window and run:
echo    cd D:\my-muti-agentic\my-project\tcg-coach
echo    .\install.bat
echo    claude
pause
