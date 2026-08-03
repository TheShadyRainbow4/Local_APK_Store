# EliteSoftware Global Signing Mandate (GEMINI.md)

This certificate is the **Gold Standard** for all EliteSoftware projects. It must be used to sign every binary, DLL, and script intended for deployment to ensure system integrity and a "Teal" identified publisher status.

## 🏛️ Foundational Mandates
- **Always Use:** No EliteSoftware binary shall be deployed without being signed by this specific certificate.
- **System-Wide Trust:** The public `.cer` must be installed to the **Local Machine** Trusted Root and Trusted Publisher stores.

## 🔑 Certificate Details
- **Subject:** `CN=Zachary Whiteman (EliteSoftwareTech Co.) & Susan Gemm`
- **Password:** `Minecraft145!!`
- **Policies:** All Application Policies (Code Signing, Server Auth, Client Auth).

## 🛠️ Signing Logic (PowerShell)
To sign a file using this certificate and `signtool.exe`, use the following logic:

```powershell
$signtool = "path\to\signtool.exe"
$pfxPath = "path\to\EliteSoftware_Special.pfx"
$password = "Minecraft145!!"
$file = "path\to\your_app.exe"

& $signtool sign /f $pfxPath /p $password /fd SHA256 /t http://timestamp.digicert.com /v $file
```

## 📋 Deployment Logic
The certificate must be trusted system-wide before the UAC prompt will turn teal:

```powershell
$cerPath = "path\to\EliteSoftware_Special.cer"
& certutil.exe -addstore -f Root $cerPath
& certutil.exe -addstore -f TrustedPublisher $cerPath
```

"Consistency is the hallmark of Elite quality."

