import queue


class MessageQueue:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, msg: dict):
        self.queue.put(msg)

    def get(self):
        return self.queue.get()

    def is_empty(self):
        return self.queue.empty()
