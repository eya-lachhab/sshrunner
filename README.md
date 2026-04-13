# sshrunner 🚀

A lightweight Python module for running commands across multiple servers simultaneously over SSH — with parallel execution, jump host support, per-host log saving, and an interactive broadcast shell.

---

## Features

- ⚡ **Parallel execution** — runs commands on all hosts concurrently via threads
- 🔐 **SSH key & jump host support** — works with bastion/proxy servers
- 📁 **Per-host log files** — timestamped output saved automatically
- 🖥️ **Interactive broadcast mode** — type once, runs everywhere
- 🔧 **Per-host port override** — perfect for Docker/local testing

---

## Installation

```bash
pip install paramiko
```

Then drop `sshrunner.py` into your project, or install from PyPI (coming soon):

```bash
pip install sshrunner
```

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

---

## Docker Testing

Spin up local SSH containers for testing without real servers:

```bash
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
    jump_username="bastion-user",
    jump_key_path="~/.ssh/bastion_rsa",
)
```

---

## Interactive broadcast mode

```python
runner.interactive()
# all> tail -f /var/log/app.log   ← runs on every host simultaneously
```

---

## Configuration Reference

| Parameter         | Default | Description                                      |
|-------------------|---------|--------------------------------------------------|
| `hosts`           | —       | List of hostnames, IPs, or `Host(addr, port)`    |
| `username`        | —       | SSH username                                     |
| `key_path`        | `None`  | Path to private key (`~` expanded)               |
| `password`        | `None`  | Password auth (key preferred)                    |
| `port`            | `22`    | Default SSH port                                 |
| `jump_host`       | `None`  | Bastion/jump host address                        |
| `output_dir`      | `None`  | Directory to save per-host log files             |
| `connect_timeout` | `10`    | Connection timeout in seconds                    |
| `max_workers`     | `20`    | Max parallel threads                             |

---

## Roadmap

- [ ] YAML/JSON host inventory file support
- [ ] CLI interface (`sshrunner --hosts-file servers.yml "uptime"`)
- [ ] Colored terminal output
- [ ] Retry logic for flaky connections
- [ ] Async backend option (`asyncssh`)

---

## Requirements

- Python 3.10+
- [paramiko](https://www.paramiko.org/)

---

## License

MIT
