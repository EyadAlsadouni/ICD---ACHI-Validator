@echo off
echo Starting React Frontend on Port 3004...
echo.

REM Set the PORT environment variable
set PORT=3004

REM Run react-scripts directly
node node_modules\react-scripts\bin\react-scripts.js start


