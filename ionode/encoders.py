#!/usr/bin/env python

from cStringIO import StringIO
import json

import numpy
import PIL.Image


class SetAwareEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (dict, )):
            return {k: self.default(obj[k]) for k in obj}
        if isinstance(obj, (tuple, list, set)):
            return [self.default(v) for v in obj]
        if isinstance(obj, (float, int, str, unicode)):
            return obj
        return super(SetAwareEncoder, self).default(obj)


class NumpyAwareEncoder(SetAwareEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            if obj.ndim == 1:
                return obj.tolist()
            elif obj.ndim == 0:
                return obj.item()
            else:  # Don't encode large arrays?
                return None
        elif isinstance(obj, numpy.generic):
            return obj.item()
        return super(NumpyAwareEncoder, self).default(obj)


class ImageAwareEncoder(NumpyAwareEncoder):
    def default(self, obj):
        if isinstance(obj, PIL.Image.Image):
            io = StringIO()
            obj.save(io, format='jpeg')
            io.seek(0)
            return io.read().encode('base64')
        return super(ImageAwareEncoder, self).default(obj)


default = ImageAwareEncoder
