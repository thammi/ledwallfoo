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

