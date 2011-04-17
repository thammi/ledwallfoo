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

import math
import time

from ledwall import LedMatrix, const_loop, brightness_adjust

# WARNING: this code is _very_ hacky!!!

BRIGHT = int(brightness_adjust() * 0xff)

class Pacman:

    def __init__(self, matrix):
        self.matrix = matrix

        width, height = matrix.size
        self.field = [False] * (width * height)

        self.size = size = height + 1
        self.pos = -size

    def step(self):
        pos = self.pos
        field = self.field
        size = self.size
        matrix = self.matrix

        width, height = matrix.size

        threshold = (size / 2.0) ** 2
        middlepos = pos + size / 2.0

        for x in range(width):
            for y in range(height):
                painted = False

                a = x - middlepos
                b = y - height / 2.0

                sq_dist = a**2 + b**2

                field_pos = x+y*width

                if sq_dist < threshold:
                    dist = math.sqrt(sq_dist)

                    # hacky mouth animation progress
                    mouth = (0, 0.4)[pos%2]

                    deg = math.asin(abs(b/dist))

                    # not painting the eye
                    if not 0.8 < deg < 1.2 or not (0.55 < dist / size * 2 < 0.75 and b < 0 and a > 0):
                        # not painting the mouth
                        if deg > mouth or a < 0:
                            # not clearing later
                            painted = True

                            # edge fading
                            max_intensity = BRIGHT
                            rad = size / 2.0
                            intensity = math.sqrt((rad - dist) / rad) * 2 * max_intensity
                            intensity = min(intensity, max_intensity)

                            # not sending if pixel already at that state
                            if field[field_pos] != intensity:
                                # marking pixel as dirty
                                field[field_pos] = intensity

                                # finally painting
                                matrix.send_pixel((x,y), (intensity, intensity, 0x00))

                if not painted and field[field_pos]:
                    # clear formerly painted and no longer used pixels
                    field[field_pos] = False
                    matrix.send_pixel((x,y), (0x00, 0x00, 0x00))

        # move forward
        self.pos += 1

        # are we finished?
        return pos < width

matrix = LedMatrix()
pacman = Pacman(matrix)

try:
    const_loop(pacman.step, 0.2)
finally:
    matrix.close()

