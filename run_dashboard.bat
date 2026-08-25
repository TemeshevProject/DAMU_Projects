@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONPATH=%CD%
python -m streamlit run dashboard/app.py --browser.gatherUsageStats false
