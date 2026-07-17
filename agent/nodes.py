import logging

from sandbox.docker_runner import run_python_code
from agent.state import AgentState

logger = logging.getLogger(__name__)


def execute_code(state: AgentState) -> dict:
    """Execute the code in the sandbox and return the results.

    This node is the bridge between the LangGraph workflow and the
    Docker sandbox.  It receives the agent state, calls
    ``run_python_code``, and returns only the fields that changed.

    Args:
        state: The current agent state containing ``code``.

    Returns:
        A partial dict with updated ``stdout``, ``stderr``,
        ``status``, and ``exit_code``.
    """
    code = state["code"]
    logger.info("Executing code (first 80 chars): %s ...", code[:80])

    result = run_python_code(code)

    logger.info("Execution complete — status=%s, exit_code=%d", result["status"], result["exit_code"])

    return {
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "status": result["status"],
        "exit_code": result["exit_code"],
    }
