#!/usr/bin/env python

import os
import socket

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

    def send_image(self, image):
        size = self.size
        sock = self.sock

        msg_format = "02" + "%02x" * 2 + "%02x" * 3 + "\r\n"

        for index, pixel in enumerate(image.getdata()):
            # 1-based index?
            x = index % size[0] + 1
            y = index / size[0] + 1

            sock.send(msg_format % ((x, y) + pixel))

