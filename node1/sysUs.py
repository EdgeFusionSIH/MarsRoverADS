import psutil
import GPUtil


def get_system_usage():
    """
    Return current Node 1 system usage.

    Returns:
        dict: CPU, RAM, and GPU usage information.
    """

    # CPU usage
    cpu_usage = psutil.cpu_percent(interval=1)

    # RAM usage
    memory = psutil.virtual_memory()

    ram_usage = memory.percent
    ram_used_gb = round(memory.used / (1024 ** 3), 2)
    ram_total_gb = round(memory.total / (1024 ** 3), 2)

    # GPU usage
    gpus = GPUtil.getGPUs()

    gpu_info = []

    for gpu in gpus:
        gpu_info.append({
            "name": gpu.name,
            "usage_percent": round(gpu.load * 100, 2),
            "memory_usage_percent": round(gpu.memoryUtil * 100, 2),
            "memory_used_gb": round(gpu.memoryUsed / 1024, 2),
            "memory_total_gb": round(gpu.memoryTotal / 1024, 2)
        })

    return {
        "cpu_usage_percent": cpu_usage,
        "ram_usage_percent": ram_usage,
        "ram_used_gb": ram_used_gb,
        "ram_total_gb": ram_total_gb,
        "gpu": gpu_info
    }


# ------------------------------------------------------------
# TEST MODE
# ------------------------------------------------------------

if __name__ == "__main__":

    print("========================================")
    print("       NODE 1 SYSTEM USAGE")
    print("========================================")

    usage = get_system_usage()

    print("\nCPU:")
    print(f"Usage: {usage['cpu_usage_percent']}%")

    print("\nRAM:")
    print(
        f"Usage: {usage['ram_usage_percent']}% "
        f"({usage['ram_used_gb']} GB / "
        f"{usage['ram_total_gb']} GB)"
    )

    print("\nGPU:")

    if len(usage["gpu"]) == 0:

        print("No GPU detected.")

    else:

        for gpu in usage["gpu"]:

            print(f"Name: {gpu['name']}")
            print(f"Usage: {gpu['usage_percent']}%")
            print(
                f"VRAM: {gpu['memory_used_gb']} GB / "
                f"{gpu['memory_total_gb']} GB"
            )
            print(
                f"VRAM usage: "
                f"{gpu['memory_usage_percent']}%"
            )

    print("\nSystem usage check complete.")