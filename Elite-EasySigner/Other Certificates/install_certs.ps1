Write-Host "--- EliteSoftware Chain Trust Deployment ---"

$certFiles = @(
    "EliteSoftware_Root.cer",
    "EliteSoftware_Intermediate.cer",
    "EliteSoftware_Special.cer"
)

foreach ($file in $certFiles) {
    if (Test-Path $file) {
        Write-Host "Processing $file..."
        
        # Add to Local Machine Root (Trusted Root Certification Authorities)
        Write-Host "  -> Adding to Root store..."
        & certutil.exe -addstore -f Root $file
        
        # Add to Local Machine TrustedPublisher (Trusted Publishers)
        Write-Host "  -> Adding to TrustedPublisher store..."
        & certutil.exe -addstore -f TrustedPublisher $file
        
        # Also keep it in CA store for intermediate path building if it's the intermediate
        if ($file -eq "EliteSoftware_Intermediate.cer") {
            Write-Host "  -> Adding to CA store (Intermediate)..."
            & certutil.exe -addstore -f CA $file
        }
    } else {
        Write-Warning "File not found: $file"
    }
}

Write-Host "--- Trust Deployment Complete ---"
