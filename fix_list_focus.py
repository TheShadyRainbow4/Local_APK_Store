import os

filepath = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\res\layout\list_item_app.xml"
with open(filepath, "r") as f:
    xml = f.read()

xml = xml.replace('<Button', '<Button\n        android:focusable="false"')

with open(filepath, "w") as f:
    f.write(xml)

