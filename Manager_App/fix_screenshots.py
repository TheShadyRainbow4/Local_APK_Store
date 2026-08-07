
import re

with open("main.cpp", "r") as f:
    code = f.read()

# Add ImageList global
if "HIMAGELIST g_hImgListSS" not in code:
    code = code.replace("HWND lstScreenshots = NULL;", "HWND lstScreenshots = NULL;\nHIMAGELIST g_hImgListSS = NULL;")

# Initialize ImageList
init_code = "g_hImgListSS = ImageList_Create(100, 100, ILC_COLOR32 | ILC_MASK, 0, 10);"
if init_code not in code:
    code = code.replace("g_hTabImageList = ImageList_Create(16, 16, ILC_COLOR32 | ILC_MASK, 2, 1);", "g_hTabImageList = ImageList_Create(16, 16, ILC_COLOR32 | ILC_MASK, 2, 1);\n    " + init_code)

# Change ListView style
old_style = "LVS_REPORT | LVS_SINGLESEL | LVS_NOCOLUMNHEADER | LVS_SHOWSELALWAYS"
new_style = "LVS_ICON | LVS_SINGLESEL | LVS_SHOWSELALWAYS"
code = code.replace(old_style, new_style)

# Function to add image to imagelist
img_func = """
int AddImageToImageList(HIMAGELIST hIml, const std::string& path) {
    if (!fs::exists(path)) return -1;
    std::wstring wpath(path.begin(), path.end());
    Gdiplus::Bitmap* bmp = Gdiplus::Bitmap::FromFile(wpath.c_str());
    int idx = -1;
    if (bmp && bmp->GetLastStatus() == Gdiplus::Ok) {
        int w = bmp->GetWidth();
        int h = bmp->GetHeight();
        float scale = std::min((float)100/w, (float)100/h);
        int newW = std::max(1, (int)(w * scale));
        int newH = std::max(1, (int)(h * scale));
        Gdiplus::Bitmap* resized = new Gdiplus::Bitmap(100, 100, PixelFormat32bppARGB);
        Gdiplus::Graphics g(resized);
        g.Clear(Gdiplus::Color(255,255,255,255));
        g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
        g.DrawImage(bmp, (100-newW)/2, (100-newH)/2, newW, newH);
        HBITMAP hBmp = NULL;
        resized->GetHBITMAP(Gdiplus::Color(255, 255, 255), &hBmp);
        if (hBmp) {
            idx = ImageList_Add(hIml, hBmp, NULL);
            DeleteObject(hBmp);
        }
        delete resized;
        delete bmp;
    }
    return idx;
}
"""
if "AddImageToImageList" not in code:
    code = code.replace("void UpdatePreviewImage(std::string path) {", img_func + "\nvoid UpdatePreviewImage(std::string path) {")

# When clearing
code = code.replace("ListView_DeleteAllItems(lstScreenshots);", "ListView_DeleteAllItems(lstScreenshots); ImageList_RemoveAll(g_hImgListSS);")

# Update inserts
code = re.sub(
    r"screenshots\.push_back\(([^)]+)\);\s*LVITEMA lvi = \{0\};\s*lvi\.mask = LVIF_TEXT;\s*lvi\.iItem = ListView_GetItemCount\(lstScreenshots\);\s*lvi\.pszText = \(LPSTR\)([^;]+);\s*ListView_InsertItem\(lstScreenshots, &lvi\);",
    r"""screenshots.push_back(\1);
            int imgIdx = AddImageToImageList(g_hImgListSS, \1);
            LVITEMA lvi = {0};
            lvi.mask = LVIF_TEXT | LVIF_IMAGE;
            lvi.iItem = ListView_GetItemCount(lstScreenshots);
            lvi.iImage = imgIdx;
            lvi.pszText = (LPSTR)\2;
            ListView_InsertItem(lstScreenshots, &lvi);""",
    code
)

# Replace the specific insert in LoadAppDetails which uses sPath
code = re.sub(
    r"std::string sPath = imgDir \+ \"\\\\\" \+ s.get<std::string>\(\);\s*screenshots\.push_back\(sPath\);\s*LVITEMA lvi = \{0\};\s*lvi\.mask = LVIF_TEXT;\s*lvi\.iItem = ListView_GetItemCount\(lstScreenshots\);\s*lvi\.pszText = \(LPSTR\)s\.get<std::string>\(\)\.c_str\(\);\s*ListView_InsertItem\(lstScreenshots, &lvi\);",
    r"""std::string sPath = imgDir + "\\\\" + s.get<std::string>();
            screenshots.push_back(sPath);
            int imgIdx = AddImageToImageList(g_hImgListSS, sPath);
            LVITEMA lvi = {0};
            lvi.mask = LVIF_TEXT | LVIF_IMAGE;
            lvi.iItem = ListView_GetItemCount(lstScreenshots);
            lvi.iImage = imgIdx;
            lvi.pszText = (LPSTR)s.get<std::string>().c_str();
            ListView_InsertItem(lstScreenshots, &lvi);""",
    code
)

# Set the ImageList when ListView is created
code = code.replace("ListView_SetExtendedListViewStyle(lstScreenshots, LVS_EX_FULLROWSELECT | LVS_EX_DOUBLEBUFFER);", "ListView_SetExtendedListViewStyle(lstScreenshots, LVS_EX_FULLROWSELECT | LVS_EX_DOUBLEBUFFER);\n        ListView_SetImageList(lstScreenshots, g_hImgListSS, LVSIL_NORMAL);")

with open("main.cpp", "w") as f:
    f.write(code)

