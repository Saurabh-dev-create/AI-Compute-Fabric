import pytest

from compute_fabric.execution import factory


def test_execution_backend_defaults_to_none():
    runner = factory.create_workload_runner({})

    assert runner is None


def test_execution_backend_explicit_none():
    runner = factory.create_workload_runner(
        {
            "COMPUTE_FABRIC_EXECUTION_BACKEND": "none",
        }
    )

    assert runner is None


def test_execution_backend_rejects_unknown_backend():
    with pytest.raises(
        RuntimeError,
        match="Unsupported execution backend: invalid",
    ):
        factory.create_workload_runner(
            {
                "COMPUTE_FABRIC_EXECUTION_BACKEND": "invalid",
            }
        )


def test_kubernetes_backend_builds_runner(monkeypatch):
    calls = []

    monkeypatch.setattr(
        factory.config,
        "load_incluster_config",
        lambda: calls.append("configured"),
    )

    fake_batch_api = object()

    monkeypatch.setattr(
        factory.client,
        "BatchV1Api",
        lambda: fake_batch_api,
    )

    runner = factory.create_workload_runner(
        {
            "COMPUTE_FABRIC_EXECUTION_BACKEND": "kubernetes",
            "COMPUTE_FABRIC_WORKLOAD_NAMESPACE": "ai-workloads",
        }
    )

    assert calls == ["configured"]
    assert isinstance(
        runner,
        factory.KubernetesWorkloadRunner,
    )
    assert runner.batch_api is fake_batch_api
    assert runner.namespace == "ai-workloads"


def test_kubernetes_backend_defaults_namespace(monkeypatch):
    monkeypatch.setattr(
        factory.config,
        "load_incluster_config",
        lambda: None,
    )

    fake_batch_api = object()

    monkeypatch.setattr(
        factory.client,
        "BatchV1Api",
        lambda: fake_batch_api,
    )

    runner = factory.create_workload_runner(
        {
            "COMPUTE_FABRIC_EXECUTION_BACKEND": "kubernetes",
        }
    )

    assert runner is not None
    assert runner.namespace == "default"


def test_kubernetes_backend_rejects_empty_namespace():
    with pytest.raises(
        RuntimeError,
        match="COMPUTE_FABRIC_WORKLOAD_NAMESPACE must not be empty",
    ):
        factory.create_workload_runner(
            {
                "COMPUTE_FABRIC_EXECUTION_BACKEND": "kubernetes",
                "COMPUTE_FABRIC_WORKLOAD_NAMESPACE": "   ",
            }
        )


def test_create_workload_observer_none_backend():
    from compute_fabric.execution.factory import create_workload_observer

    assert create_workload_observer({}) is None


def test_create_workload_observer_kubernetes(monkeypatch):
    from unittest.mock import Mock

    from compute_fabric.execution import factory

    batch_api = Mock()

    monkeypatch.setattr(
        factory.config,
        "load_incluster_config",
        Mock(),
    )
    monkeypatch.setattr(
        factory.client,
        "BatchV1Api",
        Mock(return_value=batch_api),
    )

    observer = factory.create_workload_observer(
        {
            "COMPUTE_FABRIC_EXECUTION_BACKEND": "kubernetes",
            "COMPUTE_FABRIC_WORKLOAD_NAMESPACE": "ai-workloads",
        }
    )

    assert observer is not None
    assert observer.batch_api is batch_api
    assert observer.namespace == "ai-workloads"

    factory.config.load_incluster_config.assert_called_once_with()
    factory.client.BatchV1Api.assert_called_once_with()


def test_create_workload_observer_rejects_unknown_backend():
    import pytest

    from compute_fabric.execution.factory import create_workload_observer

    with pytest.raises(
        RuntimeError,
        match="Unsupported execution backend",
    ):
        create_workload_observer(
            {
                "COMPUTE_FABRIC_EXECUTION_BACKEND": "unknown",
            }
        )


def test_create_workload_observer_rejects_blank_namespace():
    import pytest

    from compute_fabric.execution.factory import create_workload_observer

    with pytest.raises(
        RuntimeError,
        match="COMPUTE_FABRIC_WORKLOAD_NAMESPACE must not be empty",
    ):
        create_workload_observer(
            {
                "COMPUTE_FABRIC_EXECUTION_BACKEND": "kubernetes",
                "COMPUTE_FABRIC_WORKLOAD_NAMESPACE": "   ",
            }
        )
