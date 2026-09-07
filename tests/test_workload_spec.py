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
