from dataclasses import dataclass
from enum import Enum
from typing import Literal, Protocol


class WorkloadRuntimeStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class WorkloadObservation:
    workload_id: str
    status: WorkloadRuntimeStatus


class WorkloadObserver(Protocol):
    def observe(
        self,
        workload_id: str,
        execution_mode: Literal["batch", "service"] = "batch",
    ) -> WorkloadObservation:
        ...
