import os
import re

path = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\main.cpp"
with open(path, "r") as f:
    code = f.read()

# Replace all instances of hwnd parent in CreateWindow/Ex inside WM_CREATE for the UI elements
# We can just run a targeted string replace for all the known elements.

elements = ['hwndApps', 'hwndName', 'hwndPackage', 'hwndVersion', 'hwndCat', 'hwndTags', 'hwndDesc', 'lstScreenshots', 'btnAddScreenshot', 'btnClearScreenshots', 'hwndApkLabel', 'btnBrowse', 'btnDelete', 'btnClearForm', 'btnApply', 'btnExit', 'hwndLog']

for el in elements:
    # This regex looks for l = CreateWindow(..., hwnd, ...) and replaces hwnd with hwndTab
    # But it might be formatted differently, so let's just do a manual replace or regex
    # Usually it's , hwnd,  -> , hwndTab, 
    # But we only want to do it where l =  is at the start
    
    # Simple regex to replace the 8th argument (parent hwnd)
    pattern = r'(' + el + r'\s*=\s*CreateWindow(?:Ex)?\([^;]+?,\s*)hwnd(\s*,)'
    code = re.sub(pattern, r'\1hwndTab\2', code)

    # For invLabels
pattern = r'(invLabels\.push_back\(CreateWindow(?:Ex)?\([^;]+?,\s*)hwnd(\s*,)'
code = re.sub(pattern, r'\1hwndTab\2', code)

with open(path, "w") as f:
    f.write(code)
