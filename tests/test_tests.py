import io

from strategy.metrics import Metrics
from strategy.test import Test, TestSet, ICPCTestSet
from strategy.verdicts import TestVerdict


def test_testset():
    tests = [
        Test(1, io.StringIO("1 2"), io.StringIO("3")),
        Test(2, io.StringIO("1 -1"), io.StringIO("0")),
    ]

    testset = TestSet(tests)

    cnt = 0
    for test in testset:
        test.verdict = TestVerdict("ok", Metrics(10, 1, 1, "ok"))
        cnt += 1
        assert test.number == cnt

    assert cnt == len(tests)
    assert len(testset.verdicts()) == len(tests)
    for verdict in testset.verdicts():
        assert verdict.status == TestVerdict("ok", Metrics(10, 1, 1, "ok")).status
        assert verdict.metrics.time_ms == TestVerdict("ok", Metrics(10, 1, 1, "ok")).metrics.time_ms


def test_icpc_testset_ok():
    tests = [
        Test(1, io.StringIO("1 2"), io.StringIO("3")),
        Test(2, io.StringIO("1 -1"), io.StringIO("0")),
        Test(3, io.StringIO("100 200"), io.StringIO("300")),
    ]

    testset = ICPCTestSet(tests)

    cnt = 0
    for test in testset:
        test.verdict = TestVerdict("ok", Metrics(10, 1, 1, "ok"))
        cnt += 1
        assert test.number == cnt

    assert cnt == len(tests)
    assert len(testset.verdicts()) == len(tests)
    for verdict in testset.verdicts():
        assert verdict.status == TestVerdict("ok", Metrics(10, 1, 1, "ok")).status
        assert verdict.metrics.time_ms == TestVerdict("ok", Metrics(10, 1, 1, "ok")).metrics.time_ms
    assert testset.verdict.status == "ok"
    assert testset.verdict.first_test_failed is None


def test_icpc_testset_wa():
    tests = [
        Test(1, io.StringIO("1 2"), io.StringIO("3")),
        Test(2, io.StringIO("1 -1"), io.StringIO("0")),
        Test(3, io.StringIO("100 200"), io.StringIO("300")),
    ]

    testset = ICPCTestSet(tests)

    cnt = 0
    for test in testset:
        if cnt < 1:
            test.verdict = TestVerdict("ok", Metrics(10, 1, 1, "ok"))
        else:
            test.verdict = TestVerdict("wa", Metrics(10, 1, 1, "ok"))
        cnt += 1
        assert test.number == cnt

    assert cnt == len(tests) - 1
    assert len(testset.verdicts()) == len(tests) - 1
    assert testset.verdict.status == "wa"
    assert testset.verdict.first_test_failed == 2
