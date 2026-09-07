@echo off
echo ==============================================
echo Pushing TrinetLayer Cyber Labs to GitHub...
echo Target: https://github.com/lakshaysoni22/Security-Lab
echo ==============================================
git push -u origin main --force
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================
    echo SUCCESS! Repository pushed successfully.
    echo Now open https://vercel.com/new to deploy!
    echo ==============================================
) else (
    echo.
    echo If prompted for login, please sign in to GitHub in the popup window.
)
pause
