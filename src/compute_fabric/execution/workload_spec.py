from dataclasses import dataclass


@dataclass(frozen=True)
class WorkloadSpec:
    image: str
    command: tuple[str, ...] = ()
    args: tuple[str, ...] = ()
