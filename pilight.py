#!/usr/bin/python

import ctypes
import errno
import os
import select
import traceback

import cepoll
import ctimerfd

def on_timer ():
        pass

def eintr_wrap (fn, *args, **kwargs):
        while True:
                try:
                        return fn (*args, **kwargs)
                except IOError, e:
                        if e.errno == errno.EINTR:
                                continue
                        raise

def wrap (fn, *args, **kwargs):
        try:
                fn (*args, **kwargs)
        except:
                traceback.print_exc ()

def main ():
        spec = ctimerfd.itimerspec ()
        spec.it_interval.tv_sec = 0
        spec.it_interval.tv_nsec = long (1e9/60)
        spec.it_value.tv_sec = 0
        spec.it_value.tv_nsec = 1
        t = ctimerfd.timerfd_create (ctimerfd.CLOCK_MONOTONIC, ctimerfd.TFD_CLOEXEC|ctimerfd.TFD_NONBLOCK)
        ctimerfd.timerfd_settime (t, 0, ctypes.pointer (spec), None)

        epoll = select.epoll.fromfd (cepoll.epoll_create (cepoll.EPOLL_CLOEXEC))
        epoll.register (t, select.EPOLLIN)

        while True:
                for fd, event in eintr_wrap (epoll.poll):
                        if fd == t:
                                os.read (t, 8)
                                wrap (on_timer)

if __name__ == '__main__':
        main ()
