#!/usr/bin/env python

import sys
import time

import Image
import ImageDraw
import ImageFont

from ledwall import LedMatrix

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

