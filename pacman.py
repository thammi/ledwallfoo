#!/usr/bin/env python

import math
import time

from ledwall import LedMatrix, const_loop

# WARNING: this code is _very_ hacky!!!

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
                            max_intensity = 0xaa
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

