@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul || (echo Please install Python 3 on this BUILD computer.& pause & exit /b 1)
py -3 -m pip install --upgrade pyinstaller || (pause & exit /b 1)
py -3 -m PyInstaller --noconfirm --clean --onedir --console --name TreasureTracker --add-data "app\dashboard.html;." --add-data "app\overlay.html;." --add-data "app\pirate-theme.png;." app\app.py || (pause & exit /b 1)
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (echo Install Inno Setup 6 from jrsoftware.org first.& pause & exit /b 1)
"%ISCC%" "installer\TreasureTracker.iss" || (pause & exit /b 1)
echo.
echo READY: output\TreasureTrackerSetup.exe
pause
