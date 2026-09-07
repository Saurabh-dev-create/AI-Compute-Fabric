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
