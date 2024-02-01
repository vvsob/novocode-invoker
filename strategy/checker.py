from strategy import *


class CheckerJudgement:
    def __init__(self, status: str, message: str = ""):
        self.status = status
        self.message = message


class Checker(Executable):
    def __init__(self, main_file, *args):
        super().__init__(main_file, *args)

    def check(self, input: TestData, output: str, answer: TestData) -> CheckerJudgement:
        with File() as input_file, File() as output_file, File() as answer_file, File() as judgement_file:
            input_file.write(input.get())
            output_file.write(output)
            answer_file.write(answer.get())
            metrics = self(
                files=[input_file, output_file, answer_file, judgement_file],
                args=[input_file.path, output_file.path, answer_file.path, judgement_file.path]
            )
            with open(judgement_file.path, mode='r') as judgement_file_stream:
                judgement_file_contents = judgement_file_stream.read()
            judgement_properties = dict()
            for line in judgement_file_contents.strip().split('\n'):
                judgement_properties[line.split(': ')[0]] = line.split(': ')[1]
        return CheckerJudgement(judgement_properties["status"])


class TestlibChecker(Executable):
    def __init__(self, main_file, *args):
        super().__init__(main_file, *args)

    def check(self, input: TestData, output: str, answer: TestData) -> CheckerJudgement:
        with File() as input_file, File() as output_file, File() as answer_file, File() as judgement_file:
            input_file.write(input.get())
            output_file.write(output)
            answer_file.write(answer.get())
            metrics = self(
                files=[input_file, output_file, answer_file, judgement_file],
                args=[input_file.path, output_file.path, answer_file.path, judgement_file.path]
            )
            with open(judgement_file.path, mode='r') as judgement_file_stream:
                judgement_file_contents = judgement_file_stream.read()
            status = "OK" if metrics.status == "OK" else "WA"
        return CheckerJudgement(status, judgement_file_contents)
