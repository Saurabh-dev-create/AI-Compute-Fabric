from prometheus_client import Counter, Gauge, Histogram


JOB_SUBMISSIONS = Counter(
    "compute_fabric_job_submissions_total",
    "Total number of jobs submitted to the AI Compute Fabric",
)

JOB_ADMISSION_REJECTIONS = Counter(
    "compute_fabric_job_admission_rejections_total",
    "Total number of jobs rejected by admission control",
)

SCHEDULING_ATTEMPTS = Counter(
    "compute_fabric_scheduling_attempts_total",
    "Total number of scheduling attempts",
)

SCHEDULING_RESULTS = Counter(
    "compute_fabric_scheduling_results_total",
    "Scheduling outcomes",
    ["result"],
)

JOB_LIFECYCLE_TRANSITIONS = Counter(
    "compute_fabric_job_lifecycle_transitions_total",
    "Job lifecycle transitions",
    ["status"],
)

SCHEDULING_LATENCY_SECONDS = Histogram(
    "compute_fabric_scheduling_latency_seconds",
    "Time spent attempting to schedule a job",
)


GPU_TOTAL_VRAM_GB = Gauge(
    "compute_fabric_gpu_total_vram_gb",
    "Total VRAM capacity of a GPU in gigabytes",
    ["gpu_id", "gpu_type", "node_id"],
)

GPU_FREE_VRAM_GB = Gauge(
    "compute_fabric_gpu_free_vram_gb",
    "Currently available GPU VRAM in gigabytes",
    ["gpu_id", "gpu_type", "node_id"],
)

GPU_UTILIZATION_PERCENT = Gauge(
    "compute_fabric_gpu_utilization_percent",
    "Current GPU utilization percentage",
    ["gpu_id", "gpu_type", "node_id"],
)

GPU_TEMPERATURE_CELSIUS = Gauge(
    "compute_fabric_gpu_temperature_celsius",
    "Current GPU temperature in Celsius",
    ["gpu_id", "gpu_type", "node_id"],
)

GPU_STATUS = Gauge(
    "compute_fabric_gpu_status",
    "GPU status represented as a labeled state",
    ["gpu_id", "gpu_type", "node_id", "status"],
)
