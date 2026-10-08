param([switch]$InstallGcc)
$ErrorActionPreference = 'Stop'
$n2LabRoot = $PSScriptRoot
$n2WorkspaceTools = [IO.Path]::GetFullPath((Join-Path $n2LabRoot '..\..\work\toolchains'))
if (-not $env:N2_RIPES) {
    $n2RipesCandidates = @((Join-Path $n2LabRoot 'toolchains\Ripes\Ripes.exe'), (Join-Path $n2WorkspaceTools 'Ripes\Ripes.exe'))
    $env:N2_RIPES = $n2RipesCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $env:N2_RIPES) {
        $n2Zip = Join-Path $n2LabRoot 'Ripes-portable-pinned.zip'
        if (-not (Test-Path -LiteralPath $n2Zip)) { throw 'Set N2_RIPES to the pinned installed Ripes.exe, or place Ripes-portable-pinned.zip from the complete delivery bundle beside Environment.ps1.' }
        if ((Get-FileHash -LiteralPath $n2Zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'ad16997577d877838110fca9035ded9e7438db7b2e868ec05a681a12453014a4') { throw 'Ripes archive checksum mismatch' }
        Expand-Archive -LiteralPath $n2Zip -DestinationPath (Join-Path $n2LabRoot 'toolchains\Ripes')
        $env:N2_RIPES = Join-Path $n2LabRoot 'toolchains\Ripes\Ripes.exe'
    }
}
if (-not $env:N2_RV_GCC) {
    $n2GccRel = 'gcc\xpack-riscv-none-elf-gcc-15.2.0-1\bin\riscv-none-elf-gcc.exe'
    $n2GccCandidates = @((Join-Path $n2LabRoot ('toolchains\' + $n2GccRel)), (Join-Path $n2WorkspaceTools $n2GccRel))
    $env:N2_RV_GCC = $n2GccCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $env:N2_RV_GCC -and $InstallGcc) {
        $n2Dir = Join-Path $n2LabRoot 'toolchains'
        New-Item -ItemType Directory -Path $n2Dir -Force | Out-Null
        $n2Zip = Join-Path $n2Dir 'gcc-pinned.zip'
        Invoke-WebRequest -Uri 'https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack/releases/download/v15.2.0-1/xpack-riscv-none-elf-gcc-15.2.0-1-win32-x64.zip' -OutFile $n2Zip
        if ((Get-FileHash -LiteralPath $n2Zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne '85ef714dacd273b1dadf4af4892774520ac01915bfa6da816a56e7e41591e09e') { throw 'GCC archive checksum mismatch' }
        Expand-Archive -LiteralPath $n2Zip -DestinationPath (Join-Path $n2Dir 'gcc')
        $env:N2_RV_GCC = Join-Path $n2Dir $n2GccRel
    }
}
if (-not $env:N2_PYTHON) {
    $n2BundledPython = 'C:\Users\dots\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $env:N2_PYTHON = if (Test-Path -LiteralPath $n2BundledPython) { $n2BundledPython } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
}
Write-Host "Ripes: $env:N2_RIPES"
Write-Host "RV32 GCC: $env:N2_RV_GCC"
Write-Host "Python: $env:N2_PYTHON"
