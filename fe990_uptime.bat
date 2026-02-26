@echo off
REM FE990 업타임 조회
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 관리자 권한으로 다시 실행합니다...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" ^& python fe990_uptime.py ^& pause' -Verb RunAs"
    exit /b
)

python fe990_uptime.py
pause
