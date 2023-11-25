import strategy.verdicts


def get_verdict_serializer(verdict):
    serializers = {
        strategy.verdicts.TestVerdict: serialize_test,
        strategy.verdicts.ICPCVerdict: serialize_icpc,
    }
    return serializers[type(verdict)]


def serialize_metrics(metrics):
    return {
        'time_ms': metrics.time_ms,
        'memory_kb': metrics.memory_kb,
        'real_time_ms': metrics.real_time_ms,
        'status': metrics.status,
    }


def serialize_test(verdict):
    return {
        'metrics': serialize_metrics(verdict.metrics),
        'status': verdict.status,
    }


def serialize_icpc(verdict):
    return {
        'format': 'icpc',
        'first_test_failed': verdict.first_test_failed,
        'per_test_metrics': [
            serialize_test(test) for test in verdict.per_test_verdicts
        ]
    }
