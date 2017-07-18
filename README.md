ionode helps make an input/output device remotely controllable.

For example, you have a serially (rs232) contollable device connected to a computer.
You want this device to be controllable from multiple processes possibly running on one or more computers.
Using the ionode base class (ionode.IONode) you can create an IONode instance that will manage:

- connection to the serial device (connect, disconnect, connected)
- configuration of the device (config, config_changed, config_delta, load_config, save_config)
- remote access to the device over tcp or other connections (using zeromq and [pizco](https://github.com/hgrecco/pizco))

Additionally, ionodes can be controlled through a web browser by using ionode.ui to bring up a flask web server that 
exposes ionodes using websockets and a remote procedure call protocol [flask_wsrpc](https://github.com/braingram/flask_wsrpc).

See [examples](https://github.com/braingram/ionode/tree/master/examples) for a few examples.
