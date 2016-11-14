#!/usr/bin/env python

import inspect
import os


from tornado.ioloop import IOLoop

import pizco
import wsrpc

from .. import encoders


module_folder = os.path.abspath(
    os.path.dirname(inspect.getfile(inspect.currentframe())))
static_folder = os.path.abspath(os.path.join(module_folder, 'static'))
template_folder = os.path.abspath(os.path.join(module_folder, 'templates'))


def add_wsrpc_to_proxy(p, klass):
    # lookup class
    spec = wsrpc.wrapper.build_function_spec(klass)
    # have to be creative to assign attribute to the proxy
    p.__dict__['__wsrpc__'] = lambda s=spec: s
    return p


def build_spec(obj, name):
    spec = {
        'name': name,
        'object': obj,
        'static_folder': static_folder,
        'template_folder': template_folder,
        'template': open(
            os.path.join(template_folder, 'base.html'), 'r').read(),
        'encoder': encoders.default,
    }
    return spec


def run_proxy_ui(name, addr, klass):
    p = pizco.Proxy(addr)
    add_wsrpc_to_proxy(p, klass)
    if hasattr(IOLoop, '_instance'):
        del IOLoop._instance
    wsrpc.serve.register(build_spec(p, name))
    wsrpc.serve.serve()
