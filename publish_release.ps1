param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)
$ErrorActionPreference = 'Stop'

Write-Host "Building C++ Server Manager..."
cd Manager_App
g++ -O2 -mwindows -std=c++17 -o Elite_App_Marketplace-Server.exe main.cpp resource.res -lcomctl32 -lws2_32 -lgdiplus
cd ..

Write-Host "Building Android APK..."
cd Client_App
./build_apk.ps1
cd ..

Write-Host "Signing Android APK..."
$toolsDir = "C:\AndroidBuildTools"
$apksigner = (Get-ChildItem -Path "$toolsDir\android-sdk\build-tools" -Filter "apksigner.bat" -Recurse | Select-Object -First 1).FullName
& $apksigner sign --ks "C:\Users\Administrator\Desktop\Local_APK_Store\Elite-EasySigner\EliteSoftware_Special.pfx" --ks-pass pass:Minecraft145!! --out "Client_App\app\build\outputs\apk\debug\app-release-signed.apk" "Client_App\app\build\outputs\apk\debug\app-debug.apk"

Write-Host "Injecting newest APK into Server's DB..."
Copy-Item "Client_App\app\build\outputs\apk\debug\app-release-signed.apk" "Manager_App\apks\Elite_App_Marketplace-Client.apk" -Force

Write-Host "Committing and Pushing to Git..."
git add .
git commit -m "Auto-build and release $Version"
git push origin master

Write-Host "Creating GitHub Releases..."
$gh = "C:\Reunion7_Windows\Program Files\GitHub CLI\gh.exe"
& $gh release create "server-$Version" "Manager_App\Elite_App_Marketplace-Server.exe" --title "Elite App Marketplace Server $Version" --notes "Automated release." --target master
& $gh release create "client-$Version" "Client_App\app\build\outputs\apk\debug\app-release-signed.apk" --title "Elite App Marketplace Client $Version" --notes "Automated release." --target master

Write-Host "Publish complete for $Version"
