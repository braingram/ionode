#!/usr/bin/env python

import time

import pizco
import tornado.ioloop

import ionode.base


class MyIONode(ionode.base.IONode):
    def __init__(self, cfg=None):
        super(MyIONode, self).__init__(cfg)
        self.mysignal1 = pizco.Signal(nargs=1)
        self.mysignal2 = pizco.Signal(nargs=1)
        self._update_cb = None
        self.counter = 0

    def trigger_signal1(self, arg):
        print "Triggering signal1 with %s" % (arg, )
        self.mysignal1.emit(arg)

    def trigger_signal2(self, arg):
        print "Triggering signal2 with %s" % (arg, )
        self.mysignal2.emit(arg)

    def connect(self):
        if self._update_cb is not None:
            return
        self._update_cb = tornado.ioloop.PeriodicCallback(
            self.update, 500, self.loop)
        self._update_cb.start()

    def disconnect(self):
        if self._update_cb is None:
            return
        self._update_cb.stop()
        while self._update_cb._running:
            time.sleep(0.1)
        self._update_cb = None

    def connected(self):
        return self._update_cb is not None

    def update(self):
        self.mysignal2.emit(self.counter)
        self.counter += 1

if __name__ == '__main__':
    node = MyIONode('config.json')
    node.serve_forever()
