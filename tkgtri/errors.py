class RecoveryManagerError(Exception):
    """Basic exception for errors raised by RecoveryManager"""
    pass


class OwaManagerError(Exception):
    pass


class OwaManagerErrorUnFilled(Exception):
    pass


class OwaManagerErrorSkip(Exception):
    pass


class OwaManagerCancelAttemptsExceeded(Exception):
    pass

