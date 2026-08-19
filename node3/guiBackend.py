"""
Node 3 GUI Backend
Reads P2P input JSONs + lastFrame.jpg from node3/inputs/
Writes telemetry.json + last_frame.jpg into node3/GUI/public/
Also serves Chaos Bench buttons via a small HTTP API on port 5001
that writes node3/outputs/p2pn2n3Output.json
"""

import json
import os
import shutil
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Inputs from P2P
N2N3_INPUT = os.path.join(BASE_DIR, "inputs", "p2pn2n3Input.json")
N1N3_INPUT = os.path.join(BASE_DIR, "inputs", "p2pn1n3Input.json")
LAST_FRAME_INPUT = os.path.join(BASE_DIR, "inputs", "lastFrame.jpg")

# GUI public folder
GUI_PUBLIC = os.path.join(BASE_DIR, "GUI", "public")
TELEMETRY_OUT = os.path.join(GUI_PUBLIC, "telemetry.json")
LAST_FRAME_OUT = os.path.join(GUI_PUBLIC, "last_frame.jpg")

# Chaos output (this file is sent to Node 2 via p2p websocket)
CHAOS_OUTPUT = os.path.join(BASE_DIR, "outputs", "p2pn2n3Output.json")

CHAOS_API_PORT = 5001

def read_json_safe(path):
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def build_telemetry():
    n2n3 = read_json_safe(N2N3_INPUT)
    n1n3 = read_json_safe(N1N3_INPUT)
    chaos = read_json_safe(CHAOS_OUTPUT)

    # Extract sysus - handle both old flat and new nested format
    sysus = n2n3.get("sysus", {})
    if "node1" in sysus and "node2" in sysus:
        node1_hw = sysus["node1"]
        node2_hw = sysus["node2"]
    else:
        node2_hw = sysus
        node1_hw = {}

    # Extract kinematics from node2->node3 data
    kt = n2n3.get("kt", {})
    # kt has wheelslip0=newest ... wheelslip9=oldest
    # Graph expects index 0=oldest, index 9=newest, so reverse
    slip_history = [kt.get(f"wheelslip{i}", 0) for i in range(9, -1, -1)]
    torque_history = [kt.get(f"torque{i}", 0) for i in range(9, -1, -1)]

    # Model info
    model = n2n3.get("model", "medium")
    model_map = {
        "light": "YOLOv8n-INT8",
        "medium": "YOLOv8n-FP16"
    }
    active_model = model_map.get(model, "YOLOv8n-FP16")

    # Sensor data from CSV (sent by node2's core engine)
    sensor = n2n3.get("sensor", {})
    solar_pct = sensor.get("solar", 84.7)

    # Classifying engine / fusion brain output from node2
    cls_data = n2n3.get("classifying", {})
    vision_cls   = cls_data.get("vision_classification", "Nominal")
    telem_cls    = cls_data.get("telemetry_classification", "Normal Torque")
    fusion_out   = cls_data.get("fusion_output", "NOMINAL — No Fusion Conflict")
    fusion_conf  = cls_data.get("fusion_confidence", 0.85)
    rover_cmd    = cls_data.get("rover_command", "NOMINAL")

    # Model reason from complexity engine
    model_reason = f"Model selected: {model}"
    segment = sensor.get("segment", "NORMAL")
    if segment == "DUST_STORM":
        model_reason = "DUST STORM — Emergency power conservation"
    elif segment == "SAND_TRAP":
        model_reason = "SAND TRAP — Erratic terrain detected"

    # Read recent logs for the flight recorder
    logs = []
    log_path = os.path.join(BASE_DIR, "outputs", "node3_console.log")
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-30:]:  # take last 30 lines
                    line = line.strip()
                    if not line: continue
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        t_str, msg = parts
                        level = "INFO"
                        m_upper = msg.upper()
                        if "WARN" in m_upper: level = "WARN"
                        elif "ERR" in m_upper or "TRACE" in m_upper: level = "ERROR"
                        elif "CRIT" in m_upper: level = "CRIT"
                        logs.append({"time": t_str, "level": level, "msg": msg})
        except Exception:
            pass

    telemetry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "active_model": active_model,
        "complexity_engine": {
            "scheduled_model": active_model,
            "reason": model_reason,
            "node1_hardware": {
                "cpu_percent": node1_hw.get("cpu", 0),
                "vram_percent": node1_hw.get("vram", 0),
                "ram_percent": node1_hw.get("ram", 0),
                "disk_percent": node1_hw.get("disk", 0)
            },
            "node2_hardware": {
                "cpu_percent": node2_hw.get("cpu", 0),
                "vram_percent": node2_hw.get("vram", 0),
                "ram_percent": node2_hw.get("ram", 0),
                "disk_percent": node2_hw.get("disk", 0)
            }
        },
        "hardware": {
            "cpu_percent": node2_hw.get("cpu", 0),
            "gpu_percent": node2_hw.get("vram", 0),
            "ram_percent": node2_hw.get("ram", 0),
            "solar_battery_percent": solar_pct
        },
        "kinematics": {
            "wheel_slip_percent": slip_history[-1] if slip_history else 0,
            "motor_torque_nm": torque_history[-1] if torque_history else 0,
            "wheel_slip_history": slip_history,
            "motor_torque_history": torque_history
        },
        "classifying_engine": {
            "vision_classification": vision_cls,
            "telemetry_classification": telem_cls,
            "fusion_output": fusion_out,
            "fusion_confidence": fusion_conf,
            "rover_command": rover_cmd
        },
        "documentation_engine": {
            "sync_status": "BUFFERING OFFLINE",
            "earth_signal_delay_sec": 1124,
            "logs": logs
        },
        "chaos_bench": {
            "dust_storm_active": chaos.get("duststorm", 0) == 1,
            "sand_trap_injected": chaos.get("sandtrap", 0) == 1,
            "earth_uplink_enabled": chaos.get("earthuplink", 0) == 1
        }
    }

    return telemetry

def copy_last_frame():
    try:
        if os.path.exists(LAST_FRAME_INPUT):
            shutil.copy2(LAST_FRAME_INPUT, LAST_FRAME_OUT)
    except Exception as e:
        print(f"Image copy error: {e}")


# ── Chaos Bench HTTP API ──────────────────────────────────
class ChaosHandler(BaseHTTPRequestHandler):
    """Handles POST /api/chaos from the GUI to toggle chaos bench flags."""

    def do_POST(self):
        if self.path == "/api/chaos":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))

                chaos_data = {
                    "from": "node3",
                    "to": "node2",
                    "duststorm": body.get("duststorm", 0),
                    "sandtrap": body.get("sandtrap", 0),
                    "earthuplink": body.get("earthuplink", 0)
                }

                os.makedirs(os.path.dirname(CHAOS_OUTPUT), exist_ok=True)
                with open(CHAOS_OUTPUT, "w") as f:
                    json.dump(chaos_data, f, indent=4)

                print(f"[Chaos API] Updated: storm={chaos_data['duststorm']} "
                      f"trap={chaos_data['sandtrap']} uplink={chaos_data['earthuplink']}")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight for the POST."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress default HTTP logging


def start_chaos_api():
    """Run the chaos API server in a background thread."""
    server = HTTPServer(("0.0.0.0", CHAOS_API_PORT), ChaosHandler)
    print(f"[Chaos API] Listening on port {CHAOS_API_PORT}")
    server.serve_forever()


# ── Main loop ─────────────────────────────────────────────
def update_loop():
    os.makedirs(GUI_PUBLIC, exist_ok=True)

    # Ensure chaos output file exists with defaults
    if not os.path.exists(CHAOS_OUTPUT):
        os.makedirs(os.path.dirname(CHAOS_OUTPUT), exist_ok=True)
        with open(CHAOS_OUTPUT, "w") as f:
            json.dump({"from": "node3", "to": "node2",
                       "duststorm": 0, "sandtrap": 0, "earthuplink": 0}, f, indent=4)

    # Start chaos API server in background
    api_thread = threading.Thread(target=start_chaos_api, daemon=True)
    api_thread.start()

    print("Starting Node 3 GUI backend...")

    while True:
        try:
            telemetry = build_telemetry()
            with open(TELEMETRY_OUT, "w") as f:
                json.dump(telemetry, f, indent=2)
            copy_last_frame()
            print("Updated telemetry.json and last_frame.jpg")
        except Exception as e:
            print(f"Backend error: {e}")
        time.sleep(0.2)

if __name__ == "__main__":
    update_loop()
