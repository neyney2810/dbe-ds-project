class VectorClock:
    def __init__(self, id: str):
        self.vcDictionary = {}
        self.vcDictionary[id] = 0

    def increment(self, id: str):
        self.vcDictionary[id] += 1

    def merge(self, vc: 'VectorClock'):
        for key in vc.vcDictionary:
            if key not in self.vcDictionary:
                self.vcDictionary[key] = vc.vcDictionary[key]
            else:
                self.vcDictionary[key] = max(
                    self.vcDictionary[key], vc.vcDictionary[key])

    def local_event(self, id: str, clock):
        self.increment(id)
        print("Process {} performed a local event. Lamport timestamp is {}".format(
            id, clock))
        return clock

    def send_event(self, pipe, clock, pid):
        self.increment(id)
        pipe.send((pid, clock))
        print("Process {} sent a message. Lamport timestamp is {}".format(
            id, clock))
        return clock

    def receive_event(self, pipe, clock, pid):
        message, timestamp = pipe.recv()
        self.merge(timestamp)
        self.increment(id)
        print("Process {} received a message from process {}. Lamport timestamp is {}".format(
            id, message, clock))
        return clock

    def __str__(self):
        return str(self.vcDictionary)
