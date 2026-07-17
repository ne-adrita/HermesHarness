import docker
import threading
from docker.errors import DockerException
from typing import Dict, Optional


def run_python_code(
    code: str,
    timeout: Optional[int] = 30,
    memory_limit: str = "512m",
    cpu_limit: float = 1.0,
) -> Dict[str, object]:
    """
    Execute Python code inside a sandboxed Docker container.

    Spins up a python:3.11 container with strict security constraints,
    runs the provided code via `exec_run` with demultiplexed stdout/stderr,
    and guarantees resource cleanup even on failure.

    Args:
        code:          The Python source code to execute.
        timeout:       Max execution time in seconds (None = wait indefinitely).
        memory_limit:  Container memory limit, e.g. "512m", "1g".
        cpu_limit:     CPU limit expressed as a fraction of one core (e.g. 0.5).

    Returns:
        A dictionary with keys: status, stdout, stderr, exit_code.

    Raises:
        DockerException: If Docker is unreachable or the image cannot be
                         pulled (the caller should handle this at a higher
                         level, e.g. with a retry or fallback).
    """
    client = docker.from_env()

    # Start a persistent sidecar container that stays alive while we exec
    # commands into it.  The list form of command bypasses the shell,
    # preventing shell-injection attacks.
    container = client.containers.run(
        image="python:3.11",
        command=["sleep", "infinity"],
        detach=True,
        # --- Security hardening ---
        network_disabled=True,                    # No network access
        read_only=True,                           # Read-only root filesystem
        mem_limit=memory_limit,                   # Prevent memory exhaustion
        nano_cpus=int(cpu_limit * 1e9),           # CPU quota in nanokernels
        pids_limit=64,                            # Fork bomb protection
        cap_drop=["ALL"],                         # Drop every Linux capability
        security_opt=["no-new-privileges:true"],  # Block privilege escalation
    )

    try:
        result_box: list = []
        error_box: list = []

        def target() -> None:
            """Run the user code inside the container via exec_run."""
            try:
                exit_code, output = container.exec_run(
                    ["python3", "-c", code],
                    demux=True,
                    stdout=True,
                    stderr=True,
                )
                result_box.append((exit_code, output))
            except Exception as exc:
                error_box.append(exc)

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            # The exec did not finish within the timeout; kill the
            # container (which kills the exec along with it).
            try:
                container.kill()
            except DockerException:
                pass
            thread.join(timeout=5)
            return {
                "status": "error",
                "stdout": "",
                "stderr": "Execution timed out",
                "exit_code": -1,
            }

        if error_box:
            raise error_box[0]

        exit_code, output = result_box[0]

        # output is a 2-tuple (stdout_bytes | None, stderr_bytes | None)
        stdout_bytes, stderr_bytes = output if output else (b"", b"")
        stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
        status = "success" if exit_code == 0 else "failed"

        return {
            "status": status,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
        }

    finally:
        # Guarantee the container is removed, even if an exception occurred
        # above. force=True sends SIGKILL if the container is still running.
        try:
            container.remove(force=True)
        except DockerException:
            pass


if __name__ == "__main__":
    result = run_python_code("print('Hello from Docker!')")
    print(result)

    result = run_python_code("print(10/0)")
    print(result)