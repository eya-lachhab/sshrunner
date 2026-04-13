"""
examples/test_docker.py — Test sshrunner against local Docker containers
-------------------------------------------------------------------------
First start the containers:
    docker-compose -f docker-compose.test.yml up -d

Then run:
    python examples/test_docker.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sshrunner import SSHRunner, Host

runner = SSHRunner(
    hosts=[
        Host("localhost", port=2221),
        Host("localhost", port=2222),
        Host("localhost", port=2223),
    ],
    username="testuser",
    password="testpass",
    output_dir="./ssh_logs",
)

print("\n=== uptime ===")
results = runner.run("uptime")
runner.print_results(results)

print("\n=== hostname ===")
results = runner.run("hostname")
runner.print_results(results)

print("\n=== disk usage ===")
results = runner.run("df -h /")
runner.print_results(results)

# Check all passed
failed = [r for r in results if not r.ok]
if failed:
    print(f"\n⚠  {len(failed)} host(s) failed:")
    for r in failed:
        print(f"   {r.host}: {r.error or r.stderr}")
else:
    print("\n✓ All hosts responded successfully!")

# Uncomment to launch interactive broadcast mode:
# runner.interactive()
