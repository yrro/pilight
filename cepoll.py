import ctypes
import ctypes.util

libc = ctypes.CDLL (ctypes.util.find_library ("c"), use_errno=True)

EPOLL_CLOEXEC = 02000000

epoll_create = libc.epoll_create
epoll_create.argtypes = [ctypes.c_int]
def res_epoll_create (fd):
        if fd == -1:
                raise OSError (ctypes.get_errno ())
        assert fd >= 0
        return fd
epoll_create.restype = res_epoll_create
