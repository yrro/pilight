#!/usr/bin/python

import argparse
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
import commands
import ctimerfd
import util

def on_timer (state):
        '''
        Called regularly to update colours.
        '''
        t = time.time () - state['start']
        for c in ['c_red', 'c_green', 'c_blue']:
                c = state[c]
                state['pipe'].write ('{}={:.2f}\n'.format (c['channel'], c['anim'] (c['speed'] * t + c['offset'])))
        state['pipe'].flush ()


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

def eagain_wrap (fn, *args, **kwargs):
        '''
        Wrapper for socket functions that converts an EAGAIN socket.error into
        a result of None.
        '''
        try:
                return fn (*args, **kwargs)
        except socket.error as e:
                if e.errno == errno.EAGAIN:
                        return None
                raise

def wrap (fn, *args, **kwargs):
        '''
        Wrapper that logs & eats exceptions.
        '''
        try:
                fn (*args, **kwargs)
        except:
                traceback.print_exc ()

netstate = collections.namedtuple ('netstate', ('socket', 'buf'))

def main ():
        a = argparse.ArgumentParser (description='Rasberry Pi LED flashing thingy')
        a.add_argument ('--pipe', '-p', help='Pi-blaster pipe', default='/dev/pi-blaster')
        args = a.parse_args ()


        state = {}
        state['start'] = time.time ()
        state['pipe'] = open (args.pipe, 'w')
        state['c_red'] = {'anim': anims.sine, 'speed': 2*math.pi, 'offset': 0, 'channel': 2}
        state['c_green'] = {'anim': anims.sine, 'speed': 2*math.pi, 'offset': 1/3 * math.pi, 'channel': 5}
        state['c_blue'] = {'anim': anims.sine, 'speed': 2*math.pi, 'offset': 2/3 * math.pi, 'channel': 6}

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
                                while True:
                                        x = eagain_wrap (eintr_wrap, ns.socket.recv, 4096)
                                        if x is None:
                                                break
                                        if len (x) == 0:
                                                print 'Connection closed (fd={})'.format (ns.socket.fileno ())
                                                del connections [ns.socket.fileno ()]
                                                epoll.unregister (ns.socket.fileno ())
                                                ns.socket.close ()
                                                break
                                        ns.buf.extend (x)
                                while True:
                                        try:
                                                i = ns.buf.index ('\r\n')
                                        except ValueError:
                                                break
                                        args = [bytes (x) for x in ns.buf[:i].split ()]
                                        del ns.buf[:i+2]

                                        fn = commands.commands.get (args[0], commands.unknown)
                                        try:
                                                fn (ns.socket, args[1:], state)
                                        except Exception as e:
                                                eintr_wrap (ns.socket.send, b'500 {}\r\n'.format (e))
                                                traceback.print_exc ()
                        # anything else is unexpected
                        else:
                                msg = 'Bad event (fd={} event={})'.format (fd, event)
                                raise Exception (msg)

if __name__ == '__main__':
        main ()
