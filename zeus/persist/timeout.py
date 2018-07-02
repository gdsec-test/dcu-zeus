import os
import errno
import signal
from functools import wraps


# Solution extracted from a StackOverflow selected answer
# http://stackoverflow.com/questions/2281850/timeout-function-if-it-takes-too-long-to-finish

class TimeoutError(Exception):
    pass


# - - - DECORATOR FUNCTION - - - #
# Default timeout of 2 seconds, which can be changed (to 5 seconds) inside the
#  decorator call as such: @timeout(5)
# Usage: Add following above function declaration: @timeout()
def timeout(seconds=2, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator
