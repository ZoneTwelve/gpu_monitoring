import csv
import json
from abc import ABC, abstractmethod
from typing import List
from .dummy import DummyGaudiCli

import habanalabs
from datetime import datetime

class BaseMonitor(ABC):
    @abstractmethod
    def record(self):
        pass

class GaudiCli:
    def __init__(self):
        self.devices = habanalabs.device_list()

    def query(self):
        metrics = []
        for device in self.devices:
            device_info = device.get_info()
            metrics.append({
                "timestamp": datetime.utcnow().strftime("%a %b %d %H:%M:%S UTC %Y"),
                "uuid": device_info.get("uuid", "unknown"),
                "bus": device_info.get("bus", "unknown"),
                "temp": device_info.get("temperature", -1),
                "util_aip": device_info.get("utilization_aip", -1),
                "util_mem": device_info.get("utilization_mem", -1),
                "mem_total": device_info.get("memory_total", -1),
                "mem_free": device_info.get("memory_free", -1),
                "mem_used": device_info.get("memory_used", -1),
                "power": device_info.get("power", -1),
                "serial": device_info.get("serial", "unknown"),
                "index": device_info.get("index", -1)
            })
        return metrics

class GaudiMonitor(BaseMonitor):
    def __init__(self, output="csv", filename="gaudi_metrics.csv", use_dummy=True):
        self.output = output
        self.filename = filename
        self.cli = GaudiCli() if not use_dummy else DummyGaudiCli()
        self._init_output()

    def _init_output(self):
        if self.output == "csv":
            with open(self.filename, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self._fields())
                writer.writeheader()
        elif self.output == "jsonl":
            open(self.filename, "w").close()  # clear file
        elif self.output == "wandb":
            import wandb
            wandb.init(project="gaudi_monitor")

    def _fields(self):
        return ["timestamp", "uuid", "bus", "temp", "util_aip", "util_mem",
                "mem_total", "mem_free", "mem_used", "power", "serial", "index"]

    def _sanitize(self, value):
        try:
            if isinstance(value, str):
                value = value.replace("%", "").replace("C", "").strip()
            return float(value)
        except (ValueError, TypeError):
            return -1  # fallback for N/A or invalid

    def record(self, echo=False):
        metrics = self.cli.query()
        for m in metrics:
            # sanitize numeric fields
            for key in ["temp", "util_aip", "util_mem", "mem_total", "mem_free", "mem_used", "power"]:
                m[key] = self._sanitize(m[key])

        if self.output == "csv":
            with open(self.filename, "a", newline="") as f:
                import csv
                writer = csv.DictWriter(f, fieldnames=self._fields())
                writer.writerows(metrics)
        elif self.output == "jsonl":
            with open(self.filename, "a") as f:
                import json
                for m in metrics:
                    f.write(json.dumps(m) + "\n")
        elif self.output == "wandb":
            import wandb
            for m in metrics:
                uuid = m.get("uuid", "unknown")
                wandb.log({
                    f"{uuid}/temp": m["temp"],
                    f"{uuid}/util_aip": m["util_aip"],
                    f"{uuid}/util_mem": m["util_mem"],
                    f"{uuid}/power": m["power"],
                    f"{uuid}/mem_used": m["mem_used"]
                })

        if echo:
            return metrics
