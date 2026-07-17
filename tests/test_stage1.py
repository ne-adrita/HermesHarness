"""
Stage 1 verification tests for the Hermes Closed-Loop Boundary Mapping Harness.

Tests cover:
  1. Successful execution
  2. Runtime exception (ZeroDivisionError)
  3. SyntaxError capture
  4. Timeout protection
  5. Stdout correctness
  6. Stderr correctness
  7. Exit code correctness
  8. Container auto-removal
"""

import sys
import time

sys.path.insert(0, ".")

from sandbox.docker_runner import run_python_code


HEADER = "\033[95m"
OK = "\033[92m"
FAIL = "\033[91m"
BOLD = "\033[1m"
END = "\033[0m"


def section(title: str) -> None:
    print(f"\n{BOLD}{'=' * 72}{END}")
    print(f"{BOLD}{title}{END}")
    print(f"{BOLD}{'=' * 72}{END}")


def verdict(test_name: str, passed: bool, expected: str, actual: str) -> None:
    icon = f"{OK}[PASS]{END}" if passed else f"{FAIL}[FAIL]{END}"
    print(f"  {icon} {test_name}")
    print(f"    Expected: {expected}")
    print(f"    Actual:   {actual}")
    print()


# ---------- 1. Successful execution ----------
section("TEST 1: Successful Python execution")

result = run_python_code('print("Hello from Hermes Harness")')

t1_ok = (
    result["status"] == "success"
    and "Hello from Hermes Harness" in result["stdout"]
    and result["exit_code"] == 0
)
verdict(
    "print() produces stdout, exits 0",
    t1_ok,
    "status=success, stdout contains 'Hello from Hermes Harness', exit_code=0",
    f"status={result['status']}, stdout={repr(result['stdout'])}, exit_code={result['exit_code']}",
)

# ---------- 2. Runtime exception (ZeroDivisionError) ----------
section("TEST 2: Runtime exception (ZeroDivisionError)")

result = run_python_code("1 / 0")

t2_ok = (
    result["status"] == "failed"
    and "ZeroDivisionError" in result["stderr"]
    and result["exit_code"] == 1
)
verdict(
    "1/0 raises ZeroDivisionError on stderr, exits 1",
    t2_ok,
    "status=failed, stderr contains 'ZeroDivisionError', exit_code=1",
    f"status={result['status']}, stderr contains 'ZeroDivisionError'={'ZeroDivisionError' in result['stderr']}, exit_code={result['exit_code']}",
)

# ---------- 3. SyntaxError capture ----------
section("TEST 3: SyntaxError capture")

result = run_python_code("print('hello")  # deliberately unclosed quote

t3_ok = (
    result["status"] == "failed"
    and "SyntaxError" in result["stderr"]
    and result["exit_code"] == 1
)
verdict(
    "Unclosed string raises SyntaxError on stderr, exits 1",
    t3_ok,
    "status=failed, stderr contains 'SyntaxError', exit_code=1",
    f"status={result['status']}, stderr contains 'SyntaxError'={'SyntaxError' in result['stderr']}, exit_code={result['exit_code']}",
)

# ---------- 4. Timeout protection ----------
section("TEST 4: Timeout protection")

start = time.time()
result = run_python_code("while True: pass", timeout=5)
elapsed = time.time() - start

t4_ok = (
    result["status"] == "error"
    and result["exit_code"] == -1
    and elapsed < 60  # sanity check: should not hang
)
verdict(
    "Infinite loop is killed at timeout",
    t4_ok,
    "status=error, exit_code=-1, completes within ~5s",
    f"status={result['status']}, exit_code={result['exit_code']}, elapsed={elapsed:.1f}s, stderr={repr(result['stderr'][:120])}",
)

# ---------- 5. Stdout correctness ----------
section("TEST 5: Stdout correctness")

# Use raw string or double-escape to prevent Python from interpreting \n
# inside the triple-quoted string.
result = run_python_code(
    'import sys\n'
    'print("line one")\n'
    'sys.stdout.write("line two\\n")\n'
    'print("line three")\n'
)

stdout_lines = result["stdout"].strip().splitlines()
t5_ok = (
    stdout_lines == ["line one", "line two", "line three"]
    and result["status"] == "success"
    and result["exit_code"] == 0
)
verdict(
    "Multiple print/write calls produce correct ordered stdout",
    t5_ok,
    "stdout = 'line one\\nline two\\nline three\\n'",
    f"stdout = {repr(result['stdout'])}",
)

# ---------- 6. Stderr correctness ----------
section("TEST 6: Stderr correctness")

result = run_python_code(
    'import sys\n'
    'sys.stderr.write("error msg\\n")\n'
    '1 / 0\n'
)

t6_ok = (
    "error msg" in result["stderr"]
    and "ZeroDivisionError" in result["stderr"]
    and result["status"] == "failed"
)
verdict(
    "Both explicit stderr writes and exception traces appear in stderr",
    t6_ok,
    "stderr contains 'error msg' AND 'ZeroDivisionError'",
    f"stderr contains 'error msg'={'error msg' in result['stderr']}, "
    f"stderr contains 'ZeroDivisionError'={'ZeroDivisionError' in result['stderr']}",
)

# ---------- 7. Exit code correctness ----------
section("TEST 7: Exit code correctness")

cases = [
    ("exit(0)", 0, "success"),
    ("exit(42)", 42, "failed"),
    ("1/0", 1, "failed"),
]
t7_ok = True
for code_src, expected_code, expected_status in cases:
    result = run_python_code(code_src)
    ok = result["exit_code"] == expected_code and result["status"] == expected_status
    if not ok:
        t7_ok = False
    verdict(
        f"`{code_src}` -> exit_code={expected_code}, status={expected_status}",
        ok,
        f"exit_code={expected_code}, status={expected_status}",
        f"exit_code={result['exit_code']}, status={result['status']}",
    )

section("SUMMARY (Exit code correctness)")
print(f"  {'All exit code tests passed' if t7_ok else 'Some exit code tests FAILED'}")

# ---------- 8. Container auto-removal ----------
section("TEST 8: Container auto-removal")


def list_hermes_containers() -> list:
    """Return all containers created by the hermes harness."""
    try:
        import docker
        c = docker.from_env()
        return c.containers.list(all=True, filters={"ancestor": "python:3.11"})
    except Exception:
        return []


# Snapshot existing containers before our test
before = list_hermes_containers()

# Run a few iterations to stress-test cleanup
for i in range(3):
    run_python_code(f"print('iteration {i}')")

after = list_hermes_containers()
new_containers = [ct for ct in after if ct not in before]
t8_ok = len(new_containers) == 0
verdict(
    "No python:3.11 containers leak after multiple executions",
    t8_ok,
    "0 new containers created",
    f"{len(new_containers)} new containers: {[c.name for c in new_containers]}",
)

# ---------- Overall ----------
section(f"{BOLD}OVERALL RESULT{END}")

all_passed = all([t1_ok, t2_ok, t3_ok, t4_ok, t5_ok, t6_ok, t7_ok, t8_ok])
if all_passed:
    print(f"  {OK}{BOLD}ALL 8 TESTS PASSED.{END}")
    sys.exit(0)
else:
    print(f"  {FAIL}{BOLD}SOME TESTS FAILED.  Review output above.{END}")
    sys.exit(1)
