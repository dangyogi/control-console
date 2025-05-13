# control-console

Raspberry Pi hardware control console using raw touch/draw devices.

This is trying to provide a software solution to build control consoles for hardware projects.

It's designed to run on a Raspberrypi 64-bit without desktop.  Currently running on rasp pi OS 12 on a
rasp pi 3 model B+.

It's designed to let you draw simple control widgets directly to the screen that are touch controlled.
Currently being run with a 10-touch monitor.  Multiple touch inputs are designed to be routed to
multiple widgets, rather than controlling a single widget (e.g., pinch).

The idea is to simulate slider pots, buttons, switches, etc, and to allow the software to reconfigure
these on the fly.

It has no concept of windows (overlapping or not), and does not run under a GUI manager.
