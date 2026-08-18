import subprocess
import os
import sys
import time
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

scripts = [
    "p2pn2n3.py",
    "p2pn1n3.py",
    "guiBackend.py"
]

def print_output(process, prefix):
    for line in iter(process.stdout.readline, b''):
        line = line.decode('utf-8', errors='replace').rstrip()
        if line:
            print(f"[{prefix}] {line}")
            sys.stdout.flush()

processes = []
print("Starting Node 3 processes...")
for script in scripts:
    script_path = os.path.join(BASE_DIR, script)
    if os.path.exists(script_path):
        print(f"[{script}] Launching...")
        p = subprocess.Popen(
            [sys.executable, script_path], 
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        processes.append(p)
        t = threading.Thread(target=print_output, args=(p, script), daemon=True)
        t.start()
        time.sleep(1) # stagger startups slightly
    else:
        print(f"[{script}] Warning: not found in {BASE_DIR}")

# Launch Vite dev server for GUI
gui_dir = os.path.join(BASE_DIR, "GUI")
if os.path.exists(gui_dir):
    print("[GUI] Launching Vite dev server...")
    p = subprocess.Popen(
        ["npx", "vite", "--host"],
        cwd=gui_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    processes.append(p)
    t = threading.Thread(target=print_output, args=(p, "GUI"), daemon=True)
    t.start()
else:
    print("[GUI] Warning: GUI folder not found")

try:
    print("All processes started! Press Ctrl+C to terminate all.")
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nShutting down Node 3 processes...")
    for p in processes:
        p.terminate()
