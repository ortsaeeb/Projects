@echo off
rem KILL switch for the Trade Guardian: sells every option position, then keeps selling new ones until UNKILL.bat.
cd /d "%~dp0"
echo.
echo   KILL SWITCH
echo   The Trade Guardian will SELL EVERY OPTION POSITION within about 5 seconds,
echo   and sell anything else you buy today until you run UNKILL.bat.
echo.
if not exist logs\guard.lock echo   WARNING: the Guardian does not seem to be running. KILL only works while its window is open.
if not exist logs\guard.lock echo   Start it with Start Guardian, or sell in the Webull app.
if not exist logs\guard.lock echo.
choice /c YN /m "  Sell everything now"
if errorlevel 2 goto cancel
type nul > KILL
echo.
echo   KILL is ON. Watch the Guardian window for CLOSED lines.
echo   Double-click UNKILL.bat to trade normally again.
goto done
:cancel
echo.
echo   Cancelled. Nothing was changed.
:done
echo.
pause
