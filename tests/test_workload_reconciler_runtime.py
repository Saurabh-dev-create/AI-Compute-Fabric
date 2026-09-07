from unittest.mock import Mock

import pytest

from compute_fabric.execution.workload_reconciler_runtime import (
    WorkloadReconcilerRuntime,
)


def test_runtime_reconciles_before_waiting():
    reconciler = Mock()
    wait = Mock(return_value=True)

    runtime = WorkloadReconcilerRuntime(
        reconciler=reconciler,
        interval_seconds=5,
        wait=wait,
    )

    runtime.run()

    reconciler.reconcile_once.assert_called_once_with()
    wait.assert_called_once_with(5)


def test_runtime_rejects_non_positive_interval():
    reconciler = Mock()
    wait = Mock()

    with pytest.raises(
        ValueError,
        match="interval_seconds must be greater than zero",
    ):
        WorkloadReconcilerRuntime(
            reconciler=reconciler,
            interval_seconds=0,
            wait=wait,
        )


def test_runtime_repeats_until_stop_requested():
    reconciler = Mock()
    wait = Mock(side_effect=[False, True])

    runtime = WorkloadReconcilerRuntime(
        reconciler=reconciler,
        interval_seconds=3,
        wait=wait,
    )

    runtime.run()

    assert reconciler.reconcile_once.call_count == 2
    assert wait.call_count == 2
    wait.assert_called_with(3)



def test_runtime_retries_after_reconciliation_pass_failure():
    reconciler = Mock()
    reconciler.reconcile_once.side_effect = [
        RuntimeError("temporary repository failure"),
        1,
    ]

    wait = Mock(side_effect=[False, True])

    runtime = WorkloadReconcilerRuntime(
        reconciler=reconciler,
        interval_seconds=5,
        wait=wait,
    )

    runtime.run()

    assert reconciler.reconcile_once.call_count == 2
    assert wait.call_count == 2
