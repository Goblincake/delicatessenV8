@echo off
echo Ensuring Flask runs in development mode and restarting server...
echo Stopping any existing Flask server on port 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo Starting Flask dev server...
set "FLASK_ENV=development"
set "FLASK_DEBUG=1"
python app.py