$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("C:\Users\zwhiteman\Desktop\Other Certificates.lnk")
$Shortcut.TargetPath = "C:\Users\zwhiteman\Desktop\Elite-EasySigner\Other Certificates"
$Shortcut.Save()
Write-Host "Shortcut created on desktop."
