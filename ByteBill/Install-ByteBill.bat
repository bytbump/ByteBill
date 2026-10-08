@echo off
REM ============================================================
REM  Install ByteBill on this PC — NO admin needed, just double-click.
REM  Copies the app to your user folder, adds Desktop + Start Menu
REM  shortcuts and an Add/Remove Programs entry (uninstaller included).
REM  Run this from the ByteBill folder (extracted zip or dist\ByteBill).
REM ============================================================
setlocal
set APPDIR=%LocalAppData%\ByteBump\ByteBill
echo Installing ByteBill to %APPDIR% ...
mkdir "%APPDIR%" 2>nul
xcopy "%~dp0*" "%APPDIR%\" /E /I /Y >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$exe = \"$env:LocalAppData\ByteBump\ByteBill\ByteBill.exe\"; " ^
  "$s1 = $ws.CreateShortcut(\"$env:USERPROFILE\Desktop\ByteBill.lnk\"); " ^
  "$s1.TargetPath = $exe; $s1.WorkingDirectory = \"$env:LocalAppData\ByteBump\ByteBill\"; " ^
  "$s1.IconLocation = \"$exe,0\"; $s1.Save(); " ^
  "$sm = \"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\ByteBill\"; " ^
  "New-Item -ItemType Directory -Force -Path $sm | Out-Null; " ^
  "$s2 = $ws.CreateShortcut(\"$sm\ByteBill.lnk\"); " ^
  "$s2.TargetPath = $exe; $s2.WorkingDirectory = \"$env:LocalAppData\ByteBump\ByteBill\"; " ^
  "$s2.IconLocation = \"$exe,0\"; $s2.Save(); " ^
  "$s3 = $ws.CreateShortcut(\"$sm\Uninstall ByteBill.lnk\"); " ^
  "$s3.TargetPath = \"$env:LocalAppData\ByteBump\ByteBill\Uninstall.exe\"; $s3.Save()"

reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\ByteBill" /v DisplayName /d "ByteBill (by ByteBump)" /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\ByteBill" /v Publisher /d "ByteBump (Next Brain Mechatronics Pvt Ltd)" /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\ByteBill" /v DisplayVersion /d "1.0.0" /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\ByteBill" /v "UninstallString" /d "\"%APPDIR%\Uninstall.exe\"" /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\ByteBill" /v DisplayIcon /d "%APPDIR%\ByteBill.exe,0" /f >nul

echo.
echo ByteBill installed. Launch it from the Desktop icon.
echo To remove later: Settings - Apps - ByteBill - Uninstall (your bills are kept).
pause
