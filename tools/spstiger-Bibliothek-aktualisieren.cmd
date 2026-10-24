@echo off
rem Startet das Update der spstiger-Komponentenbibliothek fuer Kinco DTools V4.
rem Parameter werden durchgereicht, z. B.:  spstiger-Bibliothek-aktualisieren.cmd -NurPruefen
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Update-spstigerBibliothek.ps1" %*
echo.
pause
