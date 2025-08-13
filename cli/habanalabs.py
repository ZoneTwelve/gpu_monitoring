import csv
import json
from abc import ABC, abstractmethod
from typing import List
from .dummy_habanalabs import DummyGaudiCli

class BaseMonitor(ABC):
    @abstractmethod
    def record(self):
        pass

class GaudiMonitor(BaseMonitor):
    def __init__(self, output="csv", filename="gaudi_metrics.csv", use_dummy=True):
        self.output = output
        self.filename = filename
        self.cli = DummyGaudiCli() if use_dummy else None  # replace with real CLI later
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
