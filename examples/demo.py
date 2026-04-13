"""
examples/demo.py — Real server demo
------------------------------------
Edit hosts/credentials below, then run:
    python examples/demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sshrunner import SSHRunner

runner = SSHRunner(
    hosts=["web1.example.com", "web2.example.com", "db1.example.com"],
    username="deploy",
    key_path="~/.ssh/id_rsa",
    # jump_host="bastion.example.com",
    output_dir="./ssh_logs",
)

print("=== disk usage ===")
results = runner.run("df -h /")
runner.print_results(results)

print("=== nginx status ===")
results = runner.run("systemctl is-active nginx")
for r in results:
    symbol = "✓" if r.ok else "✗"
    print(f"  {symbol} {r.host}: {r.stdout or r.error}")

# Uncomment to launch interactive mode:
# runner.interactive()
