@echo off
chcp 65001 >nul
echo ============================================
echo  KENT PLC Dashboard Updater
echo ============================================
echo.

echo [1/2] Updating dashboard from Excel...
python "%~dp0kentplc_dashboard.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to generate dashboard!
    pause
    exit /b 1
)

echo.
echo [2/2] Copying to index.html...
copy /Y "%~dp0KENTPLC_Completion_Dashboard.html" "%~dp0index.html" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to copy index.html!
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Dashboard updated successfully!
echo ============================================
echo.
echo Opening in browser...
start "" "%~dp0index.html"
echo.
pause
