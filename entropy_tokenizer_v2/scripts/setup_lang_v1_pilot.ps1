$ErrorActionPreference = "Stop"

param(
    [string]$Venv = ".venv-langv1",
    [ValidateSet("auto", "cpu", "cu128", "skip")]
    [string]$Torch = "auto",
    [switch]$SkipHumanEval,
    [switch]$ForceEnv
)

$root = Split-Path -Parent $PSScriptRoot
$argsList = @(
    (Join-Path $root "scripts\setup_lang_v1_pilot.py"),
    "--venv", $Venv,
    "--torch", $Torch
)

if ($SkipHumanEval) {
    $argsList += "--skip-human-eval"
}
if ($ForceEnv) {
    $argsList += "--force-env"
}

python @argsList
