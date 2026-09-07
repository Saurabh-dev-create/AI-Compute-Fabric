from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class GPUAgentConfig:
    node_id: str
    control_plane_url: str
    interval_seconds: float = 15.0

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, str],
    ) -> "GPUAgentConfig":
        try:
            node_id = values["GPU_AGENT_NODE_ID"].strip()
        except KeyError as exc:
            raise ValueError(
                "GPU_AGENT_NODE_ID is required"
            ) from exc

        try:
            control_plane_url = (
                values["GPU_AGENT_CONTROL_PLANE_URL"].strip()
            )
        except KeyError as exc:
            raise ValueError(
                "GPU_AGENT_CONTROL_PLANE_URL is required"
            ) from exc

        if not node_id:
            raise ValueError("GPU_AGENT_NODE_ID must not be empty")

        if not control_plane_url:
            raise ValueError(
                "GPU_AGENT_CONTROL_PLANE_URL must not be empty"
            )

        interval_value = values.get(
            "GPU_AGENT_INTERVAL_SECONDS",
            "15",
        )

        try:
            interval_seconds = float(interval_value)
        except ValueError as exc:
            raise ValueError(
                "GPU_AGENT_INTERVAL_SECONDS must be numeric"
            ) from exc

        if interval_seconds <= 0:
            raise ValueError(
                "GPU_AGENT_INTERVAL_SECONDS must be greater than zero"
            )

        return cls(
            node_id=node_id,
            control_plane_url=control_plane_url.rstrip("/"),
            interval_seconds=interval_seconds,
        )
