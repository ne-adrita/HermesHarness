import logging
import sys

from agent.graph import build_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point: build the graph and run a few test invocations."""
    graph = build_graph()

    # --- Test 1: Successful code -------------------------------------------
    logger.info("=" * 60)
    logger.info("Test 1: Successful code — print('Hello from Hermes!')")
    logger.info("=" * 60)

    result = graph.invoke({
        "code": "print('Hello from Hermes!')",
        "stdout": "",
        "stderr": "",
        "status": "",
        "exit_code": -1,
    })

    logger.info("Final state:")
    print(result)
    print()

    # --- Test 2: Failing code ----------------------------------------------
    logger.info("=" * 60)
    logger.info("Test 2: Failing code — print(10/0)")
    logger.info("=" * 60)

    result = graph.invoke({
        "code": "print(10/0)",
        "stdout": "",
        "stderr": "",
        "status": "",
        "exit_code": -1,
    })

    logger.info("Final state:")
    print(result)


if __name__ == "__main__":
    main()
