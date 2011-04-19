#!/usr/bin/env python
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

import time

import os
import Image
import ImageDraw
import ImageFont

from ledwall import LedMatrix, const_loop

DEF_COLORS = [(0xff, 0x00, 0x00), (0x00, 0xff, 0x00), (0x00, 0x00, 0xff)]
DEF_FONT = "DejaVuSans.ttf"

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

class FadingText:

    def __init__(self, matrix, text, fade_steps=40, font=DEF_FONT, colors=DEF_COLORS):
        self.matrix = matrix
        self.text = text

        self.progress = 0

        self.im = im = Image.new(mode="RGB", size=matrix.size)
        self.clean_data = list(im.getdata())

        self.draw = draw = ImageDraw.Draw(im)

        im_font = ImageFont.truetype("DejaVuSans.ttf", matrix.size[1])
        draw.setfont(im_font)

        image_width = matrix.size[0]
        text_width = draw.textsize(text)[0]

        self.width = text_width + image_width

        self.fader = ColorFader(colors, fade_steps)

    def step(self):
        matrix = self.matrix
        text = self.text
        progress = self.progress
        fader = self.fader
        im = self.im

        image_width = matrix.size[0]

        # draw and send
        self.draw.text((image_width - progress, 0), text, fill=fader.color())
        matrix.send_image(im)

        self.progress = (progress + 1) % self.width
        self.fader.step()

        im.putdata(self.clean_data)

        return True

    def endless(self, snooze=0.1):
        const_loop(self.step, snooze)

    def scroll(self, rounds=1, snooze=0.1):
        for _ in range(rounds):
            self.step()
            time.sleep(snooze)

def main(args):
    from optparse import OptionParser

    optp = OptionParser()

    optp.add_option("-s", "--fade_steps",
            help="Set preferred number of fade-steps",
            metavar="FADE_STEPS",
            type="int",
            default=40)
            
    optp.add_option("--priority",
            help="Change priority, default is 2",
            metavar="PRIORITY",
            type="int",
            default=2)

    (options, args) = optp.parse_args()

    matrix = LedMatrix()
    matrix.change_priority(options.priority)

    if len(args) < 1:
        text = "<<</>>"
    else:
        text = u' '.join(arg.decode("utf-8") for arg in args)

    try:
        FadingText(matrix, text, options.fade_steps).endless()
    finally:
        matrix.close()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])

