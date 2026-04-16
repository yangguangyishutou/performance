# LangV1 Remote GPU Setup

This is the bootstrap entry point for the low-cost remote `LangV1` pilot.

Read [LANGV1_AUTODL_RUNBOOK.md](./LANGV1_AUTODL_RUNBOOK.md) first if you are
restarting the exact AutoDL workflow we already validated in practice.

## Important Corrections

The older remote path wasted time in four places:

- It tried to install Miniforge over SSH.
- It tried to re-download GPU `torch` from `download.pytorch.org`.
- It rebuilt the Python stack even when the server already had a working CUDA
  `torch`.
- It was easy to leave stale Hugging Face `*.lock` files behind after an
  interrupted run.

The current bootstrap path is intentionally more conservative.

## What the bootstrap does now

- Packages the repo locally.
- Uploads it to a remote Linux GPU server over SSH.
- Preserves existing remote `results/`, `cache/`, and checkpoints by default.
- Creates a remote `venv` at `/root/.venv-langv1` unless overridden.
- Reuses the server's existing CUDA `torch` install when available.
- Installs the repo's training/eval dependencies, `bitsandbytes`, and
  `human-eval`.
- Runs `scripts/check_lang_v1_pilot.py`.

## Recommended server shape

- Linux
- NVIDIA GPU with at least `24GB` VRAM
- Root SSH access or a user with package-install permissions
- Enough disk for the repo plus model downloads

For the current pilot, `32GB` VRAM is enough for:

- `Qwen/Qwen2.5-Coder-1.5B`
- LoRA / QLoRA
- `HumanEval-20`

## One-command bootstrap from the local workspace

From the repo root:

```powershell
python scripts/remote_bootstrap_lang_v1.py `
  --host YOUR_HOST `
  --port YOUR_PORT `
  --user root `
  --password YOUR_PASSWORD
```

Useful optional flags:

```powershell
python scripts/remote_bootstrap_lang_v1.py `
  --host YOUR_HOST `
  --port YOUR_PORT `
  --user root `
  --password YOUR_PASSWORD `
  --remote-dir /root/workspaces/entropy_tokenizer_v2 `
  --torch-variant cu128
```

If you really want to wipe the remote workspace first, opt in explicitly:

```powershell
python scripts/remote_bootstrap_lang_v1.py `
  --host YOUR_HOST `
  --port YOUR_PORT `
  --user root `
  --password YOUR_PASSWORD `
  --clean-remote
```

Use `--clean-remote` only for disposable runs. It removes the remote workspace
before unpacking the repo.

## Manual bootstrap on the server

After copying the repo to the server:

```bash
cd /root/workspaces/entropy_tokenizer_v2
bash scripts/setup_lang_v1_remote.sh
```

Useful env overrides:

```bash
LANGV1_REPO_DIR=/root/workspaces/entropy_tokenizer_v2
LANGV1_VENV_DIR=/root/.venv-langv1
LANGV1_BASE_PYTHON=/root/miniconda3/bin/python
LANGV1_TORCH_VARIANT=cu128
LANGV1_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
LANGV1_PIP_FALLBACK_INDEX_URL=https://pypi.org/simple
LANGV1_INSTALL_BNB=1
LANGV1_INSTALL_HUMANEVAL=1
LANGV1_HF_ENDPOINT=https://hf-mirror.com
```

## After bootstrap

Activate the environment:

```bash
source /root/.venv-langv1/bin/activate
```

Recommended runtime flags for long jobs:

```bash
export HF_ENDPOINT=https://hf-mirror.com
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONUNBUFFERED=1
```

Run the self-check again if needed:

```bash
cd /root/workspaces/entropy_tokenizer_v2
python scripts/check_lang_v1_pilot.py
```

## Notes

- The bootstrap now prefers the server's existing CUDA Python stack over a new
  Miniforge install.
- If the inherited Python stack does not expose `torch` inside the `venv`, the
  script falls back to an explicit `torch` install.
- The Tsinghua mirror is used first for Python packages, but the script falls
  back to `pypi.org` for small packages missing from the mirror.
- `bitsandbytes` is only installed on the Linux server path.
- Keep `HF_TOKEN` empty unless you need gated models or Hub push.
