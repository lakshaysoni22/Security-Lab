@echo off
rem LEAtTrace Automated Backup & Disaster Recovery for Windows Command Line
set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_DIR=%~dp0archives
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

set ARCHIVE_PATH=%BACKUP_DIR%\LEAtTrace_backup_%TIMESTAMP%.zip
echo === LEAtTrace Backup Sequence Initiated: %TIMESTAMP% ===

if exist "%~dp0..\..\backend\LEAtTrace.db" (
    echo [1/2] Creating safe online backup copy of SQLite database via python...
    if exist "%~dp0LEAtTrace_temp.db" del "%~dp0LEAtTrace_temp.db"
    python -c "import sqlite3; con = sqlite3.connect(r'%~dp0..\..\backend\LEAtTrace.db'); bck = sqlite3.connect(r'%~dp0LEAtTrace_temp.db'); con.backup(bck); bck.close(); con.close(); print('Safe copy created.')"
    
    echo Archiving staging files...
    powershell "Compress-Archive -Path '%~dp0LEAtTrace_temp.db' -DestinationPath '%ARCHIVE_PATH%' -Force"
    if exist "%~dp0LEAtTrace_temp.db" del "%~dp0LEAtTrace_temp.db"
) else (
    echo [1/2] Local SQLite database file not found.
)

echo [2/2] Calculating SHA-256 Checksum Signature...
powershell "(Get-FileHash -Path '%ARCHIVE_PATH%' -Algorithm SHA256).Hash" > "%ARCHIVE_PATH%.sha256"
echo === Backup Sequence Completed Successfully ===
echo Archive created: %ARCHIVE_PATH%
