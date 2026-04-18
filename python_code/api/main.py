import time
import uuid
import traceback
import structlog
from agent_controller import AgentController
import runpod

log = structlog.get_logger()
agent_controller = AgentController()


async def handler(event):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    log.info("request_start", request_id=request_id)
    try:
        response = await agent_controller.get_response(event)
        log.info("request_complete", request_id=request_id, total_ms=round((time.perf_counter() - start) * 1000))
        return response
    except Exception as e:
        log.error("request_error", request_id=request_id, error=str(e), detail=traceback.format_exc())
        raise


def main():
    runpod.serverless.start({"handler": handler})


if __name__ == "__main__":
    main()