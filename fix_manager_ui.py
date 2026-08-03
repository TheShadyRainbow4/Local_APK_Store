import os

filepath = r"C:\Users\Administrator\Desktop\Local_APK_Store\Manager_App\main.cpp"
with open(filepath, "r") as f:
    code = f.read()

# 1. Add WS_CLIPSIBLINGS to hwndTab
code = code.replace('hwndTab = CreateWindowEx(0, WC_TABCONTROL, "", WS_CHILD | WS_VISIBLE, 10, 50, 810, 450, hwnd, (HMENU)100, NULL, NULL);',
                    'hwndTab = CreateWindowEx(0, WC_TABCONTROL, "", WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS, 10, 50, 810, 450, hwnd, (HMENU)100, NULL, NULL);\n        SetWindowPos(hwndTab, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);')

# 2. Fix WM_CTLCOLORSTATIC to be transparent
old_color = '''    case WM_CTLCOLORSTATIC: {
        HDC hdcStatic = (HDC)wParam;
        SetBkColor(hdcStatic, GetSysColor(COLOR_BTNFACE));
        return (INT_PTR)GetSysColorBrush(COLOR_BTNFACE);
    }'''

new_color = '''    case WM_CTLCOLORSTATIC: {
        HDC hdcStatic = (HDC)wParam;
        SetBkMode(hdcStatic, TRANSPARENT);
        return (INT_PTR)GetStockObject(HOLLOW_BRUSH);
    }'''
code = code.replace(old_color, new_color)

# 3. Add WS_CLIPSIBLINGS to all children to prevent flickering
code = code.replace('WS_CHILD | WS_VISIBLE', 'WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS')

with open(filepath, "w") as f:
    f.write(code)

