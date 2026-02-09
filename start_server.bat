@echo off
cd /d D:\Research\notification-discord
d:\Research\notification-discord\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
