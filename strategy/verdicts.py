class Verdict:
    def __init__(self, status):
        self.status = status

    def is_ok(self):
        return self.status.lower() == "ok"


class TestVerdict(Verdict):
    def __init__(self, status, metrics):
        super().__init__(status)
        self.metrics = metrics


class ICPCVerdict(Verdict):
    def __init__(self, status, per_test_verdicts, first_test_failed=None):
        super().__init__(status)
        self.first_test_failed = first_test_failed
        self.per_test_verdicts = per_test_verdicts


class TestingVerdict(Verdict):
    def __init__(self, current_test):
        super().__init__("testing")
        self.current_test = current_test


class IOIVerdict(Verdict):
    def __init__(self, status, per_test_verdicts, points):
        super().__init__(status)
        self.points = points
        self.per_test_verdicts = per_test_verdicts
