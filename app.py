from sandbox.docker_runner import run_python_code

result = run_python_code(
    "print('Hello from Hermes Harness!')"
)

print(result)