from collections.abc import Callable

import httpx

from compute_fabric.gpu.gpu_agent_config import GPUAgentConfig
from compute_fabric.gpu.gpu_agent_main import build_gpu_agent_runtime
from compute_fabric.gpu.gpu_agent_runtime import GPUAgentRuntime
from compute_fabric.gpu.nvidia_gpu_collector import NvidiaGPUCollector
from compute_fabric.gpu.gpu_report_sender import HTTPGPUReportSender


def test_build_gpu_agent_runtime_wires_components() -> None:
    config = GPUAgentConfig(
        node_id="eks-gpu-node-01",
        control_plane_url="http://compute-fabric-api:8000",
        interval_seconds=15,
    )

    sleep: Callable[[float], object] = lambda _: None
    should_stop = lambda: True

    with httpx.Client() as client:
        runtime = build_gpu_agent_runtime(
            config=config,
            client=client,
            sleep=sleep,
            should_stop=should_stop,
        )

    assert isinstance(runtime, GPUAgentRuntime)
    assert runtime.interval_seconds == 15
    assert runtime.sleep is sleep
    assert runtime.should_stop is should_stop

    agent = runtime.agent

    assert isinstance(agent.collector, NvidiaGPUCollector)
    assert agent.collector.node_id == "eks-gpu-node-01"

    sender = agent.report_handler.__self__

    assert isinstance(sender, HTTPGPUReportSender)
    assert sender.base_url == "http://compute-fabric-api:8000"
    assert sender.client is client
