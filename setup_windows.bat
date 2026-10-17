@echo off
setlocal EnableExtensions
title Aura AI Assistant - Setup

echo.
echo  =====================================
echo       Aura AI Assistant - Setup
echo  =====================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python was not found.
        echo Install Python 3.11 or newer from https://www.python.org/downloads/windows/
        echo During setup, tick "Add python.exe to PATH", then run this file again.
        pause
        exit /b 1
    )
    set "PYTHON=python"
) else (
    set "PYTHON=py"
)

set "INSTALL_DIR=%USERPROFILE%\Aura-AI-Assistant"
set "ZIP_FILE=%TEMP%\Aura-AI-Assistant-main.zip"
set "EXTRACT_DIR=%TEMP%\Aura-AI-Assistant-main"

echo Installing Aura into:
echo %INSTALL_DIR%
echo.

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Downloading the latest Aura project from GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri 'https://github.com/Devajyoti-2004/Aura-AI-Assistant/archive/refs/heads/main.zip' -OutFile '%ZIP_FILE%'; exit 0 } catch { Write-Error $_; exit 1 }"
if errorlevel 1 (
    echo ERROR: Download failed. Check your internet connection and try again.
    pause
    exit /b 1
)

if exist "%EXTRACT_DIR%" rmdir /s /q "%EXTRACT_DIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP_FILE%' -DestinationPath '%TEMP%' -Force"
if errorlevel 1 (
    echo ERROR: Could not extract the project archive.
    pause
    exit /b 1
)

xcopy "%EXTRACT_DIR%\*" "%INSTALL_DIR%\" /E /I /Y >nul
if errorlevel 1 (
    echo ERROR: Could not copy the project files.
    pause
    exit /b 1
)

cd /d "%INSTALL_DIR%"
echo Creating a private Python environment...
%PYTHON% -m venv .venv
if errorlevel 1 (
    echo ERROR: Could not create the Python environment.
    echo Make sure Python 3.11 or newer is installed.
    pause
    exit /b 1
)

echo Updating pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: pip update failed; continuing with dependency installation.
)

echo Installing Aura dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Dependency installation failed. Check your internet connection.
    pause
    exit /b 1
)

if not exist ".env" if exist ".env.example" copy ".env.example" ".env" >nul

echo.
echo Setup complete.
echo.
echo To enable AI chat, open this file:
echo %INSTALL_DIR%\.env
echo Add your own OpenAI API key after OPENAI_API_KEY=
echo Leave it blank if you do not want optional AI chat.
echo.
echo Starting Aura now...
".venv\Scripts\python.exe" aura.py
if errorlevel 1 (
    echo.
    echo Aura closed with an error. If you need help, copy the error shown above.
    pause
)

endlocal
