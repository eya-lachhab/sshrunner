# sshrunner 🚀

A lightweight Python module for running commands across multiple servers simultaneously over SSH — with parallel execution, jump host support, per-host log saving, and an interactive broadcast shell.

---

## Features

* ⚡ **Parallel execution** — runs commands on all hosts concurrently via threads
* 🔐 **SSH key & jump host support** — works with bastion/proxy servers
* 📁 **Per-host log files** — timestamped output saved automatically
* 🖥️ **Interactive broadcast mode** — type once, runs everywhere
* 🔧 **Per-host port override** — perfect for Docker/local testing

---

## Installation

```
pip install sshrunner
```

`paramiko>=3.0` is installed automatically as a dependency.

---

## Quick Start

```python
from sshrunner import SSHRunner

runner = SSHRunner(
    hosts=["web1.example.com", "web2.example.com", "db1.example.com"],
    username="deploy",
    key_path="~/.ssh/id_rsa",
    output_dir="./ssh_logs",
)

results = runner.run("uptime")
runner.print_results(results)
```

`runner.run()` returns a list of `HostResult` objects, one per host. Each result exposes:

| Attribute | Type | Description |
| --- | --- | --- |
| `host` | `str` | Host address (and port if non-default) |
| `stdout` | `str` | Standard output from the command |
| `stderr` | `str` | Standard error from the command |
| `exit_code` | `int \| None` | Exit code returned by the remote command |
| `error` | `str \| None` | Connection or execution error message, if any |
| `duration` | `float` | Time taken in seconds |
| `ok` | `bool` | `True` if no error and `exit_code == 0` |

---

## Docker Testing

Spin up local SSH containers for testing without real servers:

```
docker-compose -f docker-compose.test.yml up -d
python examples/test_docker.py
```

See `docker-compose.test.yml` and `examples/test_docker.py` for full details.

---

## Per-host port support

```python
from sshrunner import SSHRunner, Host

runner = SSHRunner(
    hosts=[
        Host("localhost", port=2221),
        Host("localhost", port=2222),
        Host("localhost", port=2223),
    ],
    username="testuser",
    password="testpass",
)
```

---

## Jump host (bastion)

```python
runner = SSHRunner(
    hosts=["10.0.1.10", "10.0.1.11"],
    username="deploy",
    key_path="~/.ssh/id_rsa",
    jump_host="bastion.mycompany.com",
    jump_username="bastion-user",   # defaults to username if omitted
    jump_key_path="~/.ssh/bastion_rsa",  # defaults to key_path if omitted
    jump_port=22,  # defaults to 22
)
```

---

## Interactive broadcast mode

```python
runner.interactive()
# all> tail -f /var/log/app.log   ← runs on every host simultaneously
```

Type `exit` or press `Ctrl-C` to close all sessions.

---

## Configuration Reference

### `SSHRunner`

| Parameter | Default | Description |
| --- | --- | --- |
| `hosts` | — | List of hostnames, IPs, or `Host(addr, port)` objects |
| `username` | — | SSH username |
| `key_path` | `None` | Path to private key (`~` expanded) |
| `password` | `None` | Password auth (key preferred) |
| `port` | `22` | Default SSH port for all hosts |
| `jump_host` | `None` | Bastion/jump host address |
| `jump_username` | `username` | SSH username for the jump host |
| `jump_key_path` | `key_path` | Private key for the jump host |
| `jump_port` | `22` | SSH port for the jump host |
| `output_dir` | `None` | Directory to save per-host log files |
| `connect_timeout` | `10` | Connection timeout in seconds |
| `max_workers` | `20` | Max parallel threads |

### `print_results(results, show_stderr=True)`

| Parameter | Default | Description |
| --- | --- | --- |
| `results` | — | List of `HostResult` objects returned by `run()` |
| `show_stderr` | `True` | Whether to print stderr output for each host |

---

## Roadmap

* YAML/JSON host inventory file support
* CLI interface (`sshrunner --hosts-file servers.yml "uptime"`)
* Colored terminal output
* Retry logic for flaky connections
* Async backend option (`asyncssh`)

---

## Requirements

* Python 3.10+
* [paramiko](https://www.paramiko.org/) >= 3.0

---

## License

MIT
