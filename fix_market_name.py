import os

path = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\res\values\strings.xml"
with open(path, "r") as f:
    xml = f.read()

xml = xml.replace('Elite App Marketplace', 'Market')
with open(path, "w") as f:
    f.write(xml)

path = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\AndroidManifest.xml"
with open(path, "r") as f:
    xml = f.read()

xml = xml.replace('@android:style/Theme.Holo.Light', '@android:style/Theme.Holo.Light.NoActionBar')
with open(path, "w") as f:
    f.write(xml)

