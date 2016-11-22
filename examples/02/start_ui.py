#!/usr/bin/env python

import json
import socket
import webbrowser

import ionode.base
import ionode.ui.base

import pizco
from start_ionode import PiCameraNode, port


host_ip = socket.gethostbyname(socket.gethostname() + '.local')
proxy_addr = 'tcp://%s:%s' % (host_ip, port)

spec = {
    'template': open('template.html', 'r').read()
}

print("Use Ctrl-C in this terminal window to stop the ui and server")
p = pizco.Proxy(proxy_addr)
ionode.ui.register_proxy(p, 'tapecamera', PiCameraNode, spec)
ionode.ui.run(address=host_ip, debug=True)
