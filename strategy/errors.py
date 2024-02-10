class NovocodeError(Exception):
    pass


class CompileError(NovocodeError):
    pass


class NoVerdictError(NovocodeError):
    pass
