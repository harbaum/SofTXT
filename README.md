# SoftXT

Simple pure software implementation of the upcoming fischertechnik
TXT-4.0 controller [Video](https://youtu.be/1ub4-ASsy-U).

These scripts implement the onlin ebehaviour of the TXT-4.0 and can be
run as a client against ROBO Pro Coding.

![Screenshot](screen.png)

Optional for physical IO a ftDuino running the [IOServer](https://github.com/harbaum/ftduino/tree/master/ftduino/libraries/WebUSB/examples/IoServer) sketch is supported.

## Howto

To use this simply run '''txt-4.0.py'''. This will start a web server that
listens on port 8000 and provides the web API that ROBO Pro Coding expects
to see. The server will store downloaded programs in the local
directory and run the '''run.py''' script whenever an app is supposed to
run. '''run.py''' and all other files are needed to execute downloaded
programs.

in order to access the SoftXT on from within a browser running on the
same PC simply enter '''localhost:8000''' as the IP address into the
"Controller verbinden" dialog of ROBO Pro Coding.
