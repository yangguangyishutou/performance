"""Execute a remote SSH command with incremental streaming via Paramiko."""

from __future__ import annotations

import argparse
import socket
import sys
import time
from pathlib import Path

import paramiko


def _emit_chunks(text: str, *, buffer: list[str], mirror: object | None) -> None:
    if not text:
        return
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = normalized.split("\n")
    if len(parts) == 1:
        buffer[0] += parts[0]
        return
    for piece in parts[:-1]:
        line = buffer[0] + piece
        print(line, flush=True)
        if mirror is not None:
            mirror.write(line + "\n")
            mirror.flush()
        buffer[0] = ""
    buffer[0] = parts[-1]


def _flush_tail(buffer: list[str], mirror: object | None) -> None:
    if not buffer[0]:
        return
    print(buffer[0], flush=True)
    if mirror is not None:
        mirror.write(buffer[0] + "\n")
        mirror.flush()
    buffer[0] = ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--log-file", type=Path, default=None)
    parser.add_argument("--connect-timeout", type=float, default=20.0)
    parser.add_argument("--read-timeout", type=float, default=0.5)
    parser.add_argument("--chunk-size", type=int, default=8192)
    args = parser.parse_args()

    mirror = None
    if args.log_file is not None:
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        mirror = args.log_file.open("w", encoding="utf-8")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=args.host,
            port=int(args.port),
            username=args.user,
            password=args.password,
            timeout=float(args.connect_timeout),
        )
        transport = client.get_transport()
        if transport is None:
            raise RuntimeError("SSH transport is unavailable")
        chan = transport.open_session(timeout=float(args.connect_timeout))
        chan.get_pty()
        chan.settimeout(float(args.read_timeout))
        chan.exec_command(args.command)

        out_buf = [""]
        err_buf = [""]
        while True:
            made_progress = False
            try:
                if chan.recv_ready():
                    chunk = chan.recv(int(args.chunk_size)).decode("utf-8", errors="replace")
                    _emit_chunks(chunk, buffer=out_buf, mirror=mirror)
                    made_progress = True
                if chan.recv_stderr_ready():
                    chunk = chan.recv_stderr(int(args.chunk_size)).decode("utf-8", errors="replace")
                    _emit_chunks(chunk, buffer=err_buf, mirror=mirror)
                    made_progress = True
            except socket.timeout:
                pass

            if chan.exit_status_ready():
                if not chan.recv_ready() and not chan.recv_stderr_ready():
                    break

            if not made_progress:
                time.sleep(0.2)

        _flush_tail(out_buf, mirror)
        _flush_tail(err_buf, mirror)
        status = chan.recv_exit_status()
        print(f"[remote-exit] {status}", flush=True)
        if mirror is not None:
            mirror.write(f"[remote-exit] {status}\n")
            mirror.flush()
        return int(status)
    finally:
        if mirror is not None:
            mirror.close()
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
