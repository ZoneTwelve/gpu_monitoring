import csv
import json
from abc import ABC, abstractmethod
from typing import List, Dict
from .dummy import DummyGaudiCli
import subprocess

class BaseMonitor(ABC):
    @abstractmethod
    def record(self):
        pass

class HLsmiGaudiCli:
    """Interface to Gaudi devices using hl-smi CLI."""

    def __init__(self):
        self.devices = self.list_devices()

    def list_devices(self) -> List[str]:
        """Return list of PCI addresses for Gaudi devices."""
        try:
            result = subprocess.run(
                ["hl-smi", "--list-aips"],
                capture_output=True, text=True, check=True
            )
            lines = result.stdout.strip().splitlines()
            devices = []
            for line in lines:
                # example line: "0 0000:35:00.0 HL-325L ..."
                parts = line.strip().split()
                if len(parts) >= 2:
                    devices.append(parts[1])
            return devices
        except subprocess.CalledProcessError:
            return []

    def query(self, fields: List[str] = None) -> List[Dict]:
        """
        Query all devices and return a list of dicts.
        :param fields: list of hl-smi fields to query. Default set if None.
        """
        if fields is None:
            fields = [
                "timestamp", "name", "bus_id", "driver_version",
                "temperature.aip", "utilization.aip", "utilization.memory",
                "memory.total", "memory.free", "memory.used",
                "index", "serial", "uuid", "power.draw"
            ]
        return [self.query_device(dev, fields) for dev in self.devices]

    def query_device(self, pci_addr: str, fields: List[str]) -> Dict:
        """
        Query metrics for a single device.
        :param pci_addr: PCI address of the device
        :param fields: list of hl-smi fields to query
        :return: dict of values (non-numeric -> -1)
        """
        field_str = ",".join(fields)
        try:
            result = subprocess.run(
                [
                    "hl-smi",
                    "--query-aip=" + field_str,
                    "--format=csv,noheader,nounits",
                    "-i", pci_addr
                ],
                capture_output=True, text=True, check=True
            )
            reader = csv.reader(result.stdout.strip().splitlines())
            values = next(reader, [])
            data = {}
            for f, v in zip(fields, values):
                # Convert numeric values, fallback to -1
                try:
                    if "%" in v:
                        v = v.replace("%", "")
                    data[f] = float(v)
                except:
                    data[f] = -1
            data["pci_addr"] = pci_addr
            return data
        except subprocess.CalledProcessError:
            return {f: -1 for f in fields}

    def query_all(self, fields: List[str]) -> List[Dict]:
        """Query all devices."""
        return [self.query_device(dev, fields) for dev in self.devices]

class GaudiMonitor(BaseMonitor):
    def __init__(self, output="csv", filename="gaudi_metrics.csv", use_dummy=True):
        self.output = output
        self.filename = filename
        self.cli = HLsmiGaudiCli() if not use_dummy else DummyGaudiCli()
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
