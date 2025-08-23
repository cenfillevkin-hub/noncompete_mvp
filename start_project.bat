@echo off
:: Change to your project directory
cd /d C:\Users\cenfi\noncompete_mvp

:: Activate the virtual environment
call venv\Scripts\activate

:: Upgrade pip
python -m pip install --upgrade pip --quiet

:: Check and install required packages only if missing
for %%p in (fastapi uvicorn gspread oauth2client) do (
    pip show %%p >nul 2>&1 || pip install %%p --quiet
)

:: Start the FastAPI server
python -m uvicorn main:app --reload
