# Hermes Closed-Loop Boundary Mapping Harness

**CSE499A Capstone Project**

A self-improving execution harness around Hermes-3.  The agent executes
Python code inside Docker; execution failures are captured and, in later
stages, converted to negative constraints in a vector database.

---

## Stage 1 – Runtime Isolation & Execution Sandbox

### Purpose

Run arbitrary Python code safely inside a Docker container, capture every
aspect of the execution result, and provide a LangGraph workflow that
future stages will extend with memory, reflection, and LLM integration.

### Architecture

```
HermesHarness/
├── sandbox/
│   ├── __init__.py           # package marker
│   └── docker_runner.py      # core: run_python_code()
├── agent/
│   ├── __init__.py           # package marker
│   ├── state.py              # AgentState TypedDict
│   ├── nodes.py              # execute_code node
│   └── graph.py              # LangGraph workflow builder
├── main.py                   # entry point
├── tests/
│   └── test_stage1.py        # 9 verification tests
├── requirements.txt
└── README.md
```

### Workflow

```
START
  │
  ▼
execute_code  ── calls ──► run_python_code()
  │                          │
  │                     Docker container
  │                     (python:3.11, sandboxed)
  │                          │
  │                     {stdout, stderr,
  │                      status, exit_code}
  │
  ▼
END  ── returns updated AgentState
```

### How to Run

```bash
# Activate the virtual environment (create it first if needed)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the entry point
python main.py

# Run the test suite
python tests/test_stage1.py
```

### Security

Every container is launched with:

- `network_disabled=True`   – no internet access
- `read_only=True`          – read-only root filesystem
- `mem_limit="512m"`        – RAM cap (prevents OOM)
- `nano_cpus=1e9`           – CPU cap (1 core)
- `pids_limit=64`           – process limit (fork-bomb protection)
- `cap_drop=["ALL"]`        – zero Linux capabilities
- `no-new-privileges:true`  – blocks privilege escalation
- 30-second execution timeout (configurable)

### What's Next

- **Stage 2:** ChromaDB integration – store execution failures as
  embedding vectors for similarity-based retrieval.
- **Stage 3:** Reflection loop – the agent retries failed code after
  consulting the constraint store.
