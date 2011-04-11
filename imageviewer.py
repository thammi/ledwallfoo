#!/usr/bin/env python

import sys
import Image, ImageDraw

from ledwall import LedMatrix

matrix = LedMatrix()

orig = Image.open(sys.argv[1])

target_res = matrix.size
scale = min(float(target) / old for old, target in zip(orig.size, target_res))
new_size = tuple(int(old * scale) for old in orig.size)

scaled = orig.resize(new_size, Image.ANTIALIAS)

top = tuple((target - new) / 2 for new, target in zip(new_size, target_res))

im = Image.new(mode="RGB", size=target_res)
im.paste(scaled, top)

matrix.send_image(im)

raw_input()

