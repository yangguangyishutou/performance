#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${LANGV1_REPO_DIR:-$(pwd)}"
VENV_DIR="${LANGV1_VENV_DIR:-/root/.venv-langv1}"
BASE_PYTHON="${LANGV1_BASE_PYTHON:-}"
TORCH_VARIANT="${LANGV1_TORCH_VARIANT:-cu128}"
USE_SYSTEM_SITE_PACKAGES="${LANGV1_USE_SYSTEM_SITE_PACKAGES:-1}"
INSTALL_BNB="${LANGV1_INSTALL_BNB:-1}"
INSTALL_HUMANEVAL="${LANGV1_INSTALL_HUMANEVAL:-1}"
PIP_INDEX_URL="${LANGV1_PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
PIP_FALLBACK_INDEX_URL="${LANGV1_PIP_FALLBACK_INDEX_URL:-https://pypi.org/simple}"
HF_ENDPOINT_DEFAULT="${LANGV1_HF_ENDPOINT:-https://hf-mirror.com}"

log() {
  printf '[langv1-remote] %s\n' "$*"
}

install_base_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    log "installing base apt packages"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y \
      bash \
      bzip2 \
      build-essential \
      ca-certificates \
      curl \
      git \
      python3 \
      python3-venv \
      tmux \
      unzip \
      wget
    return
  fi
  log "apt-get not found; please install curl/git/python/build tools manually"
  exit 1
}

detect_base_python() {
  if [ -n "${BASE_PYTHON}" ] && [ -x "${BASE_PYTHON}" ]; then
    printf '%s\n' "${BASE_PYTHON}"
    return
  fi
  if [ -x /root/miniconda3/bin/python ]; then
    printf '%s\n' /root/miniconda3/bin/python
    return
  fi
  if [ -x /opt/conda/bin/python ]; then
    printf '%s\n' /opt/conda/bin/python
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi
  log "no usable base python found"
  exit 1
}

ensure_venv() {
  local base_python
  base_python="$(detect_base_python)"
  log "base python: ${base_python}"
  if [ -x "${VENV_DIR}/bin/python" ]; then
    log "venv already present at ${VENV_DIR}"
    return
  fi
  mkdir -p "$(dirname "${VENV_DIR}")"
  if [ "${USE_SYSTEM_SITE_PACKAGES}" = "1" ]; then
    log "creating venv with --system-site-packages at ${VENV_DIR}"
    "${base_python}" -m venv --system-site-packages "${VENV_DIR}"
  else
    log "creating isolated venv at ${VENV_DIR}"
    "${base_python}" -m venv "${VENV_DIR}"
  fi
}

activate_venv() {
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"
}

pip_install_index() {
  local index_url=$1
  shift
  python -m pip install --progress-bar off -i "${index_url}" "$@"
}

ensure_torch() {
  if python - <<'PY'
import torch
print(f"torch={torch.__version__} cuda={torch.cuda.is_available()}")
PY
  then
    log "reusing existing torch from the server image"
    return
  fi
  log "torch is not importable in the venv; falling back to explicit install (${TORCH_VARIANT})"
  python -m pip install --progress-bar off torch --index-url "https://download.pytorch.org/whl/${TORCH_VARIANT}"
  python - <<'PY'
import torch
print(f"torch={torch.__version__} cuda={torch.cuda.is_available()}")
PY
}

install_python_deps() {
  log "installing setuptools/wheel from ${PIP_INDEX_URL}"
  pip_install_index "${PIP_INDEX_URL}" "setuptools<82" wheel

  log "installing repo requirements"
  if ! pip_install_index "${PIP_INDEX_URL}" -r "${REPO_DIR}/requirements-langv1-pilot.txt"; then
    log "mirror install incomplete; retrying repo requirements from ${PIP_FALLBACK_INDEX_URL}"
    pip_install_index "${PIP_FALLBACK_INDEX_URL}" -r "${REPO_DIR}/requirements-langv1-pilot.txt"
  fi

  if [ "${INSTALL_BNB}" = "1" ]; then
    log "installing bitsandbytes"
    if ! pip_install_index "${PIP_INDEX_URL}" bitsandbytes; then
      pip_install_index "${PIP_FALLBACK_INDEX_URL}" bitsandbytes
    fi
  fi

  if [ "${INSTALL_HUMANEVAL}" = "1" ]; then
    log "installing human-eval"
    if ! python -m pip install --progress-bar off \
      "git+https://github.com/openai/human-eval.git" \
      --no-build-isolation; then
      python - <<'PY'
import importlib.util
import sys

sys.exit(0 if importlib.util.find_spec("human_eval") else 1)
PY
    fi
  fi
}

prepare_repo_dirs() {
  mkdir -p "${REPO_DIR}/results/langv1_pilot"
  mkdir -p "${REPO_DIR}/cache/langv1_pilot"
  mkdir -p "${REPO_DIR}/data/langv1_pilot"
}

print_gpu_summary() {
  if command -v nvidia-smi >/dev/null 2>&1; then
    log "GPU summary"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
  fi
}

main() {
  install_base_packages
  export HF_ENDPOINT="${HF_ENDPOINT:-${HF_ENDPOINT_DEFAULT}}"
  ensure_venv
  activate_venv
  ensure_torch
  install_python_deps
  prepare_repo_dirs
  print_gpu_summary

  log "running environment self-check"
  (cd "${REPO_DIR}" && python scripts/check_lang_v1_pilot.py)

  log "done"
  log "activate later with:"
  log "source ${VENV_DIR}/bin/activate"
  log "recommended runtime flags:"
  log "HF_ENDPOINT=${HF_ENDPOINT_DEFAULT} PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONUNBUFFERED=1"
}

main "$@"
