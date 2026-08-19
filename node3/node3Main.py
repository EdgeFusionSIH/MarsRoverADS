import subprocess
import os
import sys
import time
import threading
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ports used by the p2p websocket servers
WS_PORTS = [8766, 8767]

def kill_stale_port(port):
    """Kill any process still holding a port from a previous run."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        if result == 0:  # port is in use
            print(f"[cleanup] Port {port} is occupied, killing old process...")
            if sys.platform == "win32":
                # Find and kill the PID holding the port on Windows
                out = subprocess.check_output(
                    f"netstat -ano | findstr :{port}", shell=True, text=True
                )
                for line in out.strip().splitlines():
                    parts = line.split()
                    if f":{port}" in parts[1] and parts[3] == "LISTENING":
                        pid = parts[-1]
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True,
                                       capture_output=True)
                        print(f"[cleanup] Killed PID {pid} on port {port}")
                        break
            else:
                subprocess.run(f"lsof -ti :{port} | xargs kill -9", shell=True,
                               capture_output=True)
                print(f"[cleanup] Killed process on port {port}")
            time.sleep(0.5)
    except Exception:
        pass  # port is free, nothing to do

for port in WS_PORTS:
    kill_stale_port(port)

scripts = [
    "p2pn2n3.py",
    "p2pn1n3.py",
    "guiBackend.py"
]

LOG_FILE = os.path.join(BASE_DIR, "outputs", "node3_console.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
with open(LOG_FILE, "w") as f:
    f.write("")  # clear previous logs

def print_output(process, prefix):
    for line in iter(process.stdout.readline, b''):
        line = line.decode('utf-8', errors='replace').rstrip()
        if line:
            msg = f"[{prefix}] {line}"
            print(msg)
            sys.stdout.flush()
            try:
                with open(LOG_FILE, "a", encoding='utf-8') as f:
                    f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
            except Exception:
                pass

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
    npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
    p = subprocess.Popen(
        [npx_cmd, "vite", "--host"],
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
        p.kill()  # kill() is more reliable than terminate() on Windows
    for p in processes:
        p.wait()  # wait for them to actually exit
    print("All processes stopped.")
