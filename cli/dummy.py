import math
import random
from datetime import datetime

class DummyGaudiCli:
    def __init__(self):
        self.gpus = [
            {"bus": "35:00.0", "temp": 40, "util_aip": 0, "util_mem": 0, "mem_used": 672, "index": 0, "serial": "AO22049929", "uuid": "01P4-HL3090A0-18-U2W736-22-04-01", "power": 214},
            {"bus": "9a:00.0", "temp": 39, "util_aip": 0, "util_mem": 81, "mem_used": 106205, "index": 1, "serial": "AO22049870", "uuid": "01P4-HL3090A0-18-U2Y674-12-04-01", "power": 214},
            {"bus": "21:00.0", "temp": 41, "util_aip": 0, "util_mem": 0, "mem_used": 672, "index": 2, "serial": "AO37061668", "uuid": "01P4-HL3090A0-18-U4P392-07-11-06", "power": 214},
        ]
        self.memory_total = 131072  # MiB
        self.t = 0

    def smooth_random(self, base, amplitude, noise, t, freq=0.1):
        """Smooth sine variation with tiny jitter"""
        return round(base + amplitude * math.sin(2 * math.pi * freq * t) + random.uniform(-noise, noise))

    def query(self):
        timestamp = datetime.utcnow().strftime("%a %b %d %H:%M:%S UTC %Y")
        metrics = []
        for gpu in self.gpus:
            temp = self.smooth_random(gpu["temp"], 1, 0.5, self.t + gpu["index"])
            power = self.smooth_random(gpu["power"], 1, 0.5, self.t + gpu["index"])
            util_aip = self.smooth_random(gpu["util_aip"], 1, 0.5, self.t + gpu["index"])
            util_mem = self.smooth_random(gpu["util_mem"], 1, 0.5, self.t + gpu["index"])
            mem_free = self.memory_total - gpu["mem_used"]

            metrics.append({
                "timestamp": timestamp,
                "uuid": gpu["uuid"],
                "bus": gpu["bus"],
                "temp": temp,
                "util_aip": util_aip,
                "util_mem": util_mem,
                "mem_total": self.memory_total,
                "mem_free": mem_free,
                "mem_used": gpu["mem_used"],
                "power": power,
                "serial": gpu["serial"],
                "index": gpu["index"]
            })
        self.t += 1
        return metrics
