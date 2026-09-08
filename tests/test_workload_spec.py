from compute_fabric.execution.workload_spec import WorkloadSpec


def test_workload_spec_contains_backend_neutral_execution_details() -> None:
    spec = WorkloadSpec(
        image="nvidia/cuda:12.8.1-base-ubuntu24.04",
        command=("sh", "-c"),
        args=("nvidia-smi",),
    )

    assert spec.image == "nvidia/cuda:12.8.1-base-ubuntu24.04"
    assert spec.command == ("sh", "-c")
    assert spec.args == ("nvidia-smi",)


def test_workload_spec_command_and_args_are_optional() -> None:
    spec = WorkloadSpec(
        image="example/model-server:latest",
    )

    assert spec.command == ()
    assert spec.args == ()

def test_workload_spec_supports_service_execution_mode() -> None:
    spec = WorkloadSpec(
        image="example/vllm:latest",
        execution_mode="service",
    )

    assert spec.execution_mode == "service"


def test_workload_spec_defaults_to_batch_execution_mode() -> None:
    spec = WorkloadSpec(
        image="example/training:latest",
    )

    assert spec.execution_mode == "batch"

def test_workload_spec_supports_service_port() -> None:
    spec = WorkloadSpec(
        image="example/vllm:latest",
        execution_mode="service",
        service_port=8000,
    )

    assert spec.service_port == 8000
