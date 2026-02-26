@echo off
REM FE990 명령 실행 (관리자 권한)
REM 사용법: fe990_command.bat "FE990 꺼줘" 또는 fe990_command.bat "FE990 재부팅"
cd /d "%~dp0"
if "%~1"=="" (
    echo 사용법: fe990_command.bat "명령어"
    echo 예: fe990_command.bat "FE990 업타임 알려줘"
    echo 예: fe990_command.bat "FE990 꺼줘"
    echo 예: fe990_command.bat "FE990 재부팅"
    pause
) else (
    python natural.py "%~1"
    pause
)
