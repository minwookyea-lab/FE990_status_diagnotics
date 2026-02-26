
@echo off
pushd %~dp0
set FE990_PORT=COM9
set FE990_UPTIME_CMD=AT#UPTIME=0
set FE990_CLI_PATH=python cli_tool.py
python cli_tool.py --action uptime --port %FE990_PORT% --cmd "%FE990_UPTIME_CMD%"
