from dataclasses import dataclass
from typing import Protocol

from compute_fabric.jobs.job_manager import Job
from compute_fabric.scheduler.scheduler import SchedulingDecision
from compute_fabric.execution.workload_spec import WorkloadSpec


@dataclass(frozen=True)
class WorkloadExecution:
    job_id: str
    workload_id: str
    node_id: str


class WorkloadRunner(Protocol):
    def launch(
        self,
        job: Job,
        decision: SchedulingDecision,
        spec: WorkloadSpec,
    ) -> WorkloadExecution:
        ...
