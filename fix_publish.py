import os
import re

path = r"C:\Users\Administrator\Desktop\Local_APK_Store\publish_release.ps1"
with open(path, "r") as f:
    ps1 = f.read()

# I want to add steps to bump versionCode/versionName in build.gradle
# and update db.json.
# Wait, let's just rewrite publish_release.ps1 carefully.

new_ps1 = ps1.replace('Write-Host "Building C++ Server Manager..."', ''' = .Replace("v", "")
 = .Split('.')
 = 1
if (.Length -eq 3) {
     = [int][0] * 10000 + [int][1] * 100 + [int][2]
}

Write-Host "Updating Android build.gradle version..."
 = "Client_App/app/build.gradle"
 = Get-Content 
 =  -replace 'versionCode \d+', "versionCode "
 =  -replace 'versionName ".*"', "versionName """""
 | Set-Content 

Write-Host "Building C++ Server Manager..."''')

new_ps1 = new_ps1.replace('Write-Host "Committing and Pushing to Git..."', '''Write-Host "Updating db.json..."
 = "Manager_App/db.json"
 = Get-Content  | Out-String
 =  | ConvertFrom-Json
foreach ( in .apps) {
    if (.package_name -eq "com.elitesoftware.appmarketplace") {
        # Check if version exists
         = False
        foreach ( in .versions) {
            if (.version -eq ) {
                 = True
            }
        }
        if (-not ) {
             = @{
                "version" = 
                "file" = "Elite_App_Marketplace-Client.apk"
            }
            .versions += 
        }
    }
}
 | ConvertTo-Json -Depth 10 | Set-Content 

Write-Host "Committing and Pushing to Git..."''')

with open(path, "w") as f:
    f.write(new_ps1)

