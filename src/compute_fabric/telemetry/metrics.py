from prometheus_client import Counter, Histogram


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
