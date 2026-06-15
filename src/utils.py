import random
from typing import Any


def generate_random_result(base_fps: float, impact_range: tuple[float, float] = (-30, -0.5)) -> dict:
    """Generate a random benchmark result dict with FPS derived from base_fps."""
    drop = random.uniform(*impact_range)
    fps = max(10, base_fps * (1 + drop))
    frames = random.randint(1800, 2400)
    gpu_avg = fps * random.uniform(0.95, 0.99)
    gpu_p95 = gpu_avg * random.uniform(0.85, 0.95)
    cpu_times = [random.uniform(3, 15) for _ in range(800)]
    gpu_times = [random.uniform(4, 18) for _ in range(800)]
    return {
        "averageFps": round(fps, 1),
        "framesRendered": frames,
        "gpuFpsAvg": round(gpu_avg, 1),
        "gpuFpsP95": round(gpu_p95, 1),
        "cpuGameFrameTimes": cpu_times,
        "gpuFrameTimes": gpu_times,
    }


def get_fps(data: Any) -> float:
    """Safely extract FPS value from a result dict or numeric value."""
    if isinstance(data, dict):
        return data.get("averageFps", 0)
    return float(data) if data else 0
