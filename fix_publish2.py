import os

path = r"C:\Users\Administrator\Desktop\Local_APK_Store\publish_release.ps1"
with open(path, "r") as f:
    ps1 = f.read()

new_ps1 = ps1.replace('Write-Host "Building C++ Server Manager..."', '''$rawVer = $Version.Replace("v", "")
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

Write-Host "Building C++ Server Manager..."''')

new_ps1 = new_ps1.replace('Write-Host "Committing and Pushing to Git..."', '''Write-Host "Updating db.json..."
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
                "file" = "Elite_App_Marketplace-Client.apk"
            }
            $app.versions += $newVer
        }
    }
}
$dbObj | ConvertTo-Json -Depth 10 | Set-Content $dbPath

Write-Host "Committing and Pushing to Git..."''')

with open(path, "w") as f:
    f.write(new_ps1)

