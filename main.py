import time
from cli.habanalabs import GaudiMonitor

if __name__ == "__main__":
    # monitor = GaudiMonitor(output="csv", filename="gaudi.csv", use_dummy=True)
    monitor = GaudiMonitor(output="wandb", filename="gaudi.csv", use_dummy=True)

    while True:
        ret = monitor.record(echo=True)
        print(ret)
        time.sleep(1)
