from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from compute_fabric.gpu.gpu_report_reconciler_runtime import (
    GPUReportReconcilerRuntime,
)


def test_runtime_expires_stale_gpus_before_waiting() -> None:
    reconciler = Mock()
    wait = Mock(return_value=True)
    now_value = datetime(2026, 9, 8, tzinfo=UTC)
    now = Mock(return_value=now_value)

    runtime = GPUReportReconcilerRuntime(
        reconciler=reconciler,
        stale_after_seconds=60,
        interval_seconds=15,
        now=now,
        wait=wait,
    )

    runtime.run()

    reconciler.expire_stale.assert_called_once_with(
        now=now_value,
        stale_after_seconds=60,
    )
    wait.assert_called_once_with(15)


def test_runtime_retries_after_expiry_failure() -> None:
    reconciler = Mock()
    reconciler.expire_stale.side_effect = [
        RuntimeError("temporary failure"),
        1,
    ]

    wait = Mock(side_effect=[False, True])
    now = Mock(
        side_effect=[
            datetime(2026, 9, 8, 0, 0, 0, tzinfo=UTC),
            datetime(2026, 9, 8, 0, 0, 15, tzinfo=UTC),
        ]
    )

    runtime = GPUReportReconcilerRuntime(
        reconciler=reconciler,
        stale_after_seconds=60,
        interval_seconds=15,
        now=now,
        wait=wait,
    )

    runtime.run()

    assert reconciler.expire_stale.call_count == 2
    assert wait.call_count == 2


@pytest.mark.parametrize(
    ("stale_after_seconds", "interval_seconds", "message"),
    [
        (
            0,
            15,
            "stale_after_seconds must be greater than zero",
        ),
        (
            60,
            0,
            "interval_seconds must be greater than zero",
        ),
    ],
)
def test_runtime_rejects_non_positive_configuration(
    stale_after_seconds,
    interval_seconds,
    message,
) -> None:
    with pytest.raises(ValueError, match=message):
        GPUReportReconcilerRuntime(
            reconciler=Mock(),
            stale_after_seconds=stale_after_seconds,
            interval_seconds=interval_seconds,
            now=Mock(),
            wait=Mock(),
        )
