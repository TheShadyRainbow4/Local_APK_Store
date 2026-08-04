@echo off
echo Building Manager App...
windres resource.rc -O coff -o resource.res
g++ main.cpp resource.res -o Elite_App_Marketplace-Server.exe -mwindows -lcomctl32 -lws2_32 -lgdiplus -static
if %errorlevel% equ 0 (
    echo Build successful: Elite_App_Marketplace-Server.exe
) else (
    echo Build failed!
)
pause
