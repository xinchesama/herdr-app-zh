@echo off
cd /d "%~dp0.."
python src\apply_zh.py %*
pause
