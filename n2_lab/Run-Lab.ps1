param([ValidateSet('Gui','Build','Check','Measure','Benchmark','All')][string]$Action='Gui')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Environment.ps1')
function Invoke-N2Python([string[]]$N2Args) {
    if (-not $env:N2_PYTHON) { throw 'Python 3.10+ is needed for script actions; set N2_PYTHON.' }
    & $env:N2_PYTHON @N2Args
    if ($LASTEXITCODE -ne 0) { throw "Python action failed: $N2Args" }
}
if ($Action -eq 'Gui') {
    Write-Host 'Choose 5-stage processor; disable M and C. Add one LED Matrix, width 35, height 25.'
    Write-Host ('Ctrl+O -> Executable (ELF) -> ' + (Join-Path $PSScriptRoot 'build\solver_gui.elf'))
    Start-Process -FilePath $env:N2_RIPES -WindowStyle Normal
    exit
}
if ($Action -in @('Build','All')) {
    if (-not $env:N2_RV_GCC) { throw 'Run .\Environment.ps1 -InstallGcc, or set N2_RV_GCC.' }
    foreach ($n2Spec in @(@('solver_cli','0','0','False'),@('gcc_reference','0','0','True'),@('vectors','2','0','False'),@('solver_gui','0','1','False'))) {
        $n2Args=@((Join-Path $PSScriptRoot 'tools\build.py'),'--name',$n2Spec[0],'--mode',$n2Spec[1],'--render',$n2Spec[2])
        if ($n2Spec[3] -eq 'True') { $n2Args+='--reference' }
        Invoke-N2Python $n2Args
    }
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\build_pipeline.py'))
}
if ($Action -in @('Check','All')) {
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\verify_lab.py'))
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\run_validation.py'))
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\verify_led.py'))
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\verify_input_modes.py'))
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\audit_isa.py'))
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\audit_stack.py'))
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\pipeline_trace.py'))
}
if ($Action -in @('Measure','All')) {
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\measure_cases.py'))
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\profile_losses.py'))
}
if ($Action -in @('Benchmark','All')) {
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\benchmark_environment.py'))
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\benchmark_packing.py'))
    Invoke-N2Python @((Join-Path $PSScriptRoot 'tools\benchmark_target.py'))
}
