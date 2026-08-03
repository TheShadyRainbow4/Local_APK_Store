# EliteSoftware God-Tier Certificate
## Publisher: Zachary Whiteman (EliteSoftwareTech Co.) & Susan Gemm

This folder contains the master code-signing and web-hosting certificate for the EliteSoftware ecosystem.

### 🔑 Master Password
**PASSWORD:** `Minecraft145!!`

### 🛠️ Purpose & Policies (All-Purpose)
This certificate is generated with **All Application Policies** (`1.3.6.1.4.1.311.10.12.1`), making it functional for:
1. **Code Signing:** Authenticating binaries to ensure a teal "Identified Publisher" UAC prompt.
2. **Server Authentication:** SSL/TLS for local web hosting (IIS, Node.js).
3. **Client Authentication:** User/Machine identification.

### 🚀 System-Wide Deployment
This certificate is installed to the **Local Machine** (System-Wide) stores:
- **Trusted Root Certification Authorities**
- **Trusted Publishers**

### 📦 Files
- `EliteSoftware_Root.cer`: Global Root CA certificate.
- `EliteSoftware_Intermediate.cer`: Intermediate Code Signing CA certificate.
- `EliteSoftware_Special.pfx`: Private key and certificate chain (use for signing).
- `EliteSoftware_Special.cer`: Public leaf certificate (use for deployment/trust).

"Bringing 2006 to 2026 one line of code at a time."
