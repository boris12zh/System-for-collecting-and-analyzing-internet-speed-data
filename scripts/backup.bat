@echo off
setlocal
cd /d "%~dp0\.."
if not exist "backups" mkdir "backups"
REM Archive current source/docs/scripts, but never archive old backups or a venv.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$date=Get-Date -Format yyyy-MM-dd_HHmmss; $out=Join-Path (Resolve-Path 'backups') ('speed-tracker_US03_'+$date+'.zip'); Compress-Archive -Path 'src','tests','scripts','packaging','pyproject.toml','README.md','CONTRIBUTING.md','CHANGELOG.md' -DestinationPath $out; Write-Host ('Backup saved: '+$out)"
exit /b %ERRORLEVEL%
