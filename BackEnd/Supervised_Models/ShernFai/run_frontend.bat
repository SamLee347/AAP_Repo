@echo off
echo Starting Sales Forecast System - LSFModel3...
echo.

REM Check if Flask is installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing Flask...
    pip install flask
)

echo.
echo Starting Flask server...
echo Frontend will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python app_new.py
