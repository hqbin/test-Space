# PowerShell script to update version in JSON file
param(
    [Parameter(Mandatory=$true)]
    [string]$NewVersion
)

$jsonPath = "frontend\public\api\agent\latest-version.json"

try {
    # Read the JSON file
    $content = Get-Content $jsonPath -Raw -Encoding UTF8
    
    # Replace the version using regex
    $newContent = $content -replace '"version":\s*"[0-9.]+"', "`"version`": `"$NewVersion`""
    
    # Write back to file
    $newContent | Set-Content $jsonPath -Encoding UTF8 -NoNewline
    
    Write-Host "Successfully updated version to $NewVersion"
    exit 0
} catch {
    Write-Host "Error updating JSON: $_"
    exit 1
}
