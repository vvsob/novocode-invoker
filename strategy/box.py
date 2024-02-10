import logging
import os
import shutil
import subprocess
from typing import Dict, Iterable, IO

from strategy.metrics import Metrics, Limits


class Box:
    def __init__(self, files: Iterable[str] = iter([])):
        self.files = files
        self.box_path = None

    def __enter__(self):
        subprocess.run("isolate --cleanup", shell=True)
        isolate_init_result = subprocess.run("isolate --init", capture_output=True, text=True, shell=True)
        self.box_path = os.path.join(isolate_init_result.stdout.strip(), 'box')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.run("isolate --cleanup", shell=True)

    def init_stdin(self, stdin: IO[str] | None) -> None:
        data_in_path = os.path.join(self.box_path, "__data.in")
        if stdin is None:
            open(data_in_path, mode='w').close()
        else:
            with open(data_in_path, mode='w') as data_in:
                data_in.write(stdin.read())

    def write_stdout(self, stdout: IO[str] | None) -> None:
        data_out_path = os.path.join(self.box_path, "__data.out")
        if stdout is None:
            return
        with open(data_out_path, mode='r') as data_out:
            stdout.write(data_out.read())

    def init_files(self) -> None:
        for file in self.files:
            os.link(file, os.path.join(self.box_path, os.path.basename(file)))

    @staticmethod
    def parse_meta_properties(meta_properties: Dict) -> Metrics:
        time_ms = int(float(meta_properties['time']) * 1000)
        real_time_ms = int(float(meta_properties['time-wall']) * 1000)
        memory_kb = int(meta_properties['max-rss'])
        status = "ok"
        if 'status' in meta_properties:
            status = {"RE": "re", "SG": "ml", "TO": "tl", "XX": "cf"}[meta_properties["status"]]
        return Metrics(time_ms, memory_kb, real_time_ms, status)

    def execute_isolate(self, command: str, limits: Limits) -> Metrics:
        meta_path = os.path.join(self.box_path, "__test.meta")

        subprocess.run(
            f"isolate --run --stdin=__data.in "
            f"--stdout=__data.out "
            f"--time={limits.time_ms / 1000} "
            f"--mem={limits.memory_kb} "
            f"--wall-time={limits.real_time_ms / 1000} "
            f"--extra-time=1 "
            f"--meta={meta_path} " +
            f"-E PATH=\"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\" " +
            f"-p " +
            f"-- " +
            f"{command}",
            shell=True,
        )

        with open(meta_path, mode='r') as meta_file_stream:
            meta_properties = dict()
            for line in meta_file_stream.readlines():
                meta_properties[line.split(':')[0]] = line.split(':')[1].strip()

        return self.parse_meta_properties(meta_properties)

    def run(self, command: str, stdin: IO[str] | None, stdout: IO[str] | None, limits: Limits) -> Metrics:
        if self.box_path is None:
            raise EnvironmentError()
        self.init_stdin(stdin)
        self.init_files()
        metrics = self.execute_isolate(command, limits)
        self.write_stdout(stdout)
        return metrics


class TrustedBox(Box):
    def __enter__(self):
        self.box_path = os.path.join(os.path.curdir, "__strategy_temp")
        os.mkdir(self.box_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.box_path)

    def execute(self, command: str) -> int:
        process = subprocess.run(
            f"{command}",
            shell=True,
            cwd=self.box_path,
        )
        return process.returncode

    def run(self, command: str, stdin: IO[str] | None, stdout: IO[str] | None, limits: Limits | None = None) -> int:
        if self.box_path is None:
            raise EnvironmentError()
        if limits is not None:
            logging.warning("Limits are currently not supported for TrustedBox, so they are ignored.")
        self.init_stdin(stdin)
        self.init_files()
        self.write_stdout(stdout)
        return self.execute(command)
