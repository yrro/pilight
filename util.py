import fcntl

def set_cloexec (fd):
        flags = fcntl.fcntl (fd, fcntl.F_GETFD)
        fcntl.fcntl (fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)
