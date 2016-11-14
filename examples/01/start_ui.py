#!/usr/bin/env python

import json
import webbrowser

import ionode.base
import ionode.ui.base

url = 'http://127.0.0.1:5000/base'
config = json.load(open('config.json', 'r'))
print("Use Ctrl-C in this terminal window to stop the ui and server")
webbrowser.open(url)
ionode.ui.base.run_proxy_ui('base', config['addr'], ionode.base.IONode)
