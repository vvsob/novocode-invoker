import asyncio
import io
import logging
import os
import shutil

import packageparser
import strategy
import traceback
import importlib
import redis
import signal
import time
import requests
import zipfile
import verdictserializer
import dateutil.parser
from dotenv import load_dotenv

load_dotenv()

NOVOCODE_HOST = os.environ.get("NOVOCODE_HOST")
NOVOCODE_PORT = int(os.environ.get("NOVOCODE_PORT"))
NOVOCODE_TOKEN = os.environ.get("NOVOCODE_TOKEN")
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT"))


def request_get(endpoint):
    url = f"http://{NOVOCODE_HOST}:{NOVOCODE_PORT}/api/{endpoint}"
    return requests.get(url, headers={'Authorization': f'Token {NOVOCODE_TOKEN}'})


def request_get_file(url):
    return requests.get(url, headers={'Authorization': f'Token {NOVOCODE_TOKEN}'})


def request_patch(endpoint, json):
    url = f"http://{NOVOCODE_HOST}:{NOVOCODE_PORT}/api/{endpoint}"
    requests.patch(url, json=json, headers={'Authorization': f'Token {NOVOCODE_TOKEN}'})


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


interrupted = False

submission_source_path = os.environ.get("SUBMISSION_SOURCE_PATH")
problem_xml_path = os.environ.get("PROBLEM_XML_PATH")
problem_directory_path = os.environ.get("PROBLEM_DIRECTORY_PATH")


def clear_downloaded_files():
    for file in os.listdir("./downloaded"):
        file_path = os.path.join('./downloaded', file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    for file in os.listdir(problem_directory_path):
        file_path = os.path.join(problem_directory_path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def download_problem_and_submission(submission_id):
    submission_response = request_get(f'submissions/{submission_id}').json()

    problem_id = str(submission_response["problem"])
    problem_response = request_get(f"problems/{problem_id}").json()

    submission_source_response = request_get_file(submission_response["source"])
    problem_xml_response = request_get_file(problem_response["problem_xml"])
    problem_zip_response = request_get_file(problem_response["problem_archive"])

    submission_timestamp = dateutil.parser.parse(submission_response["timestamp"])
    compiler_id = str(submission_response["compiler"])

    compiler_response = request_get(f'compilers/{compiler_id}').json()

    global submission_source_path
    submission_source_path = submission_source_path + compiler_response["file_extension"]

    with open(submission_source_path, mode='wb') as submission_source:
        submission_source.write(submission_source_response.content)
    with open(problem_xml_path, mode='wb') as problem_xml:
        problem_xml.write(problem_xml_response.content)
    with zipfile.ZipFile(io.BytesIO(problem_zip_response.content), 'r') as zip_ref:
        zip_ref.extractall(problem_directory_path)

    return strategy.Submission(
        strategy.File(submission_source_path),
        submission_timestamp, submission_response["owner"],
        compiler_response["compile_command"],
        compiler_response["run_command"]
    )


def run_strategy(strategy_path, arguments):
    strategy_mod = importlib.import_module(strategy_path.rsplit('.', 1)[0].replace('/', '.').lstrip('.'))
    importlib.reload(strategy_mod)
    verdict = asyncio.run(strategy_mod.run(*arguments))
    return verdict


def submit_verdict(submission_id, verdict):
    request_patch(f"submissions/{submission_id}", json={'verdict': verdict})


def loop(r):
    while not interrupted:
        if r.llen("novocode:submissions") == 0:
            time.sleep(0.1)
            continue
        submission_id = r.lpop("novocode:submissions")

        logging.info(f"Starting testing submission {submission_id}")
        try:
            submission = download_problem_and_submission(submission_id)
            strategy_path, arguments = packageparser.parse_package(problem_xml_path, problem_directory_path)
            verdict = run_strategy(strategy_path, [submission, *arguments])
            serialized_verdict = verdictserializer.get_verdict_serializer(verdict)(verdict)
            submit_verdict(submission_id, serialized_verdict)
            logging.info(f"Finished testing submission {submission_id}. Got verdict: {serialized_verdict}")
        except BaseException as ex:
            submit_verdict(submission_id, {"format": "judge_error"})
            logging.info(f"Failed to test {submission_id}, caught exception: {ex}")
            logging.info(f"{traceback.format_exception(ex)}")
        clear_downloaded_files()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Started Novocode Invoker.")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    loop(r)
    logging.info("Shutting down Novocode Invoker.")


if __name__ == "__main__":
    main()
