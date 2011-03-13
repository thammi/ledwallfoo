#!/usr/bin/env python

import sys
import socket
import time

import Image
import ImageDraw
import ImageFont

class LedMatrix:

    size = (16,15)

    def __init__(self, server="localhost", port=1338):
        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))

    def send_image(self, image):
        size = self.size
        sock = self.sock

        msg_format = "%02i" * 2 + "%03i" * 3 + "\n"

        for index, pixel in enumerate(image.getdata()):
            # 1-based index?
            x = index % size[0] + 1
            y = index / size[0] + 1

            sock.send(msg_format % ((x, y) + pixel))

class ColorFader:

    def __init__(self, colors, fade_steps=40):
        self.colors = colors
        self.fade_steps = fade_steps
        self.pos = (0, 0)

    def step(self):
        fade_steps = self.fade_steps
        pos = self.pos

        minor = (pos[1] + 1) % fade_steps

        if minor == 0:
            major = (pos[0] + 1) % len(self.colors)
        else:
            major = pos[0]

        self.pos = (major, minor)

    def color(self):
        colors = self.colors
        pos = self.pos
        fade_steps = float(self.fade_steps)

        start = colors[pos[0]]
        target = colors[(pos[0] + 1) % len(colors)]

        color = tuple(a + (b - a) / fade_steps * pos[1] for a, b in zip(start, target))

        return ("#" + "%02x" * 3) % color

matrix = LedMatrix()

im = Image.new(mode="RGB", size=matrix.size)
clean_data = list(im.getdata())

draw = ImageDraw.Draw(im)

font = ImageFont.truetype("DejaVuSans.ttf", matrix.size[1])
draw.setfont(font)

text = "<<</>>" if len(sys.argv) < 2 else sys.argv[1]

image_width = matrix.size[0]
text_width = draw.textsize(text)[0]

width = text_width + image_width

step = 0

colors = [(0xff, 0x00, 0x00), (0x00, 0xff, 0x00), (0x00, 0x00, 0xff)]
fader = ColorFader(colors)

while True:
    draw.text((image_width - step, 0), text, fill=fader.color())
    matrix.send_image(im)

    step = (step + 1) % width

    fader.step()

    im.putdata(clean_data)
    time.sleep(0.2)

