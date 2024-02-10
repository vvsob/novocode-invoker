class Limits:
    def __init__(self, time_ms: int, memory_kb: int, real_time_ms: int):
        self.time_ms = time_ms
        self.memory_kb = memory_kb
        self.real_time_ms = real_time_ms


class Metrics:
    def __init__(self, time_ms: int, memory_kb: int, real_time_ms: int, status: str):
        self.time_ms = time_ms
        self.memory_kb = memory_kb
        self.real_time_ms = real_time_ms
        self.status = status

    def is_ok(self):
        return self.status.lower() == "ok"

