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

def main ():
        spec = ctimerfd.itimerspec ()
        spec.it_interval.tv_sec = 0
        spec.it_interval.tv_nsec = long (1e9/60)
        spec.it_value.tv_sec = 0
        spec.it_value.tv_nsec = 1
        t = ctimerfd.timerfd_create (ctimerfd.CLOCK_MONOTONIC, ctimerfd.TFD_CLOEXEC|ctimerfd.TFD_NONBLOCK)
        ctimerfd.timerfd_settime (t, 0, ctypes.pointer (spec), None)

        poll = select.epoll.fromfd (cepoll.epoll_create (cepoll.EPOLL_CLOEXEC))
        poll.register (t, select.EPOLLIN)

        while True:
                try:
                        for fd, event in poll.poll ():
                                try:
                                        if fd == t:
                                                on_timer ()
                                except:
                                        traceback.print_exc ()
                except IOError, e:
                        if e.errno == errno.EINTR:
                                continue
                        raise

if __name__ == '__main__':
        main ()
