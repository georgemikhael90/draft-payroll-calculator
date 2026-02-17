@echo off
setlocal
cd /d "%~dp0"

echo Installing/updating required packages...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install streamlit pandas numpy openpyxl pillow reportlab
if errorlevel 1 (
  echo.
  echo Failed to install dependencies. Please check Python and pip setup.
  pause
  exit /b 1
)

echo.
echo Starting Payroll Calculator...
python -m streamlit run main.py

endlocal
