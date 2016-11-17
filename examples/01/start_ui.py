#!/usr/bin/env python

import json
import webbrowser

import ionode.base
import ionode.ui.base

import pizco
from start_ionode import MyIONode

spec = {
    'template': open('template.html', 'r').read()
}

url = 'http://127.0.0.1:5000/base'
config = json.load(open('config.json', 'r'))
print("Use Ctrl-C in this terminal window to stop the ui and server")
webbrowser.open(url)
p = pizco.Proxy(config['addr'])
ionode.ui.register_proxy(p, 'base', MyIONode, spec)
ionode.ui.run(debug=True)
