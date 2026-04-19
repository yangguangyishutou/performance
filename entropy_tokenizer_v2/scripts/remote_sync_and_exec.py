"""Sync the local repo to a remote Linux host and optionally run a command."""

from __future__ import annotations

import argparse
import fnmatch
import os
import shlex
import socket
import tarfile
import tempfile
import time
from pathlib import Path

import paramiko


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REMOTE_DIR = "/root/workspaces/entropy_tokenizer_v2"
DEFAULT_REMOTE_ARCHIVE = "/tmp/entropy_tokenizer_v2_sync.tar.gz"
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
    "*.pyc",
)


def _should_exclude(rel_path: str, patterns: tuple[str, ...]) -> bool:
    norm = rel_path.replace("\\", "/").lstrip("./")
    for pattern in patterns:
        if fnmatch.fnmatch(norm, pattern):
            return True
    return False


def _build_archive(output_path: Path, *, excludes: tuple[str, ...]) -> Path:
    with tarfile.open(output_path, "w:gz") as tar:
        for root_dir, dirnames, filenames in os.walk(ROOT):
            root_path = Path(root_dir)
            rel_root = root_path.relative_to(ROOT)
            rel_root_posix = rel_root.as_posix() if rel_root != Path(".") else ""

            kept_dirs: list[str] = []
            for dirname in dirnames:
                rel_dir = f"{rel_root_posix}/{dirname}" if rel_root_posix else dirname
                if _should_exclude(rel_dir, excludes):
                    continue
                kept_dirs.append(dirname)
            dirnames[:] = kept_dirs

            for filename in filenames:
                rel_file = f"{rel_root_posix}/{filename}" if rel_root_posix else filename
                if _should_exclude(rel_file, excludes):
                    continue
                tar.add(root_path / filename, arcname=rel_file, recursive=False)
    return output_path


def _connect(
    *,
    host: str,
    port: int,
    username: str,
    password: str | None,
    key_file: str | None,
    timeout: float,
) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connect_kwargs: dict[str, object] = {
        "hostname": host,
        "port": int(port),
        "username": username,
        "timeout": float(timeout),
    }
    if key_file:
        connect_kwargs["key_filename"] = key_file
    elif password:
        connect_kwargs["password"] = password
    else:
        raise ValueError("either password or key_file is required")
    client.connect(**connect_kwargs)
    return client


def _emit_chunks(text: str, *, buffer: list[str]) -> None:
    if not text:
        return
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = normalized.split("\n")
    if len(parts) == 1:
        buffer[0] += parts[0]
        return
    for piece in parts[:-1]:
        print(buffer[0] + piece, flush=True)
        buffer[0] = ""
    buffer[0] = parts[-1]


def _flush_tail(buffer: list[str]) -> None:
    if buffer[0]:
        print(buffer[0], flush=True)
        buffer[0] = ""


def _run_stream(client: paramiko.SSHClient, command: str, *, read_timeout: float) -> int:
    transport = client.get_transport()
    if transport is None:
        raise RuntimeError("SSH transport is unavailable")
    channel = transport.open_session()
    channel.get_pty()
    channel.settimeout(float(read_timeout))
    channel.exec_command(command)

    out_buf = [""]
    err_buf = [""]
    while True:
        made_progress = False
        try:
            if channel.recv_ready():
                chunk = channel.recv(8192).decode("utf-8", errors="replace")
                _emit_chunks(chunk, buffer=out_buf)
                made_progress = True
            if channel.recv_stderr_ready():
                chunk = channel.recv_stderr(8192).decode("utf-8", errors="replace")
                _emit_chunks(chunk, buffer=err_buf)
                made_progress = True
        except socket.timeout:
            pass

        if channel.exit_status_ready():
            if not channel.recv_ready() and not channel.recv_stderr_ready():
                break

        if not made_progress:
            time.sleep(0.2)

    _flush_tail(out_buf)
    _flush_tail(err_buf)
    return channel.recv_exit_status()


def _shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", default=None)
    parser.add_argument("--key-file", default=None)
    parser.add_argument("--remote-dir", default=DEFAULT_REMOTE_DIR)
    parser.add_argument("--remote-archive", default=DEFAULT_REMOTE_ARCHIVE)
    parser.add_argument("--run", default=None, help="Command to run inside the remote repo after sync.")
    parser.add_argument("--no-sync", action="store_true", help="Skip upload/extract and only run the command.")
    parser.add_argument("--venv", default=".venv-langv1", help="Remote virtualenv path relative to the repo.")
    parser.add_argument("--connect-timeout", type=float, default=20.0)
    parser.add_argument("--read-timeout", type=float, default=0.5)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="etv2_sync_") as tmpdir:
        archive_path = Path(tmpdir) / "entropy_tokenizer_v2_sync.tar.gz"
        if not args.no_sync:
            print(f"[sync] building archive from {ROOT}", flush=True)
            _build_archive(archive_path, excludes=DEFAULT_EXCLUDES)

        client = _connect(
            host=args.host,
            port=args.port,
            username=args.user,
            password=args.password,
            key_file=args.key_file,
            timeout=args.connect_timeout,
        )
        try:
            if not args.no_sync:
                print(f"[sync] uploading archive to {args.remote_archive}", flush=True)
                sftp = client.open_sftp()
                try:
                    sftp.put(str(archive_path), str(args.remote_archive))
                finally:
                    sftp.close()

                extract_cmd = _shell_join(
                    [
                        "bash",
                        "-lc",
                        f"mkdir -p {shlex.quote(args.remote_dir)} && "
                        f"tar -xzf {shlex.quote(args.remote_archive)} "
                        f"-C {shlex.quote(args.remote_dir)} --overwrite",
                    ]
                )
                code = _run_stream(client, extract_cmd, read_timeout=args.read_timeout)
                if code != 0:
                    print(f"[remote-exit] {code}", flush=True)
                    return int(code)

            if args.run:
                repo_dir_q = shlex.quote(args.remote_dir)
                venv_path_q = shlex.quote(f"{args.remote_dir}/{args.venv}".replace("//", "/"))
                run_cmd = (
                    f"cd {repo_dir_q} && "
                    f"source {venv_path_q}/bin/activate && "
                    f"{args.run}"
                )
                code = _run_stream(
                    client,
                    _shell_join(["bash", "-lc", run_cmd]),
                    read_timeout=args.read_timeout,
                )
                print(f"[remote-exit] {code}", flush=True)
                return int(code)

            print("[remote-exit] 0", flush=True)
            return 0
        finally:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
