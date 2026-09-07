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
