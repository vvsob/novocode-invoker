import os.path
import tempfile
from typing import IO
from tempfile import TemporaryFile, NamedTemporaryFile

from strategy.executable import Executable
from strategy.metrics import Limits
from strategy.test import Test
from strategy.verdicts import TestVerdict


class CheckerJudgement:
    def __init__(self, status: str, message: str = ""):
        self.status = status
        self.message = message

    def is_ok(self):
        return self.status.lower() == "ok"


class Checker(Executable):
    def __init__(self, main_file, *args):
        super().__init__(main_file, *args)

    def check(self, input: IO[str], output: IO[str], answer: IO[str]) -> CheckerJudgement:
        with (
            NamedTemporaryFile(mode='w') as input_file,
            NamedTemporaryFile(mode='w') as output_file,
            NamedTemporaryFile(mode='w') as answer_file,
            NamedTemporaryFile(mode='r') as judgement_file,
        ):
            input_file.write(input.read())
            output_file.write(output.read())
            answer_file.write(answer.read())
            metrics = self(
                files=[input_file.name, output_file.name, answer_file.name, judgement_file.name],
                args=[os.path.basename(path) for path in [input_file.name, output_file.name, answer_file.name, judgement_file.name]],
            )
            judgement_file_contents = judgement_file.read()
            judgement_properties = dict()
            for line in judgement_file_contents.strip().split('\n'):
                judgement_properties[line.split(': ')[0]] = line.split(': ')[1]
        return CheckerJudgement(judgement_properties["status"].lower())

    def eval(self, submission: Executable, test: Test, limits: Limits) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            with open(tmp.name, mode='w') as output_file_write:
                runtime_metrics = submission(stdin=test.input, stdout=output_file_write, limits=limits)
            if not runtime_metrics.is_ok():
                test.verdict = TestVerdict(runtime_metrics.status, runtime_metrics)
                return
            with open(tmp.name, mode='r') as output_file_read:
                judgement = self.check(test.input, output_file_read, test.answer)
                test.verdict = TestVerdict(judgement.status, runtime_metrics)


class TestlibChecker(Checker):
    def check(self, input: IO[str], output: IO[str], answer: IO[str]) -> CheckerJudgement:
        with (
            NamedTemporaryFile(mode='w') as input_file,
            NamedTemporaryFile(mode='w') as output_file,
            NamedTemporaryFile(mode='w') as answer_file,
            NamedTemporaryFile(mode='r') as judgement_file,
        ):
            input_file.write(input.read())
            output_file.write(output.read())
            answer_file.write(answer.read())
            metrics = self(
                files=[input_file.name, output_file.name, answer_file.name, judgement_file.name],
                args=[os.path.basename(path) for path in
                      [input_file.name, output_file.name, answer_file.name, judgement_file.name]],
            )
            judgement_file_contents = judgement_file.read()
            status = "ok" if metrics.is_ok() else "wa"
        return CheckerJudgement(status, judgement_file_contents)
