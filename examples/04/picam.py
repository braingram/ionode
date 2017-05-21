#!/usr/bin/env python

import time

import numpy
import PIL.Image

import picamera


def round_resolution(r):
    return (
        (r[0] + 31) // 32 * 32,
        (r[1] + 15) // 16 * 16)



class PiCam(picamera.PiCamera):
    def __init__(self, *args, **kwargs):
        super(PiCam, self).__init__(*args, **kwargs)
        r = self.resolution
        self._fmt = 'rgba'
        self._resize = None
        self._roi = (0, 0, r[0], r[1])
        self.resolution = r

    def _setup_buffer(self, res):
        roi = self._roi
        rroi = round_resolution((roi[2], roi[3]))
        rres = round_resolution(res)
        ndim = len(self._fmt)
        self._ro = numpy.empty((rres[1] * rres[0] * ndim), dtype='uint8')
        nroi = rroi[0] * rroi[1] * ndim
        self._o = self._ro.view('uint8')[:nroi].reshape(
            (rroi[1], rroi[0], ndim))[:roi[3], :roi[2], :]
        self._resize = rroi
    
    @picamera.PiCamera.resolution.setter
    def resolution(self, res):
        picamera.PiCamera.resolution.fset(self, res)
        self.roi = self.roi
        self._setup_buffer(res)

    #@picamera.PiCamera.resolution.getter
    #def resolution(self):
    #    return tuple(picamera.PiCamera.resolution.fget(self))

    #@picamera.PiCamera.framerate.getter
    #def framerate(self):
    #    return tuple(picamera.PiCamera.framerate.fget(self))

    @property
    def roi(self):
        return self._roi

    @roi.setter
    def roi(self, roi):
        # TODO error check
        self._roi = roi
        res = self.resolution
        self.zoom = (
            roi[0] / float(res[0]),
            roi[1] / float(res[1]),
            roi[2] / float(res[0]),
            roi[3] / float(res[1]),
        )
        self._setup_buffer(res)

    @property
    def fmt(self):
        return self._fmt

    @fmt.setter
    def fmt(self, fmt):
        self._fmt = fmt
        self._setup_buffer(self.resolution)

    def capture(self):
        super(PiCam, self).capture(
            self._ro, self._fmt, resize=self._resize)
        return self._o
