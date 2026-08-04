import os

path = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\main.cpp"
with open(path, "r") as f:
    code = f.read()

bad_code = '''          RECT tabRect;
          GetWindowRect(hwndTab, &tabRect);
          MapWindowPoints(HWND_DESKTOP, hwnd, (LPPOINT)&tabRect, 2);
          SendMessage(hwndTab, TCM_ADJUSTRECT, FALSE, (LPARAM)&tabRect);'''

good_code = '''          RECT tabRect;
          GetClientRect(hwndTab, &tabRect);
          SendMessage(hwndTab, TCM_ADJUSTRECT, FALSE, (LPARAM)&tabRect);'''

code = code.replace(bad_code, good_code)

with open(path, "w") as f:
    f.write(code)

