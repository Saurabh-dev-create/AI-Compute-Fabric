from unittest.mock import Mock

from compute_fabric.common.enums import JobStatus
from compute_fabric.execution.workload_reconciler import WorkloadReconciler
from compute_fabric.jobs.job_manager import Job


def make_job(
    job_id: str,
    status: JobStatus,
    workload_id: str | None,
) -> Job:
    return Job(
        id=job_id,
        job_type="training",
        gpu_type="T4",
        min_vram_gb=4,
        priority=5,
        status=status,
        workload_id=workload_id,
    )


def test_reconcile_once_processes_active_workloads_only():
    job_manager = Mock()
    orchestrator = Mock()

    job_manager.list_jobs.return_value = [
        make_job(
            "scheduled",
            JobStatus.SCHEDULED,
            "compute-fabric-scheduled",
        ),
        make_job(
            "running",
            JobStatus.RUNNING,
            "compute-fabric-running",
        ),
        make_job(
            "pending",
            JobStatus.PENDING,
            "compute-fabric-pending",
        ),
        make_job(
            "completed",
            JobStatus.COMPLETED,
            "compute-fabric-completed",
        ),
        make_job(
            "failed",
            JobStatus.FAILED,
            "compute-fabric-failed",
        ),
        make_job(
            "cancelled",
            JobStatus.CANCELLED,
            "compute-fabric-cancelled",
        ),
        make_job(
            "no-workload",
            JobStatus.SCHEDULED,
            None,
        ),
    ]

    reconciler = WorkloadReconciler(
        job_manager=job_manager,
        orchestrator=orchestrator,
    )

    reconciled = reconciler.reconcile_once()

    assert reconciled == 2

    assert orchestrator.reconcile_workload.call_count == 2
    orchestrator.reconcile_workload.assert_any_call("scheduled")
    orchestrator.reconcile_workload.assert_any_call("running")


def test_reconcile_once_with_no_jobs_returns_zero():
    job_manager = Mock()
    orchestrator = Mock()

    job_manager.list_jobs.return_value = []

    reconciler = WorkloadReconciler(
        job_manager=job_manager,
        orchestrator=orchestrator,
    )

    assert reconciler.reconcile_once() == 0
    orchestrator.reconcile_workload.assert_not_called()



def test_reconcile_once_continues_after_workload_failure():
    job_manager = Mock()
    orchestrator = Mock()

    job_manager.list_jobs.return_value = [
        make_job(
            "failing",
            JobStatus.SCHEDULED,
            "compute-fabric-failing",
        ),
        make_job(
            "healthy",
            JobStatus.RUNNING,
            "compute-fabric-healthy",
        ),
    ]

    orchestrator.reconcile_workload.side_effect = [
        RuntimeError("temporary observation failure"),
        True,
    ]

    reconciler = WorkloadReconciler(
        job_manager=job_manager,
        orchestrator=orchestrator,
    )

    reconciled = reconciler.reconcile_once()

    assert reconciled == 1
    assert orchestrator.reconcile_workload.call_count == 2
    orchestrator.reconcile_workload.assert_any_call("failing")
    orchestrator.reconcile_workload.assert_any_call("healthy")
