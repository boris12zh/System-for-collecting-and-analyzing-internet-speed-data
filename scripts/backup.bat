@echo off
setlocal
REM Usage: backup.bat [LABEL]   e.g.  backup.bat US03_complete
REM Creates backups\speed-tracker_LABEL_yyyy-MM-dd_HHmmss.zip (LABEL defaults to "backup").
cd /d "%~dp0\.."
set "LABEL=%~1"
if "%LABEL%"=="" set "LABEL=backup"
if not exist "backups" mkdir "backups"
REM Archive current source/docs/scripts, but never archive old backups or a venv.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$date=Get-Date -Format yyyy-MM-dd_HHmmss; $out=Join-Path (Resolve-Path 'backups') ('speed-tracker_%LABEL%_'+$date+'.zip'); Compress-Archive -Path 'src','tests','scripts','packaging','pyproject.toml','README.md','CONTRIBUTING.md','CHANGELOG.md','.gitignore' -DestinationPath $out; Write-Host ('Backup saved: '+$out)"
exit /b %ERRORLEVEL%
