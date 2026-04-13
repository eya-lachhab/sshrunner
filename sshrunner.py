"""
sshrunner.py — Multi-server SSH command runner
------------------------------------------------
Features:
  - Run commands in parallel across multiple servers
  - SSH key & jump host (bastion) support
  - Save output per host to files
  - Interactive broadcast mode (send input to all hosts)
  - Per-host port support

Requirements:
    pip install paramiko

Usage:
    from sshrunner import SSHRunner

    runner = SSHRunner(
        hosts=["web1.example.com", "web2.example.com"],
        username="deploy",
        key_path="~/.ssh/id_rsa",
        output_dir="./ssh_logs",
    )

    results = runner.run("uptime")
    runner.print_results(results)

    # Interactive broadcast mode:
    runner.interactive()
"""

import os
import time
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

try:
    import paramiko
except ImportError:
    raise ImportError("Install paramiko first:  pip install paramiko")


# ──────────────────────────────────────────────
# Data container for per-host results
# ──────────────────────────────────────────────
class HostResult:
    def __init__(self, host: str):
        self.host = host
        self.stdout: str = ""
        self.stderr: str = ""
        self.exit_code: Optional[int] = None
        self.error: Optional[str] = None
        self.duration: float = 0.0

    @property
    def ok(self) -> bool:
        return self.error is None and self.exit_code == 0

    def __repr__(self):
        status = "OK" if self.ok else f"FAIL(exit={self.exit_code})"
        return f"<HostResult {self.host} {status} {self.duration:.2f}s>"


# ──────────────────────────────────────────────
# Host entry supporting per-host port overrides
# ──────────────────────────────────────────────
class Host:
    """
    Can be used as a plain string or with a custom port:
        Host("localhost", port=2221)
        Host("web1.example.com")
    """
    def __init__(self, address: str, port: Optional[int] = None):
        self.address = address
        self.port = port  # None means use SSHRunner default

    def __str__(self):
        return self.address if self.port is None else f"{self.address}:{self.port}"

    @staticmethod
    def parse(h) -> "Host":
        if isinstance(h, Host):
            return h
        return Host(h)


# ──────────────────────────────────────────────
# Core runner
# ──────────────────────────────────────────────
class SSHRunner:
    def __init__(
        self,
        hosts: list,
        username: str,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        port: int = 22,
        jump_host: Optional[str] = None,
        jump_username: Optional[str] = None,
        jump_key_path: Optional[str] = None,
        jump_port: int = 22,
        output_dir: Optional[str] = None,
        connect_timeout: int = 10,
        max_workers: int = 20,
    ):
        self.hosts = [Host.parse(h) for h in hosts]
        self.username = username
        self.key_path = Path(key_path).expanduser() if key_path else None
        self.password = password
        self.default_port = port
        self.jump_host = jump_host
        self.jump_username = jump_username or username
        self.jump_key_path = Path(jump_key_path).expanduser() if jump_key_path else self.key_path
        self.jump_port = jump_port
        self.output_dir = Path(output_dir) if output_dir else None
        self.connect_timeout = connect_timeout
        self.max_workers = max_workers

        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def _connect(self, host: Host) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        port = host.port if host.port is not None else self.default_port

        connect_kwargs = dict(
            username=self.username,
            port=port,
            timeout=self.connect_timeout,
            password=self.password,
        )
        if self.key_path:
            connect_kwargs["key_filename"] = str(self.key_path)

        if self.jump_host:
            jump = paramiko.SSHClient()
            jump.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            jump_kwargs = dict(
                username=self.jump_username,
                port=self.jump_port,
                timeout=self.connect_timeout,
                password=self.password,
            )
            if self.jump_key_path:
                jump_kwargs["key_filename"] = str(self.jump_key_path)
            jump.connect(self.jump_host, **jump_kwargs)
            transport = jump.get_transport()
            channel = transport.open_channel(
                "direct-tcpip", (host.address, port), ("", 0)
            )
            connect_kwargs["sock"] = channel

        client.connect(host.address, **connect_kwargs)
        return client

    def _run_on_host(self, host: Host, command: str) -> HostResult:
        result = HostResult(str(host))
        t0 = time.monotonic()
        try:
            client = self._connect(host)
            _, stdout, stderr = client.exec_command(command)
            result.stdout = stdout.read().decode(errors="replace").strip()
            result.stderr = stderr.read().decode(errors="replace").strip()
            result.exit_code = stdout.channel.recv_exit_status()
            client.close()
        except Exception as exc:
            result.error = str(exc)
        finally:
            result.duration = time.monotonic() - t0

        if self.output_dir:
            self._save_output(result)

        return result

    def _save_output(self, result: HostResult):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_host = result.host.replace(".", "_").replace(":", "_")
        log_file = self.output_dir / f"{safe_host}_{timestamp}.log"
        with open(log_file, "w") as f:
            f.write(f"Host    : {result.host}\n")
            f.write(f"Time    : {timestamp}\n")
            f.write(f"Duration: {result.duration:.2f}s\n")
            f.write(f"Exit    : {result.exit_code}\n")
            if result.error:
                f.write(f"Error   : {result.error}\n")
            f.write("\n── STDOUT ──\n")
            f.write(result.stdout or "(empty)")
            f.write("\n── STDERR ──\n")
            f.write(result.stderr or "(empty)")
            f.write("\n")

    def run(self, command: str) -> list[HostResult]:
        """Run `command` on all hosts concurrently. Returns list of HostResult."""
        results = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(self.hosts))) as pool:
            futures = {pool.submit(self._run_on_host, h, command): h for h in self.hosts}
            for future in as_completed(futures):
                results.append(future.result())
        results.sort(key=lambda r: r.host)
        return results

    def print_results(self, results: list[HostResult], show_stderr: bool = True):
        width = 60
        print()
        for r in results:
            status = "✓" if r.ok else "✗"
            header = f" {status} {r.host}  (exit={r.exit_code}, {r.duration:.2f}s)"
            print("─" * width)
            print(header)
            print("─" * width)
            if r.error:
                print(f"  [CONNECTION ERROR] {r.error}")
            else:
                if r.stdout:
                    for line in r.stdout.splitlines():
                        print(f"  {line}")
                if show_stderr and r.stderr:
                    print("  [stderr]")
                    for line in r.stderr.splitlines():
                        print(f"  {line}")
            print()

    def interactive(self):
        """
        Opens persistent SSH sessions to all hosts.
        Type a command and it runs on ALL hosts simultaneously.
        Type 'exit' or Ctrl-C to quit.
        """
        print(f"\n[sshrunner] Interactive broadcast mode — {len(self.hosts)} host(s)")
        print("[sshrunner] Type a command and press Enter. Type 'exit' to quit.\n")

        sessions: dict[str, paramiko.SSHClient] = {}
        for host in self.hosts:
            try:
                sessions[str(host)] = self._connect(host)
                print(f"  ✓ Connected: {host}")
            except Exception as exc:
                print(f"  ✗ Failed:    {host} — {exc}")
        print()

        if not sessions:
            print("[sshrunner] No hosts connected. Exiting.")
            return

        print_lock = threading.Lock()

        def run_and_print(host_str, client, cmd):
            try:
                _, stdout, stderr = client.exec_command(cmd)
                out = stdout.read().decode(errors="replace").strip()
                err = stderr.read().decode(errors="replace").strip()
                exit_code = stdout.channel.recv_exit_status()
            except Exception as exc:
                out, err, exit_code = "", str(exc), -1
            with print_lock:
                symbol = "✓" if exit_code == 0 else "✗"
                print(f"\n[{symbol} {host_str}]")
                if out:
                    for line in out.splitlines():
                        print(f"  {line}")
                if err:
                    for line in err.splitlines():
                        print(f"  [err] {line}")

        try:
            while True:
                try:
                    cmd = input("all> ").strip()
                except EOFError:
                    break
                if not cmd:
                    continue
                if cmd.lower() in ("exit", "quit"):
                    break

                threads = [
                    threading.Thread(target=run_and_print, args=(h, c, cmd), daemon=True)
                    for h, c in sessions.items()
                ]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                print()

        except KeyboardInterrupt:
            print("\n[sshrunner] Interrupted.")
        finally:
            for client in sessions.values():
                client.close()
            print("[sshrunner] All sessions closed.")


# ──────────────────────────────────────────────
# Quick demo (edit hosts before running)
# ──────────────────────────────────────────────
if __name__ == "__main__":
    runner = SSHRunner(
        hosts=["web1.example.com", "web2.example.com"],
        username="deploy",
        key_path="~/.ssh/id_rsa",
        output_dir="./ssh_logs",
    )
    results = runner.run("uptime")
    runner.print_results(results)
