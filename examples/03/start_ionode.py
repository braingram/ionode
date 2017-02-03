#!/usr/bin/env python

import Queue
import socket
import StringIO
import threading
import time

import cv2
import PIL.Image
import pizco

import ionode.base

port = 21022

print_timing = True


class CaptureThread(threading.Thread):
    def __init__(self, capture_id=-1):
        self.stop_event = threading.Event()
        self.capture_id = capture_id
        self.queue = Queue.Queue(maxsize=10)
        super(CaptureThread, self).__init__()

    def run(self):
        c = cv2.VideoCapture(self.capture_id)
        while not self.stop_event.is_set():
            r, f = c.read()
            if r and not self.queue.full():
                self.queue.put(f)
        print("Releasing capture")
        del c

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


class CameraNode(ionode.base.IONode):
    def __init__(self, cfg=None):
        super(CameraNode, self).__init__(cfg)
        self.new_image = pizco.Signal(nargs=1)
        self.state = 'disconnected'
        self.streaming = False
        self.cam = None
        self.buffer = StringIO.StringIO()

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
            # convert to string
            self.buffer.seek(0)
            t1 = time.time()
            PIL.Image.fromarray(
                f[:, :, ::-1]).save(self.buffer, format='jpeg')
            t2 = time.time()
            n = self.buffer.pos
            self.buffer.seek(0)
            t3 = time.time()
            # base64 encode
            e = self.buffer.read(n).encode('base64')
            t4 = time.time()
            self.new_image.emit(e)
            t5 = time.time()
            if print_timing:
                print("Timing:[total %s]" % (t5 - t0))
                print("\tseek1    : %s" % (t1 - t0))
                print("\tpil      : %s" % (t2 - t1))
                print("\tseek2    : %s" % (t3 - t2))
                print("\tencode   : %s" % (t4 - t3))
                print("\tbroadcast: %s" % (t5 - t4))
        if self.streaming:
            self.loop.add_callback(self.grab, True)
        return

if __name__ == '__main__':
    cfg = {}
    cfg['addr'] = (
        'tcp://%s:%s' % (
            socket.gethostbyname(
                socket.gethostname() + '.local'), port))
    node = CameraNode(cfg)
    node.serve_forever()
