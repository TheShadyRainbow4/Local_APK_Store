# EliteSoftware Global Signing Mandate (GEMINI.md)

This certificate ecosystem is the **Gold Standard** for all EliteSoftware projects. It uses a three-tier certificate chain to ensure maximum security and trust.

## 🏛️ Foundational Mandates
- **Always Use:** No EliteSoftware binary shall be deployed without being signed by the `EliteSoftware_Special` leaf certificate.
- **System-Wide Trust:** The full chain (Root, Intermediate, and Leaf) must be installed to the appropriate Local Machine stores.

## 🔗 Certificate Chain Structure
1. **Root CA:** `CN=EliteSoftware Global Root G1` (Trusted Root Certification Authorities)
2. **Intermediate CA:** `CN=EliteSoftware Code Signing CA G1` (Intermediate Certification Authorities)
3. **Leaf Certificate:** `CN=EliteSoftwareTech Company - Zachary Whiteman` (Trusted Publishers)

## 🔑 Certificate Details (Leaf)
- **Subject:** `CN=EliteSoftwareTech Company - Zachary Whiteman`
- **Emails:** `zwhiteman7144@gmail.com`, `zwhiteman7145@gmail.com`, `theshadyrainbow4@gmail.com`
- **Password:** `Minecraft145!!`
- **Policies:** Code Signing, Email Protection, Server Auth, Client Auth, All Application Policies.

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
The full chain must be trusted for the UAC prompt to turn teal:

```powershell
# Run install_certs.ps1 to automatically install the chain:
.\install_certs.ps1
```

"Consistency is the hallmark of Elite quality."

