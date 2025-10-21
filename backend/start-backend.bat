@echo off
echo Starting FastAPI Backend on Port 5003...
echo.

uvicorn app:app --host 0.0.0.0 --port 5003 --reload


