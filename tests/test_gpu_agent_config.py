import pytest

from compute_fabric.gpu.gpu_agent_config import GPUAgentConfig


def test_config_reads_required_environment_values() -> None:
    config = GPUAgentConfig.from_mapping(
        {
            "GPU_AGENT_NODE_ID": "ip-10-20-40-10",
            "GPU_AGENT_CONTROL_PLANE_URL": (
                "http://compute-fabric-api:8000"
            ),
            "GPU_AGENT_INTERVAL_SECONDS": "15",
        }
    )

    assert config.node_id == "ip-10-20-40-10"
    assert config.control_plane_url == (
        "http://compute-fabric-api:8000"
    )
    assert config.interval_seconds == 15.0


def test_config_uses_default_interval() -> None:
    config = GPUAgentConfig.from_mapping(
        {
            "GPU_AGENT_NODE_ID": "gpu-node-01",
            "GPU_AGENT_CONTROL_PLANE_URL": (
                "http://compute-fabric-api:8000"
            ),
        }
    )

    assert config.interval_seconds == 15.0


@pytest.mark.parametrize(
    "missing_key",
    [
        "GPU_AGENT_NODE_ID",
        "GPU_AGENT_CONTROL_PLANE_URL",
    ],
)
def test_config_requires_identity_and_control_plane_url(
    missing_key: str,
) -> None:
    values = {
        "GPU_AGENT_NODE_ID": "gpu-node-01",
        "GPU_AGENT_CONTROL_PLANE_URL": (
            "http://compute-fabric-api:8000"
        ),
    }
    del values[missing_key]

    with pytest.raises(ValueError):
        GPUAgentConfig.from_mapping(values)


@pytest.mark.parametrize(
    "interval",
    ["0", "-1", "not-a-number"],
)
def test_config_rejects_invalid_interval(interval: str) -> None:
    with pytest.raises(ValueError):
        GPUAgentConfig.from_mapping(
            {
                "GPU_AGENT_NODE_ID": "gpu-node-01",
                "GPU_AGENT_CONTROL_PLANE_URL": (
                    "http://compute-fabric-api:8000"
                ),
                "GPU_AGENT_INTERVAL_SECONDS": interval,
            }
        )
