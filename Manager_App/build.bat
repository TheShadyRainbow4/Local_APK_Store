@echo off
echo Building Manager App...
g++ main.cpp -o ServerManager.exe -mwindows -lcomctl32
if %errorlevel% equ 0 (
    echo Build successful: ServerManager.exe
) else (
    echo Build failed!
)
pause
