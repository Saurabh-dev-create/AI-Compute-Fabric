from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class WorkloadSpec:
    image: str
    command: tuple[str, ...] = ()
    args: tuple[str, ...] = ()
    execution_mode: Literal["batch", "service"] = "batch"
    service_port: int | None = None
