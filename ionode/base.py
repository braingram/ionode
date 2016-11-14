#!/usr/bin/env python

import copy
import os
import signal
import socket
import sys
import time

import pizco
import zmq

from . import config
from . import log

logger = log.get_logger(__name__)

if not (zmq.zmq_version_info()[0] >= 3):
    logger.error(
        "ZMQ version[%s] is too old [<3]", zmq.zmq_version())
    raise ImportError(
        "ZMQ version[{}] is too old [<3]".format(zmq.zmq_version()))


class PizcoNodeServer(pizco.Server):
    def return_as_remote(self, attr):
        if pizco.Server.return_as_remote(self, attr):
            return True
        if isinstance(attr, IONode):
            return True
        return False


class IONode(object):
    def __init__(self, cfg=None):
        cfg = config.parse(cfg)
        if cfg is not None:
            if not isinstance(cfg, dict):
                raise TypeError(
                    "Config must be a dict not {}".format(type(cfg)))
            self._config = cfg
        else:
            self._config = {}
        self.loop = None  # will be replaced with server ioloop
        self._server = None
        self._log_handler = None
        self.config_changed = pizco.Signal(nargs=1)
        logger.info("%s[%s] created", type(self), self)

    def set_log_level(self, level):
        log.set_level_for_all_loggers(level)

    def start_logging(self, directory, level=None):
        logger.info(
            "%s[%s] start_logging: %s, %s", type(self), self, directory, level)
        if self._log_handler is not None:
            self.stop_logging()
        fn = os.path.join(
            directory, '_'.join(
                (self.__module__.split('.')[-1],
                 socket.gethostname(), str(os.getpid()),
                 time.strftime('%y%m%d%H%M%S'))) + '.log')
        self._log_handler = log.log_to_filename(fn, level)

    def stop_logging(self):
        if self._log_handler is None:
            return
        logger.info("%s[%s] stop_logging", type(self), self)
        log.stop_logging_to_handler(self._log_handler)

    def connect(self):
        pass

    def disconnect(self):
        pass

    def connected(self):
        pass

    def __del__(self):
        logger.debug("%s[%s] __del__", type(self), self)
        if self.connected():
            self.disconnect()

    def config_delta(self, delta):
        """Override this to respond to changes in config
        without listening to a signal"""
        pass

    def config(self, value=None, replace=False):
        if value is None:
            return self._config
        if replace:
            logger.info(
                "Configuring %s[%s] replacing with %s",
                type(self), self, value)
        else:
            logger.info(
                "Configuring %s[%s] appending %s",
                type(self), self, value)
        value = config.parse(value)
        if not isinstance(value, dict):
            raise TypeError(
                "Config must be a dict not {}".format(type(value)))
        if value == self._config:
            return self._config
        if replace:
            new_config = copy.deepcopy(value)
        else:
            new_config = config.cascade(self._config, value)
        # make sure new_config is valid
        delta = config.delta(self._config, new_config)
        try:
            self.check_config(new_config)
            self._config = new_config
        except config.base.ConfigError as e:
            logger.error("Received invalid config {}".format(e), exc_info=e)
            delta = {}
        if delta != {}:
            self.config_delta(delta)
        self.config_changed.emit(self._config)

    def check_config(self, cfg=None):
        pass

    def serve_forever(self):
        # need to generate pub address as it defaults to loopback
        addr = self.config()['addr']
        tokens = addr.split(':')
        pub_addr = ':'.join(tokens[:-1] + [str(int(tokens[-1]) + 100), ])
        self._server = PizcoNodeServer(self, addr, pub_addr)
        self.loop = self._server.loop
        logger.info("Serving %s[%s] on %s", type(self), self,
                    self.config()['addr'])

        def quit_gracefully(*args):
            print("Quitting: %s" % (args, ))
            if self.connected():
                self.disconnect()
            sys.exit(0)

        signal.signal(signal.SIGINT, quit_gracefully)
        signal.signal(signal.SIGTERM, quit_gracefully)
        self._server.serve_forever()

    def save_config(self, fn):
        logger.info("%s[%s] saving config to %s: %s", type(self), self, fn,
                    self.config())
        config.save(self.config(), fn)

    def load_config(self, fn):
        logger.info("%s[%s] loading config from %s", type(self), self, fn)
        return self.config(fn, replace=True)


def proxy(cfg):
    logger.debug("Creating proxy from %s", cfg)
    ncfg = copy.deepcopy(cfg)
    addr = ncfg.pop('addr')
    node = pizco.Proxy(addr)
    node.config(ncfg)
    logger.info("Proxy[%s] created for address %s: %s", node, addr, ncfg)
    return node
