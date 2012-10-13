###############################################################################
##
##  Copyright (C) 2011  Thammi
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################

import os
import socket
import time
import datetime
import math
from StringIO import StringIO

def const_loop(fun, tick):
    """Calls fun() with a constant interval of tick while it returns True"""

    while True:
        # schedule the next tick
        now = time.time()
        next_tick = now + tick - now % tick

        # do something
        res = fun()

        # stop on False
        if not res:
            break

        # wait until next tick
        wait = next_tick - time.time()
        if wait > 0:
            time.sleep(wait)

def cramp(value, floor, top):
    """Fits value between floor and top"""
    return min(max(value, floor), top)

def brightness_adjust():
    """Tries to guess a sane brightness adjustment to the time of day"""
    now = datetime.datetime.now()
    progress = now.hour * 60 + now.minute 
    curve = math.sin(progress * math.pi / 60 / 24)
    return cramp(0.5 +  curve / 2, 0.75, 1)

class LedMatrix:
    """Represents a connection to a led matrix"""

    size = (16,15)
    """The size of the led matrix"""

    def __init__(self, server=None, port=1338, lazy_resp=10):
        """Connect to the led matrix

        The address of the ledwall is:
            1. the parameter server
            2. the environment variable LEDWALL_IP
            3. localhost

        lazy_resp determines how many pending responses from the ledwall are
        acceptable until the send_command() call blocks.

        The priority might be changed according to the environment variable
        LEDWALL_PRIORITY if it is set.

        """
        if server == None:
            if 'LEDWALL_IP' in os.environ:
                server = os.environ['LEDWALL_IP']
            else:
                server = "ledwall"

        self.lazy_resp = lazy_resp
        self.hang_resp = 0

        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))

        if 'LEDWALL_PRIORITY' in os.environ:
            self.change_priority(int(os.environ['LEDWALL_PRIORITY']))

        opts = self.receive_options(1)
        print(opts)
        self.size = (opts['width'], opts['height'])

    def close(self):
        """Closes the connection to the led matrix"""
        self.sock.close()

    def receive_options(self, command, data=""):
        """Receive options from the led matrix."""
        sock = self.sock
        lazy_resp = self.lazy_resp

        sock.send("%02x" % command + data + "\r\n")

        self.hang_resp += 1

        buf = ""
        opts = {}

        while True:
            buf += sock.recv(256)

            while len(buf):
                split = buf.find('\r\n')

                if split == -1:
                    break

                line = buf[:split]
                buf = buf[split+2:]

                if self.hang_resp:
                    self.hang_resp -= 1
                elif len(line):
                    key, value = line.split('=')
                    opts[key] = value
                else:
                    return opts

    def send_command(self, command, data=""):
        """Sends the command to the led matrix."""
        sock = self.sock
        lazy_resp = self.lazy_resp

        sock.send("%02x" % command + data + "\r\n")

        self.hang_resp += 1

        while self.hang_resp > lazy_resp:
            lines = sock.recv(256).split('\r\n')
            self.hang_resp -= len(lines) - 1

    def send_raw_image(self, raw):
        """Writes a raw image on the led matrix.

        The image consists of $height lines of $width RGB pixels in a string
        like object containing binary data.

        """
        self.send_command(3, str(raw).encode("hex"))

    def send_pixel(self, (x, y), (r, g, b)):
        """Writes a singe pixel on the led matrix."""
        width, height = self.size
        msg_format = "%02x" * (2 + 3)

        self.send_command(2, msg_format % (x, y, r, g, b))

    def send_image(self, image):
        """Writes a Python Imaging Library on the led matrix."""
        buf = StringIO()
        data = image.getdata()

        for pixel in data:
            for color in pixel:
                buf.write(chr(color))

        self.send_raw_image(buf.getvalue())

    def send_clear(self):
        """Sets all pixels of the led matrix to black"""
        self.send_command(2, "00" * (2 + 3))

    def change_priority(self, priority):
        """Sets the priority of this connection.

        The led matrix always shows the buffer of the highest priority with an
        active connection. Operations in lower buffers will be executed but
        might not be visible as long as there are connections with a higher
        priority.

        The priority should be between 0 and 4. The default priority is 1.

        """
        self.send_command(4, "%02x" % priority)

    def record_start(self):
        """
        Starts recording of current stream
        """
        self.send_command(5)

    def record_stop(self):
        """
        Ends current recording session
        """
        self.send_command(6)
