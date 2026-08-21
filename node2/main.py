"""
Node 2 — Core Engine (main.py)
Reads mars_rover_sensor_data.csv and advances through the correct
section based on Chaos Bench signals received from Node 3:
  - Normal:    rows 1–300   (timestamp 0.1–30.0)
  - Dust Storm: rows 301–401 (timestamp 30.1–40.0)
  - Sand Trap:  rows 402–501 (timestamp 40.1–50.0)

Also runs the Complexity Engine (model selection) and
Classifying Engine (fusion brain) logic.

Writes everything into p2pn2n3Output.json for broadcast to Node 3.
"""

import csv
import json
import os
import time
from collections import deque

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── File paths ──────────────────────────────────────────────
CSV_FILE       = os.path.join(BASE_DIR, "dataset", "mars_rover_sensor_data.csv")
NODE1_INPUT    = os.path.join(BASE_DIR, "inputs", "p2pn1n2Input.json")
NODE2_SYSUS    = os.path.join(BASE_DIR, "dataset", "systemInfo.json")
CHAOS_INPUT    = os.path.join(BASE_DIR, "inputs", "p2pn2n3Input.json")
NODE3_OUTPUT   = os.path.join(BASE_DIR, "outputs", "p2pn2n3Output.json")
NODE1_OUTPUT   = os.path.join(BASE_DIR, "outputs", "p2pn1n2Output.json")

# ── Load CSV into three segment lists ──────────────────────
def load_csv_segments(path):
    """
    Returns three lists of row-dicts:
      normal    -> timestamp 0.1–50.0 
      sandstorm -> timestamp 50.1–100.0
      sandtrap  -> timestamp 100.1–150.0
    """
    normal, sandstorm, sandtrap = [], [], []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = float(row["TIMESTAMP"])
            entry = {
                "timestamp":  ts,
                "image_num":  int(float(row["Image numbers"])),
                "wheel_slip": float(row["Wheel slip (%)"]),
                "torque":     float(row["Torque (%)"]),
                "solar":      float(row["Solar (%)"])
            }
            if ts <= 50.0:
                normal.append(entry)
            elif ts <= 100.0:
                sandstorm.append(entry)
            else:
                sandtrap.append(entry)
    return normal, sandstorm, sandtrap


# ── Helper readers ─────────────────────────────────────────
def read_json_safe(path):
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def read_node1_sysus():
    """Node 1 system info forwarded via p2pn1n2Input.json"""
    data = read_json_safe(NODE1_INPUT)
    return data.get("sysus", {})


def read_node2_sysus():
    """Node 2 local system info from dataset/systemInfo.json"""
    return read_json_safe(NODE2_SYSUS)


def read_chaos():
    """Chaos bench flags from Node 3 via p2pn2n3Input.json"""
    return read_json_safe(CHAOS_INPUT)


# ── Complexity Engine ──────────────────────────────────────
def select_model(node1_hw, node2_hw, dust_storm, solar_pct):
    """
    Pick YOLO model based on hardware load, solar power & chaos state.
    Dust storm or low solar → always light (power conservation).
    Otherwise use 'medium' if both nodes have headroom and solar is healthy.
    """
    if dust_storm:
        return "light", "DUST STORM — Emergency power conservation"

    if solar_pct < 70:
        return "light", f"Low solar ({solar_pct:.0f}%) — light model for power savings"

    cpu1 = node1_hw.get("cpu", 0)
    ram1 = node1_hw.get("ram", 0)
    cpu2 = node2_hw.get("cpu", 0)
    ram2 = node2_hw.get("ram", 0)

    both_low = cpu1 < 85 and ram1 < 90 and cpu2 < 85 and ram2 < 90
    if both_low:
        return "medium", "Nodes healthy — normal model selected"
    return "light", "High load detected — light model selected"


# ── Classifying Engine / Fusion Brain ──────────────────────
def classify_telemetry(row, dust_storm, sand_trap):
    """
    Classify the current telemetry row.
    Returns (vision_class, telem_class, fusion_output, confidence, command)
    """
    slip   = row["wheel_slip"]
    torque = row["torque"]
    solar  = row["solar"]

    # ── Sand Trap (highest priority) ──
    if sand_trap:
        return (
            "Loose Sand",
            "Erratic Torque",
            "CRITICAL — Traction Loss Imminent",
            0.97,
            "HALT"
        )

    # ── Dust Storm ──
    if dust_storm:
        if solar < 55:
            return (
                "Reduced Visibility",
                "Solar Degraded",
                "CRITICAL — Solar below safe threshold",
                0.94,
                "SAFE_MODE"
            )
        return (
            "Reduced Visibility",
            "High Torque",
            "WARNING — Dust storm active, solar declining",
            0.88,
            "SLOW"
        )

    # ── Normal operations — classify by thresholds ──
    if slip > 15:
        vision_class = "Loose Surface"
    elif slip > 8:
        vision_class = "Moderate Terrain"
    else:
        vision_class = "Nominal"

    if torque > 15:
        telem_class = "High Torque"
    elif torque > 12:
        telem_class = "Elevated Torque"
    else:
        telem_class = "Normal Torque"

    # Fusion logic
    if vision_class == "Nominal" and telem_class == "Normal Torque":
        return (vision_class, telem_class,
                "NOMINAL — No Fusion Conflict", 0.85, "NOMINAL")
    elif slip > 15 and torque > 15:
        return (vision_class, telem_class,
                "WARNING — Slip & Torque Elevated", 0.91, "SLOW")
    else:
        return (vision_class, telem_class,
                "CAUTION — Monitoring", 0.80, "NOMINAL")


# ══════════════════════════════════════════════════════════
#  MAIN LOOP
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Loading mars_rover_sensor_data.csv ...")
    normal_rows, storm_rows, trap_rows = load_csv_segments(CSV_FILE)
    print(f"  Normal: {len(normal_rows)} rows  |  "
          f"Storm: {len(storm_rows)} rows  |  "
          f"Trap: {len(trap_rows)} rows")

    # Playback cursors — one per segment so each loops independently
    idx_normal = 0
    idx_storm  = 0
    idx_trap   = 0

    # Rolling history buffers (last 10 readings)
    slip_history   = deque(maxlen=10)
    torque_history = deque(maxlen=10)

    print("Starting Node 2 Core Engine ...\n")

    while True:
        # ── Read chaos bench state from Node 3 ──
        chaos = read_chaos()
        dust_storm = chaos.get("duststorm", 0) == 1
        sand_trap  = chaos.get("sandtrap", 0) == 1

        # ── Pick the right CSV segment & advance cursor ──
        if sand_trap:
            row = trap_rows[idx_trap % len(trap_rows)]
            idx_trap += 1
            active_segment = "SAND_TRAP"
        elif dust_storm:
            row = storm_rows[idx_storm % len(storm_rows)]
            idx_storm += 1
            active_segment = "DUST_STORM"
        else:
            row = normal_rows[idx_normal % len(normal_rows)]
            idx_normal += 1
            active_segment = "NORMAL"

        # ── Update rolling history ──
        slip_history.append(row["wheel_slip"])
        torque_history.append(row["torque"])

        # ── Read hardware info ──
        node1_hw = read_node1_sysus()
        node2_hw = read_node2_sysus()

        # ── Complexity Engine — model selection ──
        model, model_reason = select_model(node1_hw, node2_hw, dust_storm, row["solar"])

        # ── Classifying Engine / Fusion Brain ──
        (vision_cls, telem_cls,
         fusion_out, fusion_conf, rover_cmd) = classify_telemetry(
            row, dust_storm, sand_trap
        )

        # ── Build the output JSON ──
        kt = {}
        hist_slip   = list(slip_history)
        hist_torque = list(torque_history)
        for i in range(10):
            if i < len(hist_slip):
                kt[f"wheelslip{i}"] = round(hist_slip[-(i+1)], 2)   # 0 = newest
                kt[f"torque{i}"]    = round(hist_torque[-(i+1)], 2)
            else:
                kt[f"wheelslip{i}"] = 0
                kt[f"torque{i}"]    = 0

        output = {
            "from": "node2",
            "to": "node3",
            "sysus": {
                "node1": node1_hw,
                "node2": node2_hw
            },
            "model": model,
            "kt": kt,
            "sensor": {
                "timestamp":  row["timestamp"],
                "image_num":  row["image_num"],
                "wheel_slip": round(row["wheel_slip"], 2),
                "torque":     round(row["torque"], 2),
                "solar":      round(row["solar"], 2),
                "segment":    active_segment
            },
            "classifying": {
                "vision_classification":    vision_cls,
                "telemetry_classification": telem_cls,
                "fusion_output":            fusion_out,
                "fusion_confidence":        fusion_conf,
                "rover_command":            rover_cmd
            }
        }

        os.makedirs(os.path.dirname(NODE3_OUTPUT), exist_ok=True)
        with open(NODE3_OUTPUT, "w") as f:
            json.dump(output, f, indent=4)

        # Also update the model+image command for Node 1
        img_num = str(row["image_num"])
        node1_cmd = {
            "from": "node2",
            "to": "node1",
            "model": model,
            "img": img_num
        }
        os.makedirs(os.path.dirname(NODE1_OUTPUT), exist_ok=True)
        with open(NODE1_OUTPUT, "w") as f:
            json.dump(node1_cmd, f, indent=4)

        print(f"[{active_segment}] ts={row['timestamp']:.1f}  "
              f"slip={row['wheel_slip']:.1f}%  torque={row['torque']:.1f}%  "
              f"solar={row['solar']:.1f}%  model={model}  cmd={rover_cmd}")

        time.sleep(0.25)  # match CSV 0.25s cadence
