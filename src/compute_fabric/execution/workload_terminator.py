from typing import Literal, Protocol


class WorkloadTerminator(Protocol):
    def terminate(
        self,
        workload_id: str,
        execution_mode: Literal["batch", "service"] = "batch",
    ) -> None:
        ...
