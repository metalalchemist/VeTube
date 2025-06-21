import threading
import time

class Timer(threading.Thread):
    def __init__(self, interval, target):
        self._timer_runs = threading.Event()
        self._timer_runs.set()
        self.timer = target
        self.interval = interval
        super().__init__()

    def run(self):
        while self._timer_runs.is_set():
            self.timer()
            time.sleep(self.interval)

    def stop(self):
        self._timer_runs.clear()
        