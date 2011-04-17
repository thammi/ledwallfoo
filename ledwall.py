import os
import socket
import time
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
                server = "localhost"

        self.lazy_resp = lazy_resp
        self.hang_resp = 0

        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))

        if 'LEDWALL_PRIORITY' in os.environ:
            self.change_priority(int(os.environ['LEDWALL_PRIORITY']))

    def close(self):
        """Closes the connection to the led matrix"""
        self.sock.close()

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

        self.send_command(2, msg_format % (x+1, y+1, r, g, b))

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

