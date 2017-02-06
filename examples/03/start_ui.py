#!/usr/bin/env python

import ionode.base
import ionode.ui.base

import pizco
from start_ionode import CameraNode, host, port


proxy_addr = 'tcp://%s:%s' % (host, port)

spec = {
    'template': open('template.html', 'r').read()
}

print("Use Ctrl-C in this terminal window to stop the ui and server")
p = pizco.Proxy(proxy_addr)
ionode.ui.register_proxy(p, 'tapecamera', CameraNode, spec)
print("Running ui on: %s" % host)
print("URL: http://%s:5000/tapecamera" % host)
ionode.ui.run(address=host, debug=True)
