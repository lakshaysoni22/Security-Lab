@echo off
rem LEAtTrace Automated Restore & Disaster Recovery for Windows Command Line
set ARCHIVE_PATH=%1
if "%ARCHIVE_PATH%"=="" (
    echo ERROR: Missing backup zip file parameter.
    echo Usage: restore.bat ^<path_to_backup_archive.zip^>
    exit /b 1
)

if not exist "%ARCHIVE_PATH%" (
    echo ERROR: Backup archive file not found: %ARCHIVE_PATH%
    exit /b 1
)

echo === LEAtTrace Restoration Sequence Initiated ===
python -c "import sys, os, hashlib, zipfile, shutil; zp = sys.argv[1]; sp = zp + '.sha256'; (expected := open(sp).read().strip().upper()) if os.path.exists(sp) else (expected := None); h = hashlib.sha256(); [h.update(c) for c in iter(lambda: open(zp, 'rb').read(8192), b'')]; calc = h.hexdigest().upper(); (print('CRITICAL: Hash mismatch! Expected:', expected, 'Got:', calc) or sys.exit(1)) if expected and expected != calc else print('Integrity verified.'); td = 'temp_restore'; os.path.exists(td) and shutil.rmtree(td); os.makedirs(td); zipfile.ZipFile(zp).extractall(td); src = os.path.join(td, 'LEAtTrace_temp.db'); dest = os.path.join('backend', 'LEAtTrace.db'); shutil.copy2(src, dest) if os.path.exists(src) else None; shutil.rmtree(td); print('SQLite database file restored successfully.')" "%ARCHIVE_PATH%"

if %ERRORLEVEL% NEQ 0 (
    echo Restoration failed.
    exit /b 1
)
echo === Restoration Sequence Completed Successfully ===
