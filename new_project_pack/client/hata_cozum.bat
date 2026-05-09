@echo off
TITLE Firewall ve Defender Yonetici Araci

net session >nul 2>&1
if %errorlevel% neq 0 (
    msg * ".bat dosyasini yonetici olarak calistirin!"
    exit /b
)

powershell -Command "$Threats = Get-MpThreatDetection | Where-Object { $_.Resources -match 'metin2client.bin' }; if ($Threats) { foreach ($Threat in $Threats) { Add-MpPreference -ThreatIDDefaultAction_Ids $Threat.ThreatID -ThreatIDDefaultAction_Actions Allow } }"

powershell -Command "$rules = Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like '*Anticheat_BlockIP*' }; if ($rules) { $rules | Remove-NetFirewallRule; Write-Host 'Kurallar silindi.' } else { Write-Host 'Sorun duzeltilmistir.' }" 2>nul

echo Islem tamamlandi!
pause