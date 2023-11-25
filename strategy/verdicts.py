class Verdict:
    def __init__(self, status):
        self.status = status


class TestVerdict(Verdict):
    def __init__(self, status, metrics):
        super().__init__(status)
        self.metrics = metrics


class ICPCVerdict(Verdict):
    def __init__(self, status, per_test_verdicts, first_test_failed=None):
        super().__init__(status)
        self.first_test_failed = first_test_failed
        self.per_test_verdicts = per_test_verdicts


class IOIVerdict(Verdict):
    def __init__(self, status, per_test_verdicts, points):
        super().__init__(status)
        self.points = points
        self.per_test_verdicts = per_test_verdicts
