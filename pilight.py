#!/usr/bin/python

import collections
import ctypes
import errno
import math
import os
import select
import socket
import time
import traceback

import anims
import ctimerfd
import util

def on_timer (state):
        '''
        Called regularly to update colours.
        '''
        t = time.time () - state['start']
        for c in ['red', 'green', 'blue']:
                print '{:.2f}'.format (state[c].anim (state[c].speed * t + state[c].offset)),
        print

def eintr_wrap (fn, *args, **kwargs):
        '''
        Wrapper for socket functions that handles EINTR.
        '''
        while True:
                try:
                        return fn (*args, **kwargs)
                except socket.error as e:
                        if e.errno == errno.EINTR:
                                continue
                        raise

def wrap (fn, *args, **kwargs):
        '''
        Wrapper that logs & eats exceptions.
        '''
        try:
                fn (*args, **kwargs)
        except:
                traceback.print_exc ()

animstate = collections.namedtuple ('animstate', ('anim', 'speed', 'offset'))
netstate = collections.namedtuple ('netstate', ('socket', 'buf'))

def cmd_test_ok ():
        pass
def cmd_test_err ():
        raise Exception ('should fail')

commands = {
        b'test_ok': cmd_test_ok,
        b'test_err': cmd_test_err
}

def main ():
        state = {}
        state['start'] = time.time ()
        state['red'] = animstate (anims.sine, 2*math.pi, 0)
        state['green'] = animstate (anims.sine, 2*math.pi, 1/3 * math.pi)
        state['blue'] = animstate (anims.sine, 2*math.pi, 2/3 * math.pi)

        # Maps file descriptors to netstate instances
        connections = {}

        spec = ctimerfd.itimerspec ()
        spec.it_interval.tv_sec = 0
        spec.it_interval.tv_nsec = long (1e9/24)
        spec.it_value.tv_sec = 0
        spec.it_value.tv_nsec = 1
        t = ctimerfd.timerfd_create (ctimerfd.CLOCK_MONOTONIC, ctimerfd.TFD_CLOEXEC|ctimerfd.TFD_NONBLOCK)
        ctimerfd.timerfd_settime (t, 0, ctypes.pointer (spec), None)

        s = socket.socket (socket.AF_INET6, socket.SOCK_STREAM)
        s.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt (socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        s.bind (('', 12345))
        s.listen (5)

        epoll = select.epoll ()
        util.set_cloexec (epoll.fileno ()) # XXX As of Python 2.3, flags=EPOLL_CLOEXEC can be used when creating the epoll instead
        epoll.register (t, select.POLLIN)
        epoll.register (s, select.POLLIN)

        while True:
                for fd, event in eintr_wrap (epoll.poll):
                        # timer
                        if fd == t and event & select.POLLIN:
                                os.read (t, 8)
                                wrap (on_timer, state)
                        # listening socket
                        elif fd == s.fileno () and event & select.POLLIN:
                                conn, addr = eintr_wrap (s.accept)
                                print 'Connection accepted from [{}]:{} (fd={})'.format (addr[0], addr[1], conn.fileno ())
                                conn.setblocking (False)
                                epoll.register (conn.fileno (), select.POLLIN)
                                connections [conn.fileno ()] = netstate (conn, bytearray ())
                        # connection socket
                        elif fd in connections and event & select.POLLIN:
                                ns = connections[fd]
                                try:
                                        while True:
                                                x = eintr_wrap (ns.socket.recv, 4096)
                                                if len (x) == 0:
                                                        print 'Connection closed (fd={})'.format (ns.socket.fileno ())
                                                        del connections [ns.socket.fileno ()]
                                                        epoll.unregister (ns.socket.fileno ())
                                                        ns.socket.close ()
                                                        break
                                                ns.buf.extend (x)
                                except socket.error as e:
                                        if e.errno != errno.EAGAIN:
                                                raise
                                while True:
                                        try:
                                                i = ns.buf.index ('\r\n')
                                        except ValueError:
                                                break
                                        args = ns.buf[:i].split ()
                                        fn = commands.get (bytes (args[0]), None)
                                        if fn is None:
                                                eintr_wrap (ns.socket.send, b'500 Unknown command {}\r\n'.format (args[0]))
                                        else:
                                                try:
                                                        fn ()
                                                except Exception as e:
                                                        eintr_wrap (ns.socket.send, b'500 {}\r\n'.format (e))
                                                        traceback.print_exc ()
                                                else:
                                                        eintr_wrap (ns.socket.send, b'200 Ok\r\n')
                                        del ns.buf[:i+2]
                        else:
                                msg = 'Bad event (fd={} event={})'.format (fd, event)
                                raise Exception (msg)

if __name__ == '__main__':
        main ()
