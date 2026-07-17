from typing import TypedDict


class AgentState(TypedDict):
    """State passed between LangGraph nodes in the execution workflow.

    Fields:
        code:      The Python source code to execute.
        stdout:    Text captured from the program's standard output.
        stderr:    Text captured from the program's standard error.
        status:    One of "success", "failed", or "error".
        exit_code: Integer exit code returned by the process.
    """
    code: str
    stdout: str
    stderr: str
    status: str
    exit_code: int
