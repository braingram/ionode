#!/usr/bin/env python

import Queue
import socket
import StringIO
import threading
import time

import picamera
import picamera.array
import PIL.Image
import pizco

try:
    import cv2
    has_cv2 = True
except ImportError:
    has_cv2 = False

import ionode.base

port = 21022

print_timing = True

#ctype = 'jpeg'  # capture to jpeg
#ctype = 'yuv'  # capture to yuv (numpy array)
ctype = 'rgb'

etype = 'pil'
#etype = 'cv2'

if etype == 'cv2' and not has_cv2:
    raise ImportError("cv2 import failed")

resolution = (2592, 1944)

if ctype == 'rgb':
    use_video_port = False
else:
    use_video_port = True


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
        last_frame_time = time.time()
        if resolution is not None:
            cam.resolution = resolution
        while not self.stop_event.is_set():
            t0 = time.time()
            if ctype == 'jpeg':
                s = StringIO.StringIO()
                cam.capture(s, 'jpeg', use_video_port=use_video_port)
                s.seek(0)
                f = s
            elif ctype == 'yuv':
                f = picamera.array.PiYUVArray(cam)
                cam.capture(f, 'yuv', use_video_port=use_video_port)
                f = f.array
            elif ctype == 'rgb':
                f = picamera.array.PiRGBArray(cam)
                cam.capture(f, 'rgb', use_video_port=use_video_port)
                f = f.array
            else:
                raise ValueError("Unknown ctype: %s" % ctype)
            t1 = time.time()
            if self.queue.full():
                self.queue.get()
            self.queue.put(f)
            t2 = time.time()
            if not self.cmds.empty():
                cmd = self.cmds.get()
                n = cmd[1]
                r = None
                if not hasattr(cam, n):
                    r = Exception("invalid property: %s" % n)
                else:
                    if cmd[0] == 'get':
                        try:
                            r = getattr(cam, n)
                            if n in ('resolution', 'framerate'):
                                r = tuple(r)
                        except Exception as e:
                            r = e
                    else:
                        try:
                            setattr(cam, n, cmd[2])
                        except Exception as e:
                            r = e
                self.results.put((n, r))
            t3 = time.time()
            if print_timing:
                print("capture: %0.4f" % (t1 - t0))
                print("queue  : %0.4f" % (t2 - t1))
                print("cmds   : %0.4f" % (t3 - t2))
                fps = 1. / (t2 - last_frame_time)
                print("fps    : %0.2f" % fps)
                last_frame_time = t2

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
        r = self.results.get()
        if r[1] is not None:
            raise r[1]

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
        self.last_frame_time = time.time()

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
        if not self.streaming:
            return
        f = self.cam.get_frame(recent=True)
        dt = time.time() - self.last_frame_time
        tdt = 1. / self.config()['fps']
        if dt < tdt:
            return self.loop.add_callback(self.grab, True)
        if f is not None:
            if ctype == 'yuv' and etype == 'pil':
                s = StringIO.StringIO()
                PIL.Image.fromarray(
                    f[:, :, 0]).save(s, format='jpeg')
                s.seek(0)
                f = s.read()
            elif ctype == 'rgb' and etype == 'pil':
                s = StringIO.StringIO()
                PIL.Image.fromarray(f).save(s, format='jpeg')
                s.seek(0)
                f = s.read()
            elif ctype == 'yuv' and etype == 'cv2':
                _, b = cv2.imencode('.jpg', f[:, :, 0])
                f = b.tostring()
            elif ctype == 'rgb' and etype == 'cv2':
                _, b = cv2.imencode('.jpg', f)
                f = b.tostring()
            t0 = time.time()
            self.last_frame_time = t0
            # base64 encode
            e = f.encode('base64')
            t1 = time.time()
            self.new_image.emit(e)
            t2 = time.time()
            if print_timing:
                print(
                    "Timing:[total %s, dt: %s, fps: %s]"
                    % (t2 - t0, dt, 1. / dt))
                print("\tencode   : %s" % (t1 - t0))
                print("\tbroadcast: %s" % (t2 - t1))
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
    cfg['fps'] = 5
    node = PiCameraNode(cfg)
    node.serve_forever()
