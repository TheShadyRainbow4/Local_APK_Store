param(
    [string]$Version = ""
)
$ErrorActionPreference = 'Stop'

$dbPath = "Manager_App/db.json"
$dbStr = Get-Content $dbPath -Raw
$dbObj = $dbStr | ConvertFrom-Json

if ([string]::IsNullOrWhiteSpace($Version)) {
    $app = $dbObj.apps | Where-Object { $_.package_name -eq "com.elitesoftware.geminiwidget" }
    if ($app) {
        $sortedVers = $app.versions | Sort-Object { [version]($_.version -replace '^v?(\d+\.\d+)$', '${1}.0' -replace '^v?(\d+\.\d+\.\d+).*', '$1') } -Descending
        $latestVer = $sortedVers[0].version
        $verParts = $latestVer.Split('.')
        $patch = [int]$verParts[2] + 1
        $Version = "v" + $verParts[0] + "." + $verParts[1] + "." + $patch
    } else {
        $Version = "v1.0.0"
    }
    Write-Host "Auto-incremented version to $Version"
}

$rawVer = $Version.Replace("v", "")
$verParts = $rawVer.Split('.')
$verCode = 1
if ($verParts.Length -eq 3) {
    $verCode = [int]$verParts[0] * 10000 + [int]$verParts[1] * 100 + [int]$verParts[2]
}

Write-Host "Updating Android build.gradle version..."
$gradlePath = "EliteGeminiWidget/app/build.gradle"
$gradle = Get-Content $gradlePath
$gradle = $gradle -replace 'versionCode \d+', "versionCode $verCode"
$gradle = $gradle -replace 'versionName ".*"', "versionName `"$rawVer`""
$gradle | Set-Content $gradlePath

Write-Host "Building Android APK..."
cd EliteGeminiWidget
$env:JAVA_HOME = "C:\AndroidBuildTools\jdk-17"
$env:ANDROID_HOME = "C:\AndroidBuildTools\android-sdk"
& "C:\AndroidBuildTools\gradle-8.1.1\bin\gradle.bat" clean assembleDebug
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: APK Build Failed! Aborting release." -ForegroundColor Red
    exit 1
}
cd ..

Write-Host "Signing Android APK..."
$toolsDir = "C:\AndroidBuildTools"
$apksigner = (Get-ChildItem -Path "$toolsDir\android-sdk\build-tools" -Filter "apksigner.bat" -Recurse | Select-Object -First 1).FullName
& $apksigner sign --ks "C:\Users\Administrator\Desktop\Local_APK_Store\Elite-EasySigner\EliteSoftware_Special.pfx" --ks-pass pass:Minecraft145!! --out "EliteGeminiWidget\app\build\outputs\apk\debug\app-release-signed.apk" "EliteGeminiWidget\app\build\outputs\apk\debug\app-debug.apk"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: APK Signing Failed! Aborting release." -ForegroundColor Red
    exit 1
}

Write-Host "Injecting newest APK into Server's DB..."
$apkFileName = "EliteGeminiWidget_$Version.apk"
Copy-Item "EliteGeminiWidget\app\build\outputs\apk\debug\app-release-signed.apk" "Manager_App\apks\$apkFileName" -Force

Write-Host "Updating db.json..."
$dbObj = Get-Content $dbPath -Raw | ConvertFrom-Json
$app = $dbObj.apps | Where-Object { $_.package_name -eq "com.elitesoftware.geminiwidget" }

$newVer = @{
    "version" = $rawVer
    "file" = $apkFileName
}

if ($app) {
    $found = $false
    foreach ($v in $app.versions) {
        if ($v.version -eq $rawVer) {
            $found = $true
        }
    }
    if (-not $found) {
        $app.versions = @($newVer) + $app.versions
    }
} else {
    $newApp = @{
        "name" = "Elite Gemini Widget"
        "package_name" = "com.elitesoftware.geminiwidget"
        "description" = "A floating Gemini widget for the launcher."
        "category" = "Tools"
        "versions" = @($newVer)
        "screenshots" = @()
        "tags" = @("Gemini", "Widget", "Floating")
        "icon" = ""
        "reviews" = @()
    }
    $dbObj.apps += $newApp
}
$dbObj | ConvertTo-Json -Depth 10 | Set-Content $dbPath

Write-Host "Committing and Pushing to Git..."
git add .
git commit -m "Auto-build and release EliteGeminiWidget $Version"
git push origin master

Write-Host "Publish complete for $Version"
