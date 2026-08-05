$ErrorActionPreference = 'SilentlyContinue';
Add-Type -AssemblyName System.IO.Compression.FileSystem;
$zip = [System.IO.Compression.ZipFile]::OpenRead('C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\apks\나눔명조.FlipFont.ver.3.5.build.6.apk');
$out = 'C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\images\나눔명조.FlipFont.ver.3.5.build.6_icon.png';
$specified = '';
$entry = $null;
if ($specified -ne '') { $entry = $zip.GetEntry($specified); }
if (-not $entry) {
  $imgs = $zip.Entries | Where-Object { ($_.FullName -like '*.png' -or $_.FullName -like '*.webp' -or $_.FullName -like '*.jpg') -and $_.FullName -notlike '*.9.png' };
  $priorities = @('res/mipmap-xxxhdpi-v4/ic_launcher.png', 'res/mipmap-xxhdpi-v4/ic_launcher.png', 'res/mipmap-xhdpi-v4/ic_launcher.png', 'res/mipmap-hdpi-v4/ic_launcher.png', 'res/mipmap-mdpi-v4/ic_launcher.png', 'res/drawable-xxhdpi-v4/ic_launcher.png', 'res/drawable-xhdpi-v4/ic_launcher.png', 'res/drawable-hdpi-v4/ic_launcher.png');
  foreach ($p in $priorities) { $e = $imgs | Where-Object { $_.FullName -eq $p }; if ($e) { $entry = $e; break } }
  if (-not $entry) { $entry = $imgs | Where-Object { $_.FullName -like '*ic_launcher*.png' } | Sort-Object Length -Descending | Select-Object -First 1; }
  if (-not $entry) { $entry = $imgs | Where-Object { $_.FullName -like '*icon*.png' } | Sort-Object Length -Descending | Select-Object -First 1; }
  if (-not $entry) { $entry = $imgs | Where-Object { $_.FullName -like 'res/*.png' } | Sort-Object Length -Descending | Select-Object -First 1; }
  if (-not $entry) { $entry = $imgs | Where-Object { $_.FullName -like '*ic_launcher*' -or $_.FullName -like '*icon*' -or $_.FullName -like 'res/*' } | Sort-Object Length -Descending | Select-Object -First 1; }
  if (-not $entry) { $entry = $imgs | Sort-Object Length -Descending | Select-Object -First 1; }
}
if ($entry) { $entry.ExtractToFile($out, $true); }
$zip.Dispose();
