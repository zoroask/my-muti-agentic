@echo off
REM Installs TCG Coach: copies agents and skills into .claude, downloads card data,
REM builds the card database (knowledge\gundam-gcg\tcg.db) and creates your personal folders.
REM Run once from the repo root (double-click works). Run again after any change in claude-config\.
cd /d "%~dp0"
if not exist ".claude\agents" mkdir ".claude\agents"
if not exist ".claude\skills" mkdir ".claude\skills"
copy /Y "claude-config\agents\*.md" ".claude\agents\" >nul
REM Skills are folders (<name>\SKILL.md); remove flat copies left by older installs.
del /Q ".claude\skills\*.md" 2>nul
xcopy /E /I /Y /Q "claude-config\skills" ".claude\skills" >nul
echo TCG Coach agents and skills installed:
dir /b ".claude\agents" ".claude\skills"
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or newer was not found. Install it from python.org, then run install.bat again.
  pause
  exit /b 1
)

REM Card details are not stored in the repo; they are downloaded from the official site.
if exist "knowledge\gundam-gcg\cards\cards.json" goto :build
echo Card data is not in the repo. It is downloaded from the official card site, about 25-45 minutes.
choice /C YN /M "Download card data now"
if errorlevel 2 goto :skipdata
python tools\refresh_cards.py
if errorlevel 1 (
  echo Card download failed. Check your internet connection and run install.bat again.
  pause
  exit /b 1
)

:build
echo Building the card database...
python tools\rebuild_all.py
if errorlevel 1 (
  echo Building the card database failed. See the error above.
  pause
  exit /b 1
)
goto :personal

:skipdata
echo Skipped. Run install.bat again later to download card data and build the database.

:personal
REM Personal files are git-ignored; create empty ones on first install.
if not exist "decks" mkdir "decks"
if not exist "logs" mkdir "logs"
if not exist "logs\match-log.csv" echo date,event,my_deck,opp_deck,game,went_first,result,notes> "logs\match-log.csv"
echo.
echo TCG Coach is ready. Run: claude
pause
