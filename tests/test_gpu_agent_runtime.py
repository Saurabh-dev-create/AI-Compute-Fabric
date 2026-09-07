import pytest

from compute_fabric.gpu.gpu_agent_runtime import GPUAgentRuntime


class FakeAgent:
    def __init__(self) -> None:
        self.run_count = 0

    def run_once(self) -> int:
        self.run_count += 1
        return 1


def test_runtime_executes_agent_periodically_until_stop() -> None:
    agent = FakeAgent()
    sleep_calls: list[float] = []

    def should_stop() -> bool:
        return agent.run_count >= 3

    runtime = GPUAgentRuntime(
        agent=agent,
        interval_seconds=5,
        sleep=sleep_calls.append,
        should_stop=should_stop,
    )

    runtime.run()

    assert agent.run_count == 3
    assert sleep_calls == [5, 5]


def test_runtime_stops_without_sleeping_after_final_cycle() -> None:
    agent = FakeAgent()
    sleep_calls: list[float] = []

    def should_stop() -> bool:
        return agent.run_count >= 1

    runtime = GPUAgentRuntime(
        agent=agent,
        interval_seconds=10,
        sleep=sleep_calls.append,
        should_stop=should_stop,
    )

    runtime.run()

    assert agent.run_count == 1
    assert sleep_calls == []


def test_runtime_rejects_non_positive_interval() -> None:
    agent = FakeAgent()

    with pytest.raises(ValueError):
        GPUAgentRuntime(
            agent=agent,
            interval_seconds=0,
            sleep=lambda _: None,
            should_stop=lambda: True,
        )
