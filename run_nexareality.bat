@echo off
title NEXA REALITY
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Install Python 3.10 or newer from https://www.python.org/downloads/windows/
  echo During installation, enable "Add python.exe to PATH".
  pause
  exit /b 1
)
python nexareality.py
if errorlevel 1 (
  echo.
  echo Nexa Reality exited with an error. Read the message above.
  pause
)
