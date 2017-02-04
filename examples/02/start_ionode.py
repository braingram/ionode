#!/usr/bin/env python

import Queue
import socket
import StringIO
import threading
import time

import picamera
import pizco

import ionode.base

port = 21022

print_timing = True


class CaptureThread(threading.Thread):
    def __init__(self, capture_id=-1):
        self.stop_event = threading.Event()
        self.capture_id = capture_id
        self.queue = Queue.Queue(maxsize=10)
        self.cmds = Queue.Queue(maxsize=10)
        self.results = Queue.Queue(maxsize=10)
        super(CaptureThread, self).__init__()

    def run(self):
        cam = picamera.PiCamera()
        while not self.stop_event.is_set():
            s = StringIO.StringIO()
            cam.capture(s, 'jpeg', use_video_port=True)
            s.seek(0)
            if not self.queue.full():
                self.queue.put(s)
            if not self.cmds.empty():
                cmd = self.cmds.get()
                if cmd[0] == 'get':
                    n = cmd[1]
                    r = getattr(self.cam, n)
                    if n == 'resolution':
                        r = tuple(r)
                    self.results.put((n, r))
                else:
                    r = setattr(self.cam, cmd[1], cmd[2])

        print("Releasing capture")
        cam.close()
        del cam

    def get_property(self, name):
        self.cmds.put(('get', name))
        r = self.results.get()
        if r[0] != name:
            raise Exception
        return r[1]

    def set_property(self, name, value):
        self.cmds.put(('set', name, value))

    def stop(self):
        print("CaptureThread.stop called")
        self.stop_event.set()

    def get_frame(self, recent=False, wait=False):
        try:
            f = self.queue.get(wait)
            if not recent:
                return f
            while not self.queue.empty():
                f = self.queue.get(wait)
        except Queue.Empty:
            return None
        return f


class PiCameraNode(ionode.base.IONode):
    def __init__(self, cfg=None):
        super(PiCameraNode, self).__init__(cfg)
        self.new_image = pizco.Signal(nargs=1)
        self.state = 'disconnected'
        self.streaming = False
        self.cam = None

    def start_streaming(self):
        if self.streaming:
            return
        self.streaming = True
        self.grab()

    def stop_streaming(self):
        if not self.streaming:
            return
        self.streaming = False

    def connect(self):
        if self.cam is not None:
            return
        print("Connecting to camera")
        self.cam = CaptureThread()
        self.cam.start()
        self.start_streaming()

    def disconnect(self):
        if self.cam is None:
            return
        print("Disconnecting from camera")
        self.stop_streaming()
        self.cam.stop()
        self.cam.join()
        self.cam = None

    def connected(self):
        return self.cam is not None

    def grab(self, in_callback=False):
        if not self.connected():
            return
        if not in_callback:
            return self.loop.add_callback(self.grab, True)
        f = self.cam.get_frame(recent=True)
        if f is not None and self.streaming:
            t0 = time.time()
            # base64 encode
            e = self.buffer.read().encode('base64')
            t1 = time.time()
            self.new_image.emit(e)
            t2 = time.time()
            if print_timing:
                print("Timing:[total %s]" % (t2 - t0))
                print("\tencode   : %s" % (t1 - t0))
                print("\tbroadcast: %s" % (t2 - t1))
        if self.streaming:
            self.loop.add_callback(self.grab, True)
        return

    def set_property(self, name, value):
        if not self.connected():
            return
        self.cam.set_property(name, value)

    def get_property(self, name):
        if not self.connected():
            return
        return self.cam.get_property(name)


if __name__ == '__main__':
    cfg = {}
    cfg['addr'] = (
        'tcp://%s:%s' % (
            socket.gethostbyname(
                socket.gethostname() + '.local'), port))
    node = PiCameraNode(cfg)
    node.serve_forever()
