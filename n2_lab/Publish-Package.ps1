param([Parameter(Mandatory=$true)][string]$ForkDirectory,[switch]$Apply)
$ErrorActionPreference='Stop'
$n2ForkRoot=(Resolve-Path -LiteralPath $ForkDirectory).Path
$n2Git=(Get-Command git -ErrorAction SilentlyContinue).Source
if (-not $n2Git) {
    $n2BundledGit='C:\Users\dots\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
    if (Test-Path -LiteralPath $n2BundledGit) { $n2Git=$n2BundledGit }
}
if (-not $n2Git) { throw 'git is required to verify the local fork.' }
$n2Branch=(& $n2Git -C $n2ForkRoot branch --show-current)
if ($LASTEXITCODE -ne 0 -or $n2Branch -ne 'main') { throw 'Select the main branch of your actual local minirubik fork first.' }
$n2Target=[IO.Path]::GetFullPath((Join-Path $n2ForkRoot 'n2_lab'))
if (-not $n2Target.StartsWith($n2ForkRoot.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Destination is outside the fork.' }
if (Test-Path -LiteralPath $n2Target) { throw 'n2_lab already exists. Review and preserve its contents before a later manual update.' }
$n2Folders=@('target','reference','host_tools','tools','docs','evidence')
$n2Files=@('Environment.ps1','Run-Lab.ps1','README.txt','Publish-Package.ps1','.gitattributes')
Write-Host "Import destination: $n2Target"
Write-Host 'Includes source, documentation, host oracle and measured evidence. Excludes simulator archive, compiler, host executables and scratch benchmark builds.'
Write-Host 'This performs no login, commit, tag or push. Confirm actual fork identity and student authorship/authorization before public submission.'
if (-not $Apply) { Write-Host 'Preview only. Add -Apply to copy into the verified main checkout.'; return }
New-Item -ItemType Directory -Path $n2Target | Out-Null
foreach ($n2Folder in $n2Folders) {
    $n2Source=Join-Path $PSScriptRoot $n2Folder
    Get-ChildItem -LiteralPath $n2Source -Recurse -File | Where-Object { $_.FullName -notmatch '[\\/]__pycache__[\\/]' } | ForEach-Object {
        $n2Relative=$_.FullName.Substring($PSScriptRoot.Length+1)
        $n2Output=Join-Path $n2Target $n2Relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $n2Output) -Force | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $n2Output
    }
}
foreach ($n2File in $n2Files) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $n2File) -Destination (Join-Path $n2Target $n2File) }
New-Item -ItemType Directory -Path (Join-Path $n2Target 'build') | Out-Null
foreach ($n2Name in @('solver_cli','solver_gui','gcc_reference','vectors','pipeline_demo')) {
    foreach ($n2Extension in @('elf','disasm','map','json','sections.txt')) {
        $n2Source=Join-Path $PSScriptRoot "build\$n2Name.$n2Extension"
        if (Test-Path -LiteralPath $n2Source) { Copy-Item -LiteralPath $n2Source -Destination (Join-Path $n2Target "build\$n2Name.$n2Extension") }
    }
}
Set-Content -LiteralPath (Join-Path $n2Target '.gitignore') -Value @('__pycache__/','toolchains/','build/host/','build/case_measurements/','*.pyc') -Encoding UTF8
Write-Host 'Local import complete. Review git diff/status and make your genuine commit on main.'
