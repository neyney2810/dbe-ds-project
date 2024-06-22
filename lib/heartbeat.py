import time
import threading


class Host:
    def __init__(self, id):
        self.id = id
        self.alive = True
        self.last_heartbeat = time.time()

    def send_heartbeat(self):
        while self.alive:
            time.sleep(1)
            self.last_heartbeat = time.time()
            print(f"Host {self.id} sending heartbeat")

    def check_heartbeat(self, timeout=3):
        while True:
            time.sleep(timeout)
            if time.time() - self.last_heartbeat > timeout:
                self.alive = False
                print(f"Host {self.id} failed")
