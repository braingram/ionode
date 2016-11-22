#!/usr/bin/env python

import socket
import StringIO
import time

import numpy
import picamera
import PIL.Image
import pizco
import tornado.ioloop

import ionode.base

port = 21022


class PiCameraNode(ionode.base.IONode):
    def __init__(self, cfg=None):
        super(PiCameraNode, self).__init__(cfg)
        self.new_image = pizco.Signal(nargs=1)
        self.state = 'disconnected'
        self.cam = None
        self.buffer = StringIO.StringIO()

    def connect(self):
        if self.cam is not None:
            return
        print("Connecting to camera")
        self.cam = picamera.PiCamera()
        #self._cb = self.loop.add_callback(self._grab)

    def disconnect(self):
        if self.cam is None:
            return
        print("Disconnecting from camera")
        self.cam.close()
        self.cam = None

    def connected(self):
        return self.cam is not None

    def grab(self, in_callback=False):
        if not self.connected(): return
        print("grab")
        if not in_callback:
             return self.loop.add_callback(self.grab, True)
        print("grab in loop")
        self.buffer.seek(0)
        self.cam.capture(self.buffer, 'jpeg', use_video_port=True)
        #self.cam.capture(self.buffer, 'jpeg')
        n = self.buffer.pos
        self.buffer.seek(0)
        self.new_image.emit(self.buffer.read(n).encode('base64'))
        return
        h = self.cam.resolution.height
        w = self.cam.resolution.width
        im = numpy.empty((h * w * 3), dtype='uint8')
        self.cam.capture(im, 'rgb', use_video_port=True)
        im = im.reshape((h, w, 3))
        self.new_image_array.emit(im)
        self.new_image.emit(PIL.Image.fromarray(im))

    def set_property(self, name, value):
        if not self.connected(): return
        setattr(self.cam, name, value)

    def get_property(self, name):
        if not self.connected(): return
        v = getattr(self.cam, name)
        if (name == 'resolution'):
            return tuple(v)
        return v


if __name__ == '__main__':
    cfg = {}
    cfg['addr'] = (
    'tcp://%s:%s' % (
            socket.gethostbyname(socket.gethostname() + '.local'), port))
    node = PiCameraNode(cfg)
    node.serve_forever()
