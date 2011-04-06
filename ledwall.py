import os
import socket
from StringIO import StringIO

class LedMatrix:

    size = (16,15)

    def __init__(self, server=None, port=1338):
        if server == None:
            if 'LEDWALL_IP' in os.environ:
                server = os.environ['LEDWALL_IP']
            else:
                server = "localhost"

        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))

    def send_command(self, command, data=""):
        self.sock.send("%02x" % command + data + "\r\n")

    def send_raw_image(self, raw):
        # quickfix to adjust to current orientation and a bug
        width, height = self.size
        out = StringIO()
        for x in reversed(range(width)):
            for y in reversed(range(height)):
                offset = (x + y * width) * 3
                out.write(raw[offset:offset+3])

        self.send_command(3, str(out.getvalue()).encode("hex"))

    def send_pixel(self, (x, y), (r, g, b)):
        # quickfix! the ledwall is positioned in the wrong direction
        width, height = self.size
        (x, y) = (width - x - 1, height - y - 1)
        msg_format = "%02x" * (2 + 3)

        self.send_command(2, msg_format % (x+1, y+1, r, g, b))

    def send_image(self, image):
        buf = StringIO()
        data = image.getdata()

        for pixel in data:
            for color in pixel:
                buf.write(chr(color))

        self.send_raw_image(buf.getvalue())

    def send_clear(self):
        self.send_command(2, "00" * (2 + 3))

