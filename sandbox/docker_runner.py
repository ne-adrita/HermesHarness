import docker


def run_python_code(code: str):
    client = docker.from_env()

    container = client.containers.run(
        image="python:3.11",
        command=f'python -c "{code}"',
        detach=True,
        remove=False
    )

    # Wait until the container finishes
    result = container.wait()

    # Read the logs
    output = container.logs().decode("utf-8")

    # Remove the container
    container.remove()

    return output