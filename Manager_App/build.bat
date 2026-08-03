@echo off
echo Building Manager App...
g++ main.cpp -o Elite_App_Marketplace-Server.exe -mwindows -lcomctl32 -lws2_32 -static
if %errorlevel% equ 0 (
    echo Build successful: Elite_App_Marketplace-Server.exe
) else (
    echo Build failed!
)
pause
