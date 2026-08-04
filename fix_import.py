import os

path = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\java\com\elitesoftware\appmarketplace\MainActivity.java"
with open(path, "r") as f:
    code = f.read()

code = code.replace("ProgressBar pbDownload = convertView.findViewById(R.id.pbDownload);", "android.widget.ProgressBar pbDownload = convertView.findViewById(R.id.pbDownload);")

with open(path, "w") as f:
    f.write(code)

