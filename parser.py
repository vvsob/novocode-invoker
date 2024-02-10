import io
import os
from strategy.test import Test, TestSet, ICPCTestSet
from strategy.metrics import Limits
from strategy.checker import Checker, TestlibChecker


def get_xml_tag_parser(tag):
    conversion = {
        "file": parse_file,
        "checker": parse_checker,
        "testlib_checker": parse_testlib_checker,
        "test_data": parse_test_data,
        "test": parse_test,
        "testset": parse_testset,
        "icpc_testset": parse_icpc_testset,
        "limits": parse_limits,
    }
    return conversion[tag]


def parse_file(node, path):
    return os.path.abspath(os.path.join(path, node.attrib["path"]))


def parse_checker(node, path):
    main_file = parse_file(list(node)[0], path)
    other_files = list(map(lambda child: parse_file(child, path), list(node[1:])))
    return Checker(main_file, *other_files)


def parse_testlib_checker(node, path):
    main_file = parse_file(list(node)[0], path)
    other_files = list(map(lambda child: parse_file(child, path), list(node[1:])))
    return TestlibChecker(main_file, *other_files)


def parse_test_data(node, path):
    if list(node):
        file = list(node)[0]
        return open(parse_file(file, path), mode='r')
    return io.StringIO(node.text)


def parse_test(node, path):
    input_data, output_data = map(lambda child: parse_test_data(child, path), list(node))
    return Test(int(node.attrib["number"]), input_data, output_data)


def parse_testset(node, path):
    tests = list(map(lambda child: parse_test(child, path), list(node)))
    return TestSet(tests)


def parse_icpc_testset(node, path):
    tests = list(map(lambda child: parse_test(child, path), list(node)))
    return ICPCTestSet(tests)


def parse_limits(node, path):
    return Limits(int(node.attrib["time_ms"]), int(node.attrib["memory_kb"]), int(node.attrib["real_time_ms"]))
