#include <windows.h>
#include <gdiplus.h>
#include <iostream>

HBITMAP LoadIconAsHBitmap(HINSTANCE hInstance, int resourceId, int width, int height) {
    HICON hIcon = (HICON)LoadImage(hInstance, MAKEINTRESOURCE(resourceId), IMAGE_ICON, width, height, LR_DEFAULTCOLOR);
    if (!hIcon) return NULL;
    ICONINFO ii;
    if (GetIconInfo(hIcon, &ii)) {
        HBITMAP hBmp = ii.hbmColor;
        if (ii.hbmMask) DeleteObject(ii.hbmMask);
        DestroyIcon(hIcon);
        return hBmp;
    }
    DestroyIcon(hIcon);
    return NULL;
}

HBITMAP LoadPngAsHBitmap(HINSTANCE hInstance, int resourceId) {
    HRSRC hRes = FindResource(hInstance, MAKEINTRESOURCE(resourceId), RT_RCDATA);
    if (!hRes) return NULL;
    DWORD size = SizeofResource(hInstance, hRes);
    HGLOBAL hMem = LoadResource(hInstance, hRes);
    void* pData = LockResource(hMem);
    HGLOBAL hBuffer = GlobalAlloc(GMEM_MOVEABLE, size);
    if (hBuffer) {
        void* pBuffer = GlobalLock(hBuffer);
        memcpy(pBuffer, pData, size);
        GlobalUnlock(hBuffer);
        IStream* pStream = NULL;
        if (CreateStreamOnHGlobal(hBuffer, TRUE, &pStream) == S_OK) {
            Gdiplus::Bitmap* bmp = Gdiplus::Bitmap::FromStream(pStream);
            HBITMAP hBmp = NULL;
            if (bmp && bmp->GetLastStatus() == Gdiplus::Ok) {
                bmp->GetHBITMAP(Gdiplus::Color::Transparent, &hBmp);
            }
            if (bmp) delete bmp;
            pStream->Release();
            return hBmp;
        }
        GlobalFree(hBuffer);
    }
    return NULL;
}
