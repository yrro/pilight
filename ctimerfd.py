import ctypes
import ctypes.util

libc = ctypes.CDLL (ctypes.util.find_library ("c"), use_errno=True)

CLOCK_MONOTONIC = 1

TFD_CLOEXEC = 02000000
TFD_NONBLOCK = 00004000

timerfd_create = libc.timerfd_create
timerfd_create.argtypes = [ctypes.c_int, ctypes.c_int]
def res_timerfd_create (fd):
        if fd == -1:
                raise OSError (ctypes.get_errno ())
        assert fd >= 0
        return fd
timerfd_create.restype = res_timerfd_create

class timespec (ctypes.Structure):
        _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]

class itimerspec (ctypes.Structure):
        _fields_ = [("it_interval", timespec), ("it_value", timespec)]

timerfd_settime = libc.timerfd_settime
timerfd_settime.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER (itimerspec), ctypes.POINTER (itimerspec)]
def res_timerfd_settime (r):
        if r == -1:
                raise OSError (ctypes.get_errno ())
        assert r >= 0
        return r
timerfd_settime.restype = res_timerfd_settime
