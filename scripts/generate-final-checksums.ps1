$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $repositoryRoot "FINAL_SHA256SUMS"
$utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)

$paths = git -C $repositoryRoot ls-files --cached --others --exclude-standard |
    Where-Object { $_ -ne "FINAL_SHA256SUMS" } |
    Sort-Object

$lines = foreach ($relativePath in $paths) {
    $absolutePath = Join-Path $repositoryRoot ($relativePath -replace "/", "\")
    if (Test-Path -LiteralPath $absolutePath -PathType Leaf) {
        $hash = (Get-FileHash -LiteralPath $absolutePath -Algorithm SHA256).Hash.ToLowerInvariant()
        "$hash  $relativePath"
    }
}

[System.IO.File]::WriteAllLines($manifestPath, $lines, $utf8WithoutBom)
Write-Output "Wrote $($lines.Count) entries to $manifestPath"
