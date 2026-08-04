param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)
$ErrorActionPreference = 'Stop'

$rawVer = $Version.Replace("v", "")
$verParts = $rawVer.Split('.')
$verCode = 1
if ($verParts.Length -eq 3) {
    $verCode = [int]$verParts[0] * 10000 + [int]$verParts[1] * 100 + [int]$verParts[2]
}

Write-Host "Updating Android build.gradle version..."
$gradlePath = "Client_App/app/build.gradle"
$gradle = Get-Content $gradlePath
$gradle = $gradle -replace 'versionCode \d+', "versionCode $verCode"
$gradle = $gradle -replace 'versionName ".*"', "versionName ""$rawVer"""
$gradle | Set-Content $gradlePath

Write-Host "Building C++ Server Manager..."
cd Manager_App
windres resource.rc -O coff -o resource.res
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
$apkFileName = "Elite_App_Marketplace-Client_$Version.apk"
Copy-Item "Client_App\app\build\outputs\apk\debug\app-release-signed.apk" "Manager_App\apks\$apkFileName" -Force

Write-Host "Updating db.json..."
$dbPath = "Manager_App/db.json"
$dbStr = Get-Content $dbPath -Raw
$dbObj = $dbStr | ConvertFrom-Json
foreach ($app in $dbObj.apps) {
    if ($app.package_name -eq "com.elitesoftware.appmarketplace") {
        $found = $false
        foreach ($v in $app.versions) {
            if ($v.version -eq $rawVer) {
                $found = $true
            }
        }
        if (-not $found) {
            $newVer = @{
                "version" = $rawVer
                "file" = $apkFileName
            }
            $app.versions += $newVer
        }
    }
}
$dbObj | ConvertTo-Json -Depth 10 | Set-Content $dbPath

Write-Host "Committing and Pushing to Git..."
git add .
git commit -m "Auto-build and release $Version"
git push origin master

Write-Host "Creating GitHub Releases..."
$gh = "C:\Reunion7_Windows\Program Files\GitHub CLI\gh.exe"
& $gh release create "server-$Version" "Manager_App\Elite_App_Marketplace-Server.exe" --title "Elite App Marketplace Server $Version" --notes "Automated release." --target master

$properApkName = "Elite_App_Marketplace-Client_$Version.apk"
Copy-Item "Client_App\app\build\outputs\apk\debug\app-release-signed.apk" $properApkName -Force
& $gh release create "client-$Version" $properApkName --title "Elite App Marketplace Client $Version" --notes "Automated release." --target master
Remove-Item $properApkName

Write-Host "Publish complete for $Version"
