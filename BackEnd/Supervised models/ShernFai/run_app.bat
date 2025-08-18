@echo off
echo Starting Supply Chain Sales Prediction Flask App...
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Flask server...
echo The app will be available at http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.
python app.py
