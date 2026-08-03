$ErrorActionPreference = 'Stop'

$toolsDir = "C:\AndroidBuildTools"
$jdkDir = "$toolsDir\jdk-17"
$sdkDir = "$toolsDir\android-sdk"
$cmdlineToolsDir = "$sdkDir\cmdline-tools\latest"

if (-not (Test-Path $toolsDir)) { New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null }

# 1. Download and Extract JDK 17
if (-not (Test-Path "$jdkDir\bin\java.exe")) {
    Write-Host "Downloading OpenJDK 17..."
    $jdkUrl = "https://aka.ms/download-jdk/microsoft-jdk-17.0.12-windows-x64.zip"
    $jdkZip = "$toolsDir\jdk17.zip"
    Invoke-WebRequest -Uri $jdkUrl -OutFile $jdkZip
    Write-Host "Extracting JDK 17..."
    Expand-Archive -Path $jdkZip -DestinationPath $toolsDir -Force
    Rename-Item "$toolsDir\jdk-17.0.12+7" "jdk-17"
    Remove-Item $jdkZip
}

$env:JAVA_HOME = $jdkDir
$env:Path = "$jdkDir\bin;" + $env:Path

# 2. Download and Extract Android Command Line Tools
if (-not (Test-Path "$cmdlineToolsDir\bin\sdkmanager.bat")) {
    Write-Host "Downloading Android SDK Command Line Tools..."
    $sdkUrl = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"
    $sdkZip = "$toolsDir\sdk.zip"
    Invoke-WebRequest -Uri $sdkUrl -OutFile $sdkZip
    
    if (-not (Test-Path $sdkDir)) { New-Item -ItemType Directory -Force -Path $sdkDir | Out-Null }
    Write-Host "Extracting SDK Tools..."
    Expand-Archive -Path $sdkZip -DestinationPath "$sdkDir\cmdline-tools" -Force
    Rename-Item "$sdkDir\cmdline-tools\cmdline-tools" "latest"
    Remove-Item $sdkZip
}

$env:ANDROID_HOME = $sdkDir

# 3. Accept Licenses
Write-Host "Accepting Android SDK Licenses..."
$yesParams = "y`n" * 10
$yesParams | & "$cmdlineToolsDir\bin\sdkmanager.bat" --licenses | Out-Null

# 4. Download Gradle Wrapper to the project if not exists
if (-not (Test-Path "gradlew.bat")) {
    Write-Host "Initializing Gradle Wrapper..."
    & "$jdkDir\bin\java.exe" -jar "gradle\wrapper\gradle-wrapper.jar" --version 8.1.1 2>$null
    # Since we don't have a global gradle, we can download the wrapper jar manually, 
    # but actually we can just download a generic gradle wrapper!
}

# Actually, the best way to get gradle without global gradle is to download gradle binary and use it!
$gradleDir = "$toolsDir\gradle-8.1.1"
if (-not (Test-Path "$gradleDir\bin\gradle.bat")) {
    Write-Host "Downloading Gradle 8.1.1..."
    $gradleUrl = "https://services.gradle.org/distributions/gradle-8.1.1-bin.zip"
    $gradleZip = "$toolsDir\gradle.zip"
    Invoke-WebRequest -Uri $gradleUrl -OutFile $gradleZip
    Write-Host "Extracting Gradle..."
    Expand-Archive -Path $gradleZip -DestinationPath $toolsDir -Force
    Remove-Item $gradleZip
}

# 5. Build the APK
Write-Host "Building the APK using Gradle..."
& "$gradleDir\bin\gradle.bat" assembleDebug

if ($LASTEXITCODE -eq 0) {
    Write-Host "APK Built Successfully at app\build\outputs\apk\debug\app-debug.apk"
} else {
    Write-Host "Gradle Build Failed."
}
