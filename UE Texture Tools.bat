@echo off
cd /d "%~dp0"
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found in PATH! Install Python 3.x.
    pause & exit /b 1
)
python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo tkinter not found! Install Python with tkinter support.
    pause & exit /b 1
)
python -c "import tkinterdnd2" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing tkinterdnd2...
    pip install tkinterdnd2 -q
)
start "" pythonw ue_texture_tools.py 2>nul || start "" python ue_texture_tools.py
