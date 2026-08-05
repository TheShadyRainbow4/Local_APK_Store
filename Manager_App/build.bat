@echo off
echo Terminating running instances...
taskkill /F /IM Elite_App_Marketplace-Server.exe >nul 2>&1
taskkill /F /IM LocalAPKStore.exe >nul 2>&1

echo Cleaning old builds...
if exist LocalAPKStore.exe del LocalAPKStore.exe
if exist Elite_App_Marketplace-Server.exe del Elite_App_Marketplace-Server.exe

echo Building Manager App...
windres resource.rc -O coff -o resource.res
g++ main.cpp resource.res -o Elite_App_Marketplace-Server.exe -mwindows -lcomctl32 -lws2_32 -lgdiplus -lole32 -static

if %errorlevel% equ 0 (
    echo Build successful: Elite_App_Marketplace-Server.exe
) else (
    echo Build failed!
)
