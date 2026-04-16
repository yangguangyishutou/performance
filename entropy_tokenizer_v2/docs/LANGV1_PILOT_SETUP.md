# LangV1 Pilot Setup

This repo now includes a lowest-cost setup path for the learned-compression pilot.

## What it configures

- A dedicated virtual environment: `.venv-langv1`
- Training/eval dependencies for a small `LangV1` pilot
- Optional `human-eval` install for scoring
- A starter env file: `.env.langv1_pilot`
- Local output folders under `results/langv1_pilot`, `cache/langv1_pilot`, and `data/langv1_pilot`
- An environment self-check

## One-click setup

From the repo root on Windows PowerShell:

```powershell
.\scripts\setup_lang_v1_pilot.ps1
```

The script defaults to:

- `Qwen/Qwen2.5-Coder-1.5B`
- automatic torch selection:
  - `cu128` if `nvidia-smi` is available
  - otherwise CPU-only torch
- `human-eval` enabled

## Useful variants

CPU-only setup:

```powershell
.\scripts\setup_lang_v1_pilot.ps1 -Torch cpu
```

Skip `human-eval`:

```powershell
.\scripts\setup_lang_v1_pilot.ps1 -SkipHumanEval
```

Overwrite `.env.langv1_pilot`:

```powershell
.\scripts\setup_lang_v1_pilot.ps1 -ForceEnv
```

## Manual self-check

After setup:

```powershell
.\.venv-langv1\Scripts\Activate.ps1
python scripts/check_lang_v1_pilot.py
```

## Scope of this setup

This is the cheapest pilot path, not the full training stack for a 7B model.

Recommended first target:

- base model: `Qwen/Qwen2.5-Coder-1.5B`
- small `LangV1` CPT/SFT pilot
- `HumanEval-20` before any full `HumanEval-164` run
