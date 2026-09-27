@echo off
rem Turns the KILL switch off so the Trade Guardian protects trades normally again.
cd /d "%~dp0"
if exist KILL del KILL
if exist KILL.txt del KILL.txt
echo.
echo   KILL is OFF. The Guardian protects your trades normally again.
echo.
pause
