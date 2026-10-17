@echo off
cd /d "%~dp0"
title AI Course and Career Advisor

REM ---------- 1. Find Python anywhere on this laptop ----------
if exist ".venv\setup_done.txt" goto run

set "PYCMD="
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if not errorlevel 1 set "PYCMD=python"
if defined PYCMD goto found

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"
if defined PYCMD goto found

for %%V in (311 312 310 313 314 39) do call :trydir "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
if defined PYCMD goto found
for %%V in (311 312 310 313 314 39) do call :trydir "%ProgramFiles%\Python%%V\python.exe"
if defined PYCMD goto found
for %%V in (311 312 310 313 314 39) do call :trydir "C:\Python%%V\python.exe"
if defined PYCMD goto found
call :trydir "%USERPROFILE%\anaconda3\python.exe"
if defined PYCMD goto found
call :trydir "%USERPROFILE%\miniconda3\python.exe"
if defined PYCMD goto found
call :trydir "%ProgramData%\anaconda3\python.exe"
if defined PYCMD goto found

echo.
echo  Could not find Python 3.9 or newer on this laptop.
echo  Install Python 3.11 from:
echo  https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
echo  On the first screen tick "Add python.exe to PATH", then run START.bat again.
echo.
pause
exit /b

:trydir
if defined PYCMD goto :eof
if exist %1 set "PYCMD=%~1"
goto :eof

:found
echo.
echo  Using Python: %PYCMD%

REM ---------- 2. Skip the Streamlit e-mail question ----------
if exist "%USERPROFILE%\.streamlit\credentials.toml" goto setup
mkdir "%USERPROFILE%\.streamlit" 2>nul
> "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
>> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""

REM ---------- 3. First-time setup ----------
:setup
echo.
echo  ===== FIRST-TIME SETUP: takes about 5 minutes. Please wait... =====
echo.
if exist ".venv" rmdir /s /q ".venv"
if "%PYCMD%"=="python" goto mkpy
if "%PYCMD%"=="py -3" goto mkpylauncher
"%PYCMD%" -m venv .venv
goto venvmade
:mkpy
python -m venv .venv
goto venvmade
:mkpylauncher
py -3 -m venv .venv
:venvmade
if not exist ".venv\Scripts\python.exe" goto setupfail
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto setupfail
echo  Installing vector database ChromaDB - optional, app works without it...
".venv\Scripts\python.exe" -m pip install chromadb
> ".venv\setup_done.txt" echo done
goto run

:setupfail
echo.
echo  Setup failed. Check your internet connection and run START.bat again.
echo  If it fails again, send a screenshot of this window.
pause
exit /b

REM ---------- 4. Run the app ----------
:run
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
  mkdir "%USERPROFILE%\.streamlit" 2>nul
  > "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
  >> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)
echo.
echo  ===== Starting the app. Your browser will open in a few seconds. =====
echo  ===== Keep this window open. Close it to stop the app.          =====
echo.
".venv\Scripts\python.exe" -m streamlit run app.py
pause
