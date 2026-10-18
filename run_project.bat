@echo off
cd /d "%~dp0"
echo Starting Project Cost Estimation Tool and SPM Control Center...
echo Cost estimator: http://127.0.0.1:8000
echo SPM workspace:  http://127.0.0.1:8000/frontend/spm.html
python app.py
pause
