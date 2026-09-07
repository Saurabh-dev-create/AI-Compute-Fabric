from compute_fabric.gpu.nvidia_gpu_collector import NvidiaGPUCollector


def test_collector_converts_nvidia_csv_into_gpu_report() -> None:
    output = (
        "GPU-abc123, Tesla T4, 15360, 12288, 25, 58, 42.50\n"
    )

    collector = NvidiaGPUCollector(
        node_id="ip-10-20-40-10.ap-south-1.compute.internal"
    )

    reports = collector.parse_output(output)

    assert len(reports) == 1

    report = reports[0]

    assert report.gpu_id == "GPU-abc123"
    assert report.gpu_type == "T4"
    assert report.node_id == (
        "ip-10-20-40-10.ap-south-1.compute.internal"
    )
    assert report.total_vram_gb == 15
    assert report.free_vram_gb == 12
    assert report.utilization_percent == 25
    assert report.temperature_c == 58
    assert report.power_draw_watts == 42.5


def test_collector_parses_multiple_gpus() -> None:
    output = (
        "GPU-aaa111, Tesla T4, 15360, 12288, 10, 50, 35.00\n"
        "GPU-bbb222, NVIDIA A100-SXM4-80GB, 81920, 65536, 40, 61, 180.00\n"
    )

    collector = NvidiaGPUCollector(node_id="gpu-node-01")

    reports = collector.parse_output(output)

    assert len(reports) == 2

    assert reports[0].gpu_id == "GPU-aaa111"
    assert reports[0].gpu_type == "T4"

    assert reports[1].gpu_id == "GPU-bbb222"
    assert reports[1].gpu_type == "A100"
    assert reports[1].total_vram_gb == 80
    assert reports[1].free_vram_gb == 64


def test_collector_ignores_blank_lines() -> None:
    collector = NvidiaGPUCollector(node_id="gpu-node-01")

    reports = collector.parse_output("\n\n")

    assert reports == []
