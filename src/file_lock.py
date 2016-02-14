"""Implements unix file_lock as a context manager"""
import signal
import fcntl
import errno
from contextlib import contextmanager

@contextmanager
def file_lock(filed, exclusive=False):
    """Non-blocking file lock context manager"""
    opcode = [fcntl.LOCK_SH, fcntl.LOCK_EX][exclusive] | fcntl.LOCK_NB
    try:
        try:
            fcntl.flock(filed, opcode)
        except IOError, err:
            if not (err.errno == errno.EAGAIN or err.errno == errno.EACCES):
                raise
            else:
                yield False
        else:
            yield True
    except:
        raise
    finally:
        fcntl.flock(filed, fcntl.LOCK_UN)