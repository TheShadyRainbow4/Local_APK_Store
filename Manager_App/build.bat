@echo off
echo Terminating running instances...
taskkill /F /IM Elite_App_Marketplace-Server.exe >nul 2>&1
taskkill /F /IM LocalAPKStore.exe >nul 2>&1

echo Cleaning old builds...
if exist LocalAPKStore.exe del LocalAPKStore.exe
if exist Elite_App_Marketplace-Server.exe del Elite_App_Marketplace-Server.exe

echo Building Manager App...
windres resource.rc -O coff -o resource.res
gcc -O2 -c miniz.c -o miniz.o
g++ -O2 -mwindows -std=c++17 -o Elite_App_Marketplace-Server.exe main.cpp miniz.o resource.res -lcomctl32 -lws2_32 -lgdiplus -lole32 -static -static-libgcc -static-libstdc++

if %errorlevel% equ 0 (
    echo Build successful: Elite_App_Marketplace-Server.exe
    cd ..
    powershell -NoProfile -ExecutionPolicy Bypass -File publish_release.ps1
) else (
    echo Build failed!
)
