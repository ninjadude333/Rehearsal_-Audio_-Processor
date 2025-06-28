@echo off
echo Rehearsal Audio Processor
echo ========================

if "%1"=="" (
    echo Usage: process_rehearsals.bat "path\to\rehearsal\folder"
    echo Example: process_rehearsals.bat "C:\Music\Rehearsals"
    pause
    exit /b 1
)

echo Processing folder: %1
echo Using reference songs from: .\songs
echo Output will be saved to: .\output

python rehearsal_processor.py "%1" --songs .\songs --output .\output

echo.
echo Processing complete! Check .\output\rehearsal_analysis.csv for results
pause