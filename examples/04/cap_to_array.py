#!/usr/bin/env python

import time

import numpy
import PIL.Image

import picamera


def round_resolution(r):
    return (
        (r[0] + 31) // 32 * 32,
        (r[1] + 15) // 16 * 16)


res = (2592, 1944)
roi = (0, 500, 2592, 50)
fmt = 'rgba'
ndim = len(fmt)


rres = round_resolution(res)
raw = numpy.empty(rres[1] * rres[0] * ndim, dtype='uint8')
zoom = (
    roi[0] / float(res[0]),
    roi[1] / float(res[1]),
    roi[2] / float(res[0]),
    roi[3] / float(res[1]),
)

region = (roi[2], roi[3])
rregion = round_resolution(region)

cam = picamera.PiCamera()
cam.resolution = res
cam.zoom = zoom

t0 = time.time()
cam.capture(raw, fmt, resize=rregion)
t1 = time.time()
r = raw[:(rregion[1] * rregion[0] * ndim)].reshape((rregion[1], rregion[0], ndim))
o = r[:region[1], :region[0], :]

t2 = time.time()
im = PIL.Image.fromarray(o)
t3 = time.time()
im.save('im.jpg')
t4 = time.time()
print("cap : %s" % (t1 - t0))
print("crop: %s" % (t2 - t1))
print("pil : %s" % (t3 - t2))
print("save: %s" % (t4 - t3))
