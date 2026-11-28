param(
 [Parameter(Mandatory=$true)][string]$Snapshot,
 [Parameter(Mandatory=$true)][string]$ExternalDependency,
 [string]$Linker = 'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\link.exe',
 [string]$TrustedLinkerSha = 'a364af801a8539e4324d9489313dbf001d959128451fc99a27b24676bbac058f',
 [string]$ApprovedDependencies,
 [string]$HostClang = 'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\x64\bin\clang++.exe',
 [ValidateRange(1,100)][int]$Trials=20
)
# CRT151 monitoring-only ablation. Same preparation, policy and anchors as
# run_phase5_windows.ps1; builds the CRT151 driver and runs three arms per revision.
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 function Check([string]$name){if($LASTEXITCODE -ne 0){throw "$name failed ($LASTEXITCODE)"}}
 $clang=(Resolve-Path -LiteralPath $HostClang).Path
 $tool=(Resolve-Path (Join-Path $Snapshot 'bin\clang++.exe')).Path
 $linkerPath=(Resolve-Path -LiteralPath $Linker -ErrorAction Stop).Path
 if($TrustedLinkerSha -notmatch '^[0-9a-fA-F]{64}$'){throw 'TrustedLinkerSha must be a complete SHA-256 digest'}
 $measuredLinkerSha=(Get-FileHash -LiteralPath $linkerPath -Algorithm SHA256).Hash.ToLowerInvariant()
 if($measuredLinkerSha -ne $TrustedLinkerSha.ToLowerInvariant()){throw "Linker SHA-256 mismatch: $linkerPath expected=$TrustedLinkerSha observed=$measuredLinkerSha"}
 Write-Host "CRT151_LINKER_AUTH $linkerPath sha256=$measuredLinkerSha"
 Write-Host "CRT151_HOST_CLANG $clang $((& $clang --version)[0])"
 New-Item -ItemType Directory -Force 'bin','results' | Out-Null
 & $clang -std=c++17 -O2 src/crt151_monitor_ablation.cpp -o bin/crt151_monitor_ablation.exe
 Check 'compile ablation driver'
 # Separate output names: never overwrite the binaries behind the published CRT1411 evidence.
 & $clang -std=c++17 -O2 src/crt150_debug_gate_windows.cpp -o bin/crt151_debug_gate.exe
 Check 'compile execution monitor'
 & $clang -std=c++17 -O2 -c src/native_verify.cpp -o bin/crt151_native_verify.obj
 Check 'compile independent verifier'
 $outDir=Join-Path (Resolve-Path results).Path ('ablation_'+[DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss_fff'))
 New-Item -ItemType Directory -Force $outDir | Out-Null
 & py -S src/prepare_crossover.py --output $outDir --trials $Trials --sizes '6,8,9,10,11,12' --full-root-check
 Check 'prepare authenticated revisions'
 $policy=Join-Path $outDir 'allow.tsv'
 $runtimeDir=Split-Path $linkerPath -Parent
 $runtimeFiles=@(@{ Name='vcruntime140_1.dll'; Sha='99ad0c5380674e28f965dc76b7cdfb8688cc2175a6641e00ab524195c3eaa900' })
 $extra=@()
 foreach($item in $runtimeFiles){
  $dep=Join-Path $runtimeDir $item.Name
  if((Get-FileHash -LiteralPath $dep -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Sha){throw "Runtime identity changed: $dep"}
  $extra+=@('--external-dependency',$dep)
 }
 $approvedArgs=@()
 if($ApprovedDependencies){$approvedArgs=@('--approved-manifest',(Resolve-Path -LiteralPath $ApprovedDependencies -ErrorAction Stop).Path)}
 & py -S src/prepare_execution_policy.py --snapshot $Snapshot --external-dependency $ExternalDependency --external-dependency $linkerPath @extra @approvedArgs --output $policy
 Check 'prepare file-ID and SHA policy'
 & py -S src/ablation_report.py --driver (Resolve-Path 'bin/crt151_monitor_ablation.exe').Path --manifest (Join-Path $outDir 'crossover_manifest.json') --verifier-object (Resolve-Path 'bin/crt151_native_verify.obj').Path --compiler $tool --gate (Resolve-Path 'bin/crt151_debug_gate.exe').Path --policy $policy --work (Join-Path $outDir 'work') --output (Join-Path $outDir 'ablation.json')
 Check 'monitoring-only ablation'
 Write-Host "CRT151_REPORT $(Join-Path $outDir 'ablation.json')"
}finally{Pop-Location}
