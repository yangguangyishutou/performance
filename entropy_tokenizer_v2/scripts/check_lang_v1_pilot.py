"""Environment self-check for the low-cost learned-compression pilot."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env.langv1_pilot"


def _load_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def _safe_import_version(module_name: str) -> str | None:
    try:
        module = __import__(module_name)
    except Exception:
        return None
    return getattr(module, "__version__", "unknown")


def _query_nvidia() -> list[dict[str, str]] | None:
    if shutil.which("nvidia-smi") is None:
        return None
    cmd = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,driver_version",
        "--format=csv,noheader,nounits",
    ]
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except Exception:
        return None
    rows: list[dict[str, str]] = []
    for line in proc.stdout.splitlines():
        parts = [x.strip() for x in line.split(",")]
        if len(parts) != 3:
            continue
        rows.append(
            {
                "name": parts[0],
                "memory_total_mib": parts[1],
                "driver_version": parts[2],
            }
        )
    return rows or None


def _torch_summary() -> dict[str, object]:
    try:
        import torch
    except Exception as exc:
        return {"installed": False, "error": str(exc)}

    cuda_ok = bool(torch.cuda.is_available())
    device_names = []
    if cuda_ok:
        device_names = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    return {
        "installed": True,
        "version": torch.__version__,
        "cuda_available": cuda_ok,
        "device_count": torch.cuda.device_count(),
        "device_names": device_names,
    }


def _recommendations(summary: dict[str, object]) -> list[str]:
    recs: list[str] = []
    torch_info = summary["torch"]
    env_info = summary["env"]
    if isinstance(torch_info, dict) and not torch_info.get("installed"):
        recs.append("Install PyTorch inside the pilot venv before training or generation.")
    elif isinstance(torch_info, dict) and not torch_info.get("cuda_available"):
        recs.append("CUDA is not active in this Python environment. Local training should stay at 1.5B-scale or move to WSL/Linux/cloud.")
    gpus = summary.get("gpus") or []
    if gpus:
        try:
            mem = max(int(g["memory_total_mib"]) for g in gpus if g.get("memory_total_mib"))
        except Exception:
            mem = 0
        if mem and mem < 10000:
            recs.append("GPU memory is below 10GB. Use Qwen2.5-Coder-1.5B for the first LoRA pilot.")
    else:
        recs.append("No NVIDIA GPU detected. Use this machine for data prep/eval only, or train remotely.")
    if not env_info.get("HF_TOKEN"):
        recs.append("HF_TOKEN is empty. Public models still work, but gated models and HF Jobs will need a token.")
    return recs


def main() -> None:
    env_values = _load_env_file(ENV_FILE)
    env_snapshot = {
        "HF_TOKEN": "***" if env_values.get("HF_TOKEN") else "",
        "ET_LANGV1_BASE_MODEL": env_values.get("ET_LANGV1_BASE_MODEL", ""),
        "ET_LANGV1_CPT_MAX_SAMPLES": env_values.get("ET_LANGV1_CPT_MAX_SAMPLES", ""),
        "ET_LANGV1_SFT_MAX_SAMPLES": env_values.get("ET_LANGV1_SFT_MAX_SAMPLES", ""),
        "ET_LANGV1_HUMANEVAL_LIMIT": env_values.get("ET_LANGV1_HUMANEVAL_LIMIT", ""),
    }
    packages = {
        "transformers": _safe_import_version("transformers"),
        "datasets": _safe_import_version("datasets"),
        "accelerate": _safe_import_version("accelerate"),
        "peft": _safe_import_version("peft"),
        "trl": _safe_import_version("trl"),
        "tiktoken": _safe_import_version("tiktoken"),
        "openai": _safe_import_version("openai"),
    }
    summary = {
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "env": env_snapshot,
        "packages": packages,
        "torch": _torch_summary(),
        "gpus": _query_nvidia(),
    }
    summary["recommendations"] = _recommendations(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
