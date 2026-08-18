import subprocess
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

scripts = [
    "sysUs.py",
    "vision.py",
    "p2pn1n2.py",
    "p2pn1n3.py"
]

processes = []
print("Starting Node 1 processes...")
for script in scripts:
    script_path = os.path.join(BASE_DIR, script)
    if os.path.exists(script_path):
        print(f"Launching {script}...")
        p = subprocess.Popen([sys.executable, script_path], cwd=BASE_DIR)
        processes.append(p)
        time.sleep(1) # stagger startups slightly
    else:
        print(f"Warning: {script} not found in {BASE_DIR}")

try:
    print("All processes started! Press Ctrl+C to terminate all.")
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nShutting down Node 1 processes...")
    for p in processes:
        p.terminate()
