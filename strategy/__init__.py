import shutil
import stat
import uuid
import subprocess
import os
from .errors import CompileError


class Pipe:
    pass


class File:
    def __init__(self, path=None, role=None):
        if path is None:
            path = str(uuid.uuid4())
        if not os.path.exists(path):
            open(path, mode='w').close()
        self.path = path
        self.role = role

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.path):
            os.remove(self.path)

    def __str__(self):
        return self.path

    def read(self):
        with open(self.path, mode='r') as stream:
            text = stream.read()
        return text

    def write(self, text):
        with open(self.path, mode='w') as stream:
            stream.write(text)


class Submission(File):
    def __init__(self, file, timestamp, author, compile_command, run_command):
        super().__init__(file.path, file.role)
        self.timestamp = timestamp
        self.author = author
        self.compile_command = compile_command
        self.run_command = run_command


class Limits:
    def __init__(self, time_ms, memory_kb, real_time_ms):
        self.time_ms = time_ms
        self.memory_kb = memory_kb
        self.real_time_ms = real_time_ms


class Metrics:
    def __init__(self, time_ms, memory_kb, real_time_ms, status):
        self.time_ms = time_ms
        self.memory_kb = memory_kb
        self.real_time_ms = real_time_ms
        self.status = status


class Box:
    def __init__(self, files=[]):
        self.files = files
        self.box_path = None

    def __enter__(self):
        subprocess.run("isolate --cleanup", shell=True)
        isolate_init_result = subprocess.run("isolate --init", capture_output=True, text=True, shell=True)
        self.box_path = os.path.join(isolate_init_result.stdout.strip(), 'box')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.run("isolate --cleanup", shell=True)

    def init_stdin(self, stdin):
        data_in_path = os.path.join(self.box_path, "__data.in")
        if stdin is None:
            open(data_in_path, mode='w').close()
        elif isinstance(stdin, File):
            os.link(stdin.path, data_in_path)
        elif isinstance(stdin, str):
            with open(data_in_path, mode='w') as data_in:
                data_in.write(stdin)
        elif isinstance(stdin, TestData):
            with open(data_in_path, mode='w') as data_in:
                data_in.write(stdin.get())
        else:
            raise NotImplementedError()

    def init_stdout(self, stdout):
        data_out_path = os.path.join(self.box_path, "__data.out")
        if isinstance(stdout, File):
            open(data_out_path, mode='w').close()
            if os.path.exists(stdout.path):
                os.remove(stdout.path)
            os.link(data_out_path, stdout.path)
        elif stdout is not None:
            raise NotImplementedError()

    def init_files(self):
        for file in self.files:
            os.link(file.path, os.path.join(self.box_path, os.path.basename(file.path)))

    def parse_meta_properties(self, meta_properties):
        time_ms = float(meta_properties['time']) * 1000
        real_time_ms = float(meta_properties['time-wall']) * 1000
        memory_kb = int(meta_properties['max-rss'])
        status = "ok"
        if 'status' in meta_properties:
            status = {"RE": "re", "SG": "ml", "TO": "tl", "XX": "cf"}[meta_properties["status"]]
        return Metrics(time_ms, memory_kb, real_time_ms, status)

    def execute_isolate(self, command, limits):
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

    def run(self, command, stdin, stdout, limits):
        if self.box_path is None:
            raise EnvironmentError()
        self.init_stdin(stdin)
        self.init_stdout(stdout)
        self.init_files()
        metrics = self.execute_isolate(command, limits)
        return metrics


def run_isolated(command, stdin=None, stdout=None, files=[], limits=Limits(15000, 512*1024, 30000)):
    with Box(files) as box:
        metrics = box.run(command, stdin, stdout, limits)
    return metrics


class Executable:
    def __init__(self, main_file, *args, run_command="{0} {1}"):
        if isinstance(main_file, File):
            self.main_file = main_file
        elif isinstance(main_file, str):
            self.main_file = File(main_file)
        st = os.stat(self.main_file.path)
        os.chmod(self.main_file.path, st.st_mode | stat.S_IEXEC)
        self.files = args
        self.run_command = run_command

    def __call__(self, stdin=None, stdout=None, files=[], limits=Limits(15000, 512*1024, 30000), args=[]):
        metrics = run_isolated(
            self.run_command.format(os.path.basename(self.main_file.path), ' '.join(args)),
            stdin,
            stdout,
            [self.main_file] + list(files) + list(self.files),
            limits
        )
        return metrics


class TestData:
    def __init__(self, data):
        self.data = data

    def get(self):
        if isinstance(self.data, str):
            return self.data
        if isinstance(self.data, File):
            return self.data.read()
        raise NotImplementedError()


class Test:
    def __init__(self, number, input, answer):
        self.number = number
        self.input = input
        self.answer = answer


class TestSet:
    def __init__(self, tests):
        self.tests = tests

    def __iter__(self):
        return self.tests.__iter__()

    def __next__(self):
        return self.tests.__next__()


async def compile(file):
    if not file.compile_command:
        return Executable(file.path, run_command=file.run_command)
    executable_path = file.path + '.out'
    with (Box([file]) as box):
        metrics = box.run(
            file.compile_command.format(
                os.path.basename(file.path),
                os.path.basename(executable_path)
            ),
            None,
            None,
            Limits(15000, 512*1024, 30000))
        shutil.copyfile(os.path.join(box.box_path, os.path.basename(executable_path)), executable_path)
    if metrics.status != 'ok':
        raise CompileError()
    return Executable(executable_path, run_command=file.run_command)
