import os

path = r"C:\Users\Administrator\Desktop\Local_APK_Store\Client_App\app\src\main\java\com\elitesoftware\appmarketplace\AppDetailActivity.java"
with open(path, "r") as f:
    code = f.read()

# Fix the duplicate @Override issue
code = code.replace('''    @Override
    private int getAppInstallState''', '''    private int getAppInstallState''')

with open(path, "w") as f:
    f.write(code)
