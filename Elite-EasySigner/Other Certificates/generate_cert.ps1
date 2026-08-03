$password = ConvertTo-SecureString -String "Minecraft145!!" -Force -AsPlainText

Write-Host "--- EliteSoftware Certificate Chain Generation ---"

# 1. Create Root CA
Write-Host "Creating EliteSoftware Global Root G1..."
$rootCert = New-SelfSignedCertificate -Subject "CN=EliteSoftware Global Root G1" `
    -KeyUsage DigitalSignature, CertSign, CRLSign `
    -TextExtension @("2.5.29.19={text}ca=1&pathlength=2") `
    -CertStoreLocation "Cert:\LocalMachine\My" `
    -NotAfter (Get-Date).AddYears(20) `
    -FriendlyName "EliteSoftware Global Root G1"

if ($null -eq $rootCert) { throw "Failed to create Root CA" }

# 2. Create Intermediate CA signed by Root
Write-Host "Creating EliteSoftware Code Signing CA G1..."
$interCert = New-SelfSignedCertificate -Subject "CN=EliteSoftware Code Signing CA G1" `
    -Signer $rootCert `
    -KeyUsage DigitalSignature, CertSign, CRLSign `
    -TextExtension @("2.5.29.19={text}ca=1&pathlength=1") `
    -CertStoreLocation "Cert:\LocalMachine\My" `
    -NotAfter (Get-Date).AddYears(15) `
    -FriendlyName "EliteSoftware Code Signing CA G1"

if ($null -eq $interCert) { throw "Failed to create Intermediate CA" }

# 3. Create Leaf Certificate (EliteSoftware_Special) signed by Intermediate
Write-Host "Creating EliteSoftware_Special End-Entity..."
$leafCert = New-SelfSignedCertificate -Subject "CN=EliteSoftwareTech Company - Zachary Whiteman" `
    -Signer $interCert `
    -TextExtension @( `
        "2.5.29.37={text}1.3.6.1.5.5.7.3.3, 1.3.6.1.5.5.7.3.4, 1.3.6.1.5.5.7.3.1, 1.3.6.1.5.5.7.3.2, 1.3.6.1.4.1.311.10.12.1", `
        "2.5.29.17={text}email=zwhiteman7144@gmail.com&email=zwhiteman7145@gmail.com&email=theshadyrainbow4@gmail.com" `
    ) `
    -KeyUsage DigitalSignature, KeyEncipherment, DataEncipherment, NonRepudiation `
    -CertStoreLocation "Cert:\LocalMachine\My" `
    -NotAfter (Get-Date).AddYears(10) `
    -FriendlyName "EliteSoftware_Special"

if ($null -eq $leafCert) { throw "Failed to create Leaf Certificate" }

# Exporting files
Write-Host "Exporting certificates to files..."
Export-Certificate -Cert $rootCert -FilePath "EliteSoftware_Root.cer"
Export-Certificate -Cert $interCert -FilePath "EliteSoftware_Intermediate.cer"

# Export Leaf PFX and CER
# We use the object directly instead of the path string to avoid issues
Export-PfxCertificate -Cert $leafCert -FilePath "EliteSoftware_Special.pfx" -Password $password
Export-Certificate -Cert $leafCert -FilePath "EliteSoftware_Special.cer"

Write-Host "--- Chain Generation Complete ---"
Write-Host "Chain: Root -> Intermediate -> EliteSoftware_Special"
