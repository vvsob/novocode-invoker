import os
import shutil
import stat
import subprocess
import logging
from typing import Iterable, IO

from strategy.box import Box, TrustedBox
from strategy.errors import CompileError
from strategy.metrics import Limits


class Executable:
    def __init__(self, main_file: str, files: Iterable[str] = iter([]), run_command="{0} {1}"):
        self.main_file = main_file
        st = os.stat(self.main_file)
        os.chmod(self.main_file, st.st_mode | stat.S_IEXEC)
        self.files = files
        self.run_command = run_command

    def __call__(self,
                 stdin: IO[str] | None = None,
                 stdout: IO[str] | None = None,
                 files: Iterable[str] = iter([]),
                 limits: Limits | None = Limits(15000, 512 * 1024, 30000),
                 args: Iterable[str] = iter([])):
        with Box([self.main_file] + list(files) + list(self.files)) as box:
            metrics = box.run(
                self.run_command.format(os.path.basename(self.main_file), ' '.join(args)),
                stdin,
                stdout,
                limits
            )
        return metrics


class Compilable:
    def __init__(self, file: str, compile_command: str, run_command: str):
        self.file = file
        self.compile_command = compile_command
        self.run_command = run_command

    def compile(self, executable_path=None):
        if not self.compile_command:
            return Executable(self.file, run_command=self.run_command)
        if executable_path is None:
            executable_path = self.file + '.out'
        with (Box([self.file]) as box):
            metrics = box.run(
                self.compile_command.format(
                    os.path.basename(self.file),
                    os.path.basename(executable_path)
                ),
                None,
                None,
                Limits(15000, 512 * 1024, 30000))
            shutil.copyfile(os.path.join(box.box_path, os.path.basename(executable_path)), executable_path)
        if metrics.status != 'ok':
            raise CompileError()
        return Executable(executable_path, run_command=self.run_command)


class TrustedExecutable(Executable):
    def __call__(self,
                 stdin: IO[str] | None = None,
                 stdout: IO[str] | None = None,
                 files: Iterable[str] = iter([]),
                 limits: Limits | None = None,
                 args: Iterable[str] = iter([])):
        with TrustedBox([self.main_file] + list(files) + list(self.files)) as box:
            exitcode = box.run(
                self.run_command.format(os.path.basename(self.main_file), ' '.join(args)),
                stdin,
                stdout,
                limits
            )
        return exitcode


class TrustedCompilable(Compilable):
    def compile(self, executable_path=None):
        if not self.compile_command:
            return Executable(self.file, run_command=self.run_command)
        if executable_path is None:
            executable_path = self.file + '.out'
        with TrustedBox([self.file]) as box:
            exitcode = box.run(
                self.compile_command.format(
                    os.path.basename(self.file),
                    os.path.basename(executable_path)
                ),
                None,
                None)
            shutil.copyfile(os.path.join(box.box_path, os.path.basename(executable_path)), executable_path)
        if exitcode != 0:
            raise CompileError()
        return Executable(executable_path, run_command=self.run_command)
