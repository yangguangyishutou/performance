"""One-click setup for the low-cost LangV1 learned-compression pilot."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import textwrap
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQ_FILE = ROOT / "requirements-langv1-pilot.txt"
DEFAULT_VENV = ROOT / ".venv-langv1"
DEFAULT_ENV_FILE = ROOT / ".env.langv1_pilot"

ENV_TEMPLATE = textwrap.dedent(
    """\
    # Low-cost LangV1 learned-compression pilot
    HF_TOKEN=
    ET_LANGV1_BASE_MODEL=Qwen/Qwen2.5-Coder-1.5B
    ET_LANGV1_COMPARE_MODEL=deepseek-ai/deepseek-coder-1.3b-base
    ET_LANGV1_CPT_DATASET=zhensuuu/starcoderdata_100star_py
    ET_LANGV1_CPT_MAX_SAMPLES=50000
    ET_LANGV1_SFT_MAX_SAMPLES=5000
    ET_LANGV1_HUMANEVAL_LIMIT=20
    ET_LANGV1_RESULTS_DIR=./results/langv1_pilot
    ET_LANGV1_CACHE_DIR=./cache/langv1_pilot
    ET_LANGV1_OUTPUT_DIR=./results/langv1_pilot/checkpoints
    """
)


def _python_in_venv(venv_dir: Path) -> Path:
    if platform.system().lower() == "windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(cwd or ROOT))


def _run_human_eval_install(python_bin: Path) -> None:
    cmd = [
        str(python_bin),
        "-m",
        "pip",
        "install",
        "git+https://github.com/openai/human-eval.git",
        "--no-build-isolation",
    ]
    print("+", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode == 0:
        return
    check = subprocess.run(
        [str(python_bin), "-c", "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('human_eval') else 1)"],
        cwd=str(ROOT),
    )
    if check.returncode == 0:
        print("[setup] human_eval import is available; ignoring Windows entry-point packaging error")
        return
    raise subprocess.CalledProcessError(proc.returncode, cmd)


def _detect_torch_variant(requested: str) -> str:
    if requested != "auto":
        return requested
    if shutil.which("nvidia-smi"):
        return "cu128"
    return "cpu"


def _ensure_venv(venv_dir: Path) -> Path:
    python_bin = _python_in_venv(venv_dir)
    if python_bin.exists():
        return python_bin
    print(f"[setup] creating virtual environment at {venv_dir}")
    builder = venv.EnvBuilder(with_pip=True, clear=False, upgrade_deps=False)
    builder.create(str(venv_dir))
    return python_bin


def _install_torch(python_bin: Path, variant: str) -> None:
    if variant == "skip":
        return
    if variant == "cpu":
        index_url = "https://download.pytorch.org/whl/cpu"
    elif variant == "cu128":
        index_url = "https://download.pytorch.org/whl/cu128"
    else:
        raise ValueError(f"unsupported torch variant: {variant}")
    _run(
        [
            str(python_bin),
            "-m",
            "pip",
            "install",
            "torch",
            "--index-url",
            index_url,
        ]
    )


def _write_env_file(path: Path, *, force: bool) -> None:
    if path.exists() and not force:
        print(f"[setup] keeping existing env file: {path}")
        return
    path.write_text(ENV_TEMPLATE, encoding="utf-8")
    print(f"[setup] wrote env file: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up the low-cost LangV1 pilot environment.")
    parser.add_argument("--venv", type=Path, default=DEFAULT_VENV)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--torch", choices=("auto", "cpu", "cu128", "skip"), default="auto")
    parser.add_argument("--skip-human-eval", action="store_true")
    parser.add_argument("--force-env", action="store_true")
    args = parser.parse_args()

    python_bin = _ensure_venv(args.venv)
    _write_env_file(args.env_file, force=args.force_env)
    _run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip", "setuptools<82", "wheel"])
    torch_variant = _detect_torch_variant(args.torch)
    _install_torch(python_bin, torch_variant)
    _run([str(python_bin), "-m", "pip", "install", "-r", str(REQ_FILE)])
    if not args.skip_human_eval:
        _run_human_eval_install(python_bin)

    for rel in ("results/langv1_pilot", "cache/langv1_pilot", "data/langv1_pilot"):
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    print("[setup] running environment self-check")
    _run([str(python_bin), str(ROOT / "scripts" / "check_lang_v1_pilot.py")])

    if platform.system().lower() == "windows":
        activate_cmd = f".\\{args.venv.name}\\Scripts\\Activate.ps1"
    else:
        activate_cmd = f"source {args.venv}/bin/activate"
    print()
    print("[setup] complete")
    print(f"[setup] activate with: {activate_cmd}")
    print(f"[setup] env file: {args.env_file}")


if __name__ == "__main__":
    main()
