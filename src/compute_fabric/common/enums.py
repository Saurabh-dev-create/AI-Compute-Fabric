from enum import Enum


class GPUStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ALLOCATED = "ALLOCATED"
    UNHEALTHY = "UNHEALTHY"
    DRAINING = "DRAINING"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
