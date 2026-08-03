import os

filepath = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\main.cpp"
with open(filepath, "r") as f:
    code = f.read()

# Remove the early SetWindowPos
code = code.replace("SetWindowPos(hwndTab, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);", "")

# Add it right before UpdateTabVisibility() at the end of WM_CREATE
code = code.replace("UpdateTabVisibility();\n        RefreshAppList();", "SetWindowPos(hwndTab, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);\n        UpdateTabVisibility();\n        RefreshAppList();")

with open(filepath, "w") as f:
    f.write(code)

