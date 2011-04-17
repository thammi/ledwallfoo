import os
import socket
import time
from StringIO import StringIO

def const_loop(fun, tick):
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

    size = (16,15)

    def __init__(self, server=None, port=1338, lazy_resp=10):
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
        self.sock.close()

    def send_command(self, command, data=""):
        sock = self.sock
        lazy_resp = self.lazy_resp

        sock.send("%02x" % command + data + "\r\n")

        self.hang_resp += 1

        while self.hang_resp > lazy_resp:
            lines = sock.recv(256).split('\r\n')
            self.hang_resp -= len(lines) - 1

    def send_raw_image(self, raw):
        self.send_command(3, str(raw).encode("hex"))

    def send_pixel(self, (x, y), (r, g, b)):
        width, height = self.size
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

    def change_priority(self, priority):
        self.send_command(4, "%02x" % priority)

