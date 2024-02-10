from typing import Sequence, IO, Callable

from strategy.errors import NoVerdictError
from strategy.verdicts import TestVerdict, ICPCVerdict


class Test:
    def __init__(self, number: int, input: IO[str], answer: IO[str], verdict: TestVerdict | None = None):
        self.number = number
        self.input = input
        self.answer = answer
        self.verdict = verdict


class TestSet:
    def __init__(self, tests: Sequence[Test]):
        self.tests = tests
        self.on_next = list()

    def add_on_next(self, func: Callable[[int], None]):
        self.on_next.append(func)

    def __iter__(self):
        self.current_test = -1
        return self

    def __next__(self):
        self.current_test += 1
        if self.current_test >= len(self.tests):
            raise StopIteration
        for func in self.on_next:
            func(self.tests[self.current_test].number)
        return self.tests[self.current_test]

    def verdicts(self):
        return [test.verdict for test in self.tests if test.verdict is not None]


class ICPCTestSet(TestSet):
    def __next__(self):
        current_test = self.tests[self.current_test] if self.current_test >= 0 else None
        if current_test is not None and current_test.verdict is None:
            raise NoVerdictError()
        if current_test is not None and not current_test.verdict.is_ok():
            self.verdict = ICPCVerdict(current_test.verdict.status, self.verdicts(), current_test.number)
            raise StopIteration
        self.current_test += 1
        if self.current_test >= len(self.tests):
            self.verdict = ICPCVerdict("ok", self.verdicts())
            raise StopIteration
        for func in self.on_next:
            func(self.tests[self.current_test].number)
        return self.tests[self.current_test]
