#!/usr/bin/env python

import pizco

import ionode.base


class MyIONode(ionode.base.IONode):
    def __init__(self, cfg=None):
        super(MyIONode, self).__init__(cfg)
        self.mysignal1 = pizco.Signal(nargs=1)
        self.mysignal2 = pizco.Signal(nargs=1)
        self.counter = 0

    def trigger_signal1(self, arg):
        print "Triggering signal1 with %s" % (arg, )
        self.mysignal1.emit(arg)

    def trigger_signal2(self, arg):
        print "Triggering signal2 with %s" % (arg, )
        self.mysignal2.emit(arg)

    def update(self):
        self.mysignal2.emit(self.counter)
        self.counter += 1

if __name__ == '__main__':
    node = MyIONode('config.json')
    node.serve_forever()
