from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class GPUReport:
    gpu_id: str
    gpu_type: str
    node_id: str
    total_vram_gb: float
    free_vram_gb: float
    utilization_percent: float
    temperature_c: float
    power_draw_watts: float
    observed_at: datetime
