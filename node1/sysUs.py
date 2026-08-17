import psutil
import json
import time
import os


OUTPUT_FILE = "node1\\dataset\\systemInfo.json"


def get_system_info():
    # Real CPU usage
    cpu = psutil.cpu_percent(interval=0.5)

    # Real RAM usage
    ram = psutil.virtual_memory().percent

    # Real disk usage
    disk = psutil.disk_usage('/').percent

    # Real GPU usage
    gpu = 0

    try:
        import pynvml

        pynvml.nvmlInit()

        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_info = pynvml.nvmlDeviceGetUtilizationRates(handle)

        gpu = gpu_info.gpu

        pynvml.nvmlShutdown()

    except Exception:
        # No NVIDIA GPU / NVML unavailable
        gpu = 0

    return {
        "nodeid": 1,
        "cpu": cpu,
        "gpu": gpu,
        "ram": ram,
        "disk": disk
    }


def write_system_info():
    # Make sure dataset folder exists
    os.makedirs("dataset", exist_ok=True)

    while True:
        system_info = get_system_info()

        # 'w' MODE COMPLETELY OVERWRITES THE FILE
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(system_info, file, indent=4)

        print(system_info)

        # Update every 1 second
        time.sleep(1)


if __name__ == "__main__":
    write_system_info()