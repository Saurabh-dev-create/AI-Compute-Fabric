from collections.abc import Callable
from typing import Protocol


class GPUAgentRunner(Protocol):
    def run_once(self) -> int:
        ...


class GPUAgentRuntime:
    def __init__(
        self,
        agent: GPUAgentRunner,
        interval_seconds: float,
        sleep: Callable[[float], object],
        should_stop: Callable[[], bool],
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        self.agent = agent
        self.interval_seconds = interval_seconds
        self.sleep = sleep
        self.should_stop = should_stop

    def run(self) -> None:
        while True:
            self.agent.run_once()

            if self.should_stop():
                return

            self.sleep(self.interval_seconds)
