"""Package the repo, upload it to a remote Linux GPU server, and bootstrap LangV1."""

from __future__ import annotations

import argparse
import fnmatch
import os
import tarfile
import tempfile
from pathlib import Path

import paramiko


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REMOTE_DIR = "/root/workspaces/entropy_tokenizer_v2"
DEFAULT_EXCLUDES = (
    ".git",
    ".git/*",
    ".venv",
    ".venv/*",
    ".codex",
    ".codex/*",
    ".pytest_cache",
    ".pytest_cache/*",
    ".venv-langv1",
    ".venv-langv1/*",
    "cache",
    "cache/*",
    "data",
    "data/*",
    "results",
    "results/*",
    "artifacts",
    "artifacts/*",
    "stage3/.benchmarks",
    "stage3/.benchmarks/*",
    "__pycache__",
    "__pycache__/*",
    "results_fast_try",
    "results_fast_try/*",
)


def _should_exclude(rel_path: str, patterns: tuple[str, ...]) -> bool:
    norm = rel_path.replace("\\", "/").lstrip("./")
    for pattern in patterns:
        if fnmatch.fnmatch(norm, pattern):
            return True
    return False


def build_archive(output_path: Path, *, excludes: tuple[str, ...]) -> Path:
    with tarfile.open(output_path, "w:gz") as tar:
        for root_dir, dirnames, filenames in os.walk(ROOT):
            root_path = Path(root_dir)
            rel_root = root_path.relative_to(ROOT)
            rel_root_posix = rel_root.as_posix() if rel_root != Path(".") else ""

            keep_dirs: list[str] = []
            for dirname in dirnames:
                rel_dir = f"{rel_root_posix}/{dirname}" if rel_root_posix else dirname
                if _should_exclude(rel_dir, excludes):
                    continue
                keep_dirs.append(dirname)
            dirnames[:] = keep_dirs

            for filename in filenames:
                rel_file = f"{rel_root_posix}/{filename}" if rel_root_posix else filename
                if _should_exclude(rel_file, excludes):
                    continue
                tar.add(root_path / filename, arcname=rel_file, recursive=False)
    return output_path


def _connect(host: str, port: int, username: str, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=username, password=password, timeout=30)
    return client


def _run_stream(client: paramiko.SSHClient, command: str) -> int:
    transport = client.get_transport()
    if transport is None:
        raise RuntimeError("SSH transport not available")
    channel = transport.open_session()
    channel.get_pty()
    channel.exec_command(command)
    while True:
        if channel.recv_ready():
            data = channel.recv(4096)
            if data:
                print(data.decode("utf-8", "replace"), end="")
        if channel.recv_stderr_ready():
            data = channel.recv_stderr(4096)
            if data:
                print(data.decode("utf-8", "replace"), end="")
        if channel.exit_status_ready():
            while channel.recv_ready():
                data = channel.recv(4096)
                if data:
                    print(data.decode("utf-8", "replace"), end="")
            while channel.recv_stderr_ready():
                data = channel.recv_stderr(4096)
                if data:
                    print(data.decode("utf-8", "replace"), end="")
            return channel.recv_exit_status()


def upload_and_bootstrap(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    remote_dir: str,
    archive_path: Path,
    torch_variant: str,
    clean_remote: bool,
) -> None:
    remote_archive = "/tmp/entropy_tokenizer_v2_langv1.tar.gz"
    client = _connect(host, port, username, password)
    try:
        sftp = client.open_sftp()
        try:
            sftp.put(str(archive_path), remote_archive)
        finally:
            sftp.close()

        remote_dir_q = remote_dir.replace("'", "'\"'\"'")
        setup_steps: list[str] = []
        if clean_remote:
            setup_steps.append(f"rm -rf '{remote_dir_q}'")
        setup_steps.extend(
            [
                f"mkdir -p '{remote_dir_q}'",
                f"tar -xzf '{remote_archive}' -C '{remote_dir_q}' --overwrite",
                f"cd '{remote_dir_q}'",
                f"LANGV1_REPO_DIR='{remote_dir_q}' "
                f"LANGV1_TORCH_VARIANT='{torch_variant}' "
                f"bash scripts/setup_lang_v1_remote.sh",
            ]
        )
        setup_cmd = " && ".join(setup_steps)
        code = _run_stream(client, f"bash -lc {setup_cmd!r}")
        if code != 0:
            raise SystemExit(code)
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--remote-dir", default=DEFAULT_REMOTE_DIR)
    parser.add_argument("--torch-variant", default="cu128", choices=("cu124", "cu126", "cu128"))
    parser.add_argument(
        "--clean-remote",
        action="store_true",
        help="Delete the remote workspace before unpacking. Use only for disposable runs.",
    )
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="langv1_remote_") as tmpdir:
        archive_path = Path(tmpdir) / "entropy_tokenizer_v2_langv1.tar.gz"
        build_archive(archive_path, excludes=DEFAULT_EXCLUDES)
        upload_and_bootstrap(
            host=args.host,
            port=args.port,
            username=args.user,
            password=args.password,
            remote_dir=args.remote_dir,
            archive_path=archive_path,
            torch_variant=args.torch_variant,
            clean_remote=bool(args.clean_remote),
        )


if __name__ == "__main__":
    main()
