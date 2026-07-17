import docker


def run_python_code(code: str):
    client = docker.from_env()

    container = client.containers.run(
        image="python:3.11",
        command=f'python -c "{code}"',
        detach=True,
        stdout=True,
        stderr=True,
        remove=False,
    )

    # Wait until execution finishes
    result = container.wait()

    # Get output
    logs = container.logs(
        stdout=True,
        stderr=True
    ).decode("utf-8")

    exit_code = result["StatusCode"]

    if exit_code == 0:
        status = "success"
        stdout = logs
        stderr = ""
    else:
        status = "failed"
        stdout = ""
        stderr = logs

    container.remove()

    return {
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
    }

# -------------------------
# Test the function
# -------------------------

if __name__ == "__main__":
 result = run_python_code("""
print('Hello from Docker!')
""")

print(result)