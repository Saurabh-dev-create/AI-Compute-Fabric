import os
import signal
import time
from collections.abc import Callable

import httpx

from compute_fabric.gpu.gpu_agent import GPUAgent
from compute_fabric.gpu.gpu_agent_config import GPUAgentConfig
from compute_fabric.gpu.gpu_agent_runtime import GPUAgentRuntime
from compute_fabric.gpu.gpu_report_sender import HTTPGPUReportSender
from compute_fabric.gpu.nvidia_gpu_collector import NvidiaGPUCollector


def build_gpu_agent_runtime(
    config: GPUAgentConfig,
    client: httpx.Client,
    sleep: Callable[[float], object],
    should_stop: Callable[[], bool],
) -> GPUAgentRuntime:
    collector = NvidiaGPUCollector(
        node_id=config.node_id,
    )

    sender = HTTPGPUReportSender(
        base_url=config.control_plane_url,
        client=client,
    )

    agent = GPUAgent(
        collector=collector,
        report_handler=sender.send,
    )

    return GPUAgentRuntime(
        agent=agent,
        interval_seconds=config.interval_seconds,
        sleep=sleep,
        should_stop=should_stop,
    )


def main() -> None:
    config = GPUAgentConfig.from_mapping(os.environ)

    shutdown_requested = False

    def request_shutdown(
        signum: int,
        frame: object,
    ) -> None:
        nonlocal shutdown_requested
        shutdown_requested = True

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)

    def should_stop() -> bool:
        return shutdown_requested

    with httpx.Client() as client:
        runtime = build_gpu_agent_runtime(
            config=config,
            client=client,
            sleep=time.sleep,
            should_stop=should_stop,
        )

        runtime.run()


if __name__ == "__main__":
    main()
