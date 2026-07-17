import logging

from langgraph.graph import StateGraph, START, END

from agent.state import AgentState
from agent.nodes import execute_code

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """Construct the Stage-1 execution workflow.

    The graph is deliberately minimal::

        START → execute_code → END

    ``execute_code`` calls ``run_python_code()`` from the Docker sandbox
    and writes the result back into the shared agent state.

    Returns:
        A compiled ``StateGraph`` ready for ``.invoke()``.
    """
    builder = StateGraph(AgentState)

    builder.add_node("execute_code", execute_code)

    builder.add_edge(START, "execute_code")
    builder.add_edge("execute_code", END)

    graph = builder.compile()

    logger.info("LangGraph workflow compiled successfully")
    return graph
