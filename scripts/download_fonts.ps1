# ═══════════════════════════════════════════════════════════
# Download Google Fonts for self-hosting (offline support)
# Run once: .\scripts\download_fonts.ps1
# ═══════════════════════════════════════════════════════════

$fontDir = "$PSScriptRoot\..\frontend\src\fonts"
if (!(Test-Path $fontDir)) { New-Item -ItemType Directory -Path $fontDir -Force | Out-Null }

Write-Host "⬇️  Downloading Inter font family..." -ForegroundColor Yellow

$interBase = "https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip"
$tempZip = "$env:TEMP\Inter-4.0.zip"
$tempExtract = "$env:TEMP\Inter-4.0"

# Download Inter
Invoke-WebRequest -Uri $interBase -OutFile $tempZip
Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

# Copy woff2 files
$interFiles = @{
  "InterWeb-Light.woff2"     = "Inter-Light.woff2"
  "InterWeb-Regular.woff2"   = "Inter-Regular.woff2"
  "InterWeb-Medium.woff2"    = "Inter-Medium.woff2"
  "InterWeb-SemiBold.woff2"  = "Inter-SemiBold.woff2"
  "InterWeb-Bold.woff2"      = "Inter-Bold.woff2"
  "InterWeb-ExtraBold.woff2" = "Inter-ExtraBold.woff2"
}

$found = Get-ChildItem -Path $tempExtract -Recurse -Filter "*.woff2"
foreach ($file in $found) {
  foreach ($key in $interFiles.Keys) {
    if ($file.Name -like "*$key*" -or $file.Name -eq $key) {
      Copy-Item $file.FullName "$fontDir\$($interFiles[$key])" -Force
      Write-Host "  ✓ $($interFiles[$key])" -ForegroundColor Green
    }
  }
}

# Fallback: if specific names not found, copy all woff2 matching weights
if (!(Test-Path "$fontDir\Inter-Regular.woff2")) {
  Write-Host "  ℹ️  Exact filenames not matched — copying available woff2 files..." -ForegroundColor Cyan
  $found | Where-Object { $_.Name -match "Inter" } | ForEach-Object {
    Copy-Item $_.FullName "$fontDir\$($_.Name)" -Force
    Write-Host "  ✓ $($_.Name)" -ForegroundColor Green
  }
}

# Cleanup Inter temp
Remove-Item $tempZip -Force -ErrorAction SilentlyContinue
Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n⬇️  Downloading JetBrains Mono..." -ForegroundColor Yellow

$jbBase = "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip"
$jbZip = "$env:TEMP\JetBrainsMono.zip"
$jbExtract = "$env:TEMP\JetBrainsMono"

Invoke-WebRequest -Uri $jbBase -OutFile $jbZip
Expand-Archive -Path $jbZip -DestinationPath $jbExtract -Force

$jbFound = Get-ChildItem -Path $jbExtract -Recurse -Filter "*.woff2"
foreach ($file in $jbFound) {
  if ($file.Name -match "JetBrainsMono-Regular\.woff2") {
    Copy-Item $file.FullName "$fontDir\JetBrainsMono-Regular.woff2" -Force
    Write-Host "  ✓ JetBrainsMono-Regular.woff2" -ForegroundColor Green
  }
  if ($file.Name -match "JetBrainsMono-Medium\.woff2") {
    Copy-Item $file.FullName "$fontDir\JetBrainsMono-Medium.woff2" -Force
    Write-Host "  ✓ JetBrainsMono-Medium.woff2" -ForegroundColor Green
  }
}

Remove-Item $jbZip -Force -ErrorAction SilentlyContinue
Remove-Item $jbExtract -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n✅ Fonts downloaded to: $fontDir" -ForegroundColor Green
Write-Host "   The app now works 100% offline!" -ForegroundColor Cyan
