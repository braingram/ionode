#!/usr/bin/env python

import ionode.base

node = ionode.base.IONode('config.json')
node.serve_forever()
