import psutil
import json
import time
import os
from pathlib import Path

OUTPUT_FILE = Path(__file__).resolve().parent / "dataset" / "systemInfo.json"

def get_system_info():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    vram = 0

    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        vram = round((mem_info.used / mem_info.total) * 100, 1)
        pynvml.nvmlShutdown()
    except Exception:
        vram = 0

    return {
        "nodeid": 1,
        "cpu": cpu,
        "vram": vram,
        "ram": ram,
        "disk": disk
    }

def write_system_info():
    os.makedirs(OUTPUT_FILE.parent, exist_ok=True)
    while True:
        system_info = get_system_info()
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(system_info, file, indent=4)
        print(system_info)
        time.sleep(1)

if __name__ == "__main__":
    write_system_info()