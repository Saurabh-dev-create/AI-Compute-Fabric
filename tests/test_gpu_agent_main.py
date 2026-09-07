from collections.abc import Callable
import os
import signal

import httpx

from compute_fabric.gpu.gpu_agent_config import GPUAgentConfig
from compute_fabric.gpu.gpu_agent_main import (
    build_gpu_agent_runtime,
    main,
)
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


def test_main_builds_and_runs_agent_from_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "GPU_AGENT_NODE_ID",
        "eks-gpu-node-01",
    )
    monkeypatch.setenv(
        "GPU_AGENT_CONTROL_PLANE_URL",
        "http://compute-fabric-api:8000",
    )
    monkeypatch.setenv(
        "GPU_AGENT_INTERVAL_SECONDS",
        "15",
    )

    captured = {}

    class FakeRuntime:
        def run(self) -> None:
            captured["ran"] = True

    def fake_builder(
        config,
        client,
        sleep,
        should_stop,
    ):
        captured["config"] = config
        captured["client"] = client
        captured["sleep"] = sleep
        captured["should_stop"] = should_stop
        return FakeRuntime()

    monkeypatch.setattr(
        "compute_fabric.gpu.gpu_agent_main.build_gpu_agent_runtime",
        fake_builder,
    )

    main()

    assert captured["ran"] is True
    assert captured["config"].node_id == "eks-gpu-node-01"
    assert captured["config"].control_plane_url == (
        "http://compute-fabric-api:8000"
    )
    assert captured["config"].interval_seconds == 15.0


def test_main_registers_shutdown_signals(monkeypatch) -> None:
    monkeypatch.setenv(
        "GPU_AGENT_NODE_ID",
        "eks-gpu-node-01",
    )
    monkeypatch.setenv(
        "GPU_AGENT_CONTROL_PLANE_URL",
        "http://compute-fabric-api:8000",
    )

    registered_signals = []

    def fake_signal(signum, handler):
        registered_signals.append(signum)

    monkeypatch.setattr(signal, "signal", fake_signal)

    class FakeRuntime:
        def run(self) -> None:
            pass

    monkeypatch.setattr(
        "compute_fabric.gpu.gpu_agent_main.build_gpu_agent_runtime",
        lambda **_: FakeRuntime(),
    )

    main()

    assert signal.SIGTERM in registered_signals
    assert signal.SIGINT in registered_signals
