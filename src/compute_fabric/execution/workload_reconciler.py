import logging

from compute_fabric.common.enums import JobStatus
from compute_fabric.jobs.job_manager import JobManager
from compute_fabric.jobs.job_orchestrator import JobOrchestrator


logger = logging.getLogger(__name__)


class WorkloadReconciler:
    ACTIVE_STATUSES = {
        JobStatus.SCHEDULED,
        JobStatus.RUNNING,
    }

    def __init__(
        self,
        job_manager: JobManager,
        orchestrator: JobOrchestrator,
    ) -> None:
        self.job_manager = job_manager
        self.orchestrator = orchestrator

    def reconcile_once(self) -> int:
        reconciled = 0

        for job in self.job_manager.list_jobs():
            if job.workload_id is None:
                continue

            if job.status not in self.ACTIVE_STATUSES:
                continue

            try:
                self.orchestrator.reconcile_workload(job.id)
            except Exception:
                logger.exception(
                    "workload_reconciliation_failed job_id=%s",
                    job.id,
                )
                continue

            reconciled += 1

        return reconciled
