"""Fake CNC machines pushing readings to the API.

Stand-in for an OPC-UA source. Later you can point a real OPC-UA client here instead.
"""
import os
import random
import time

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")
MACHINES = os.getenv("MACHINES", "cnc-01,cnc-02,cnc-03").split(",")
INTERVAL = float(os.getenv("INTERVAL_SECONDS", "2"))

TAGS = {
    "spindle_temp": (55.0, 85.0),
    "vibration": (0.1, 1.2),
    "spindle_rpm": (800.0, 12000.0),
}


def wait_for_api():
    for _ in range(30):
        try:
            if requests.get(f"{API_URL}/ready", timeout=2).ok:
                return
        except requests.RequestException:
            pass
        print("waiting for api...", flush=True)
        time.sleep(2)
    raise SystemExit("api never became ready")


def main():
    wait_for_api()
    print(f"sending readings for {MACHINES} every {INTERVAL}s", flush=True)
    while True:
        for machine in MACHINES:
            tag, (lo, hi) = random.choice(list(TAGS.items()))
            payload = {"machine_id": machine, "tag": tag, "value": round(random.uniform(lo, hi), 2)}
            try:
                r = requests.post(f"{API_URL}/readings", json=payload, timeout=3)
                r.raise_for_status()
            except requests.RequestException as exc:
                # Keep going. A dead API shouldn't kill the simulator.
                print(f"send failed: {exc}", flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
