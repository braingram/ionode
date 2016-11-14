#!/usr/bin/env python

import pizco

import ionode.base


class MyIONode(ionode.base.IONode):
    def __init__(self, cfg=None):
        super(MyIONode, self).__init__(cfg)
        self.mysignal = pizco.Signal(nargs=1)

    def trigger_signal(self, arg):
        print "Triggering signal with %s" % (arg, )
        self.mysignal.emit(arg)

if __name__ == '__main__':
    node = MyIONode('config.json')
    node.serve_forever()
