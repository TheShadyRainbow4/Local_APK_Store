
import re
with open("main.cpp", "r") as f:
    code = f.read()

# Fix WM_DROPFILES insert
code = re.sub(
    r"screenshots\.push_back\(path\);\s*LVITEMA lvi = \{0\};\s*lvi\.mask = LVIF_TEXT;\s*lvi\.iItem = ListView_GetItemCount\(lstScreenshots\);\s*std::string fname = fs::path\(path\)\.filename\(\)\.string\(\);\s*lvi\.pszText = \(LPSTR\)fname\.c_str\(\);\s*ListView_InsertItem\(lstScreenshots, &lvi\);",
    r"""screenshots.push_back(path);
                int imgIdx = AddImageToImageList(g_hImgListSS, path);
                LVITEMA lvi = {0};
                lvi.mask = LVIF_TEXT | LVIF_IMAGE;
                lvi.iItem = ListView_GetItemCount(lstScreenshots);
                lvi.iImage = imgIdx;
                std::string fname = fs::path(path).filename().string();
                lvi.pszText = (LPSTR)fname.c_str();
                ListView_InsertItem(lstScreenshots, &lvi);""",
    code
)

# Fix Add Screenshot button insert
code = re.sub(
    r"screenshots\.push_back\(imgPath\);\s*LVITEMA lvi = \{0\};\s*lvi\.mask = LVIF_TEXT;\s*lvi\.iItem = ListView_GetItemCount\(lstScreenshots\);\s*std::string fname = fs::path\(imgPath\)\.filename\(\)\.string\(\);\s*lvi\.pszText = \(LPSTR\)fname\.c_str\(\);\s*ListView_InsertItem\(lstScreenshots, &lvi\);",
    r"""screenshots.push_back(imgPath);
                int imgIdx = AddImageToImageList(g_hImgListSS, imgPath);
                LVITEMA lvi = {0};
                lvi.mask = LVIF_TEXT | LVIF_IMAGE;
                lvi.iItem = ListView_GetItemCount(lstScreenshots);
                lvi.iImage = imgIdx;
                std::string fname = fs::path(imgPath).filename().string();
                lvi.pszText = (LPSTR)fname.c_str();
                ListView_InsertItem(lstScreenshots, &lvi);""",
    code
)

with open("main.cpp", "w") as f:
    f.write(code)

