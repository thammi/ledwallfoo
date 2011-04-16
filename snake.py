#!/usr/bin/env python

import curses
import random
import time
import socket
import select

from ledwall import LedMatrix

class SnakeGame:

    def __init__(self, matrix):
        self.matrix = matrix
        self.size = matrix.size
        self.snake = []
        self.scr = None
        self.color = (0x00, 0x00, 0xaa)
        self.target = None

        self.address = ('<broadcast>', 38544)
        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def free_spot(self):
        width, height = self.size

        while True:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            pos = (x, y)

            if self.is_free(pos):
                return pos

    def is_free(self, pos):
        return pos not in self.snake

    def get_input(self):
        # TODO: this is madness
        scr = self.scr

        key = -1

        while True:
            new_key = scr.getch()

            if new_key == -1:
                break
            else:
                key = new_key

        return key

    def run(self):
        try:
            self.scr = scr = curses.initscr()

            scr.nodelay(1)
            scr.keypad(1)
            curses.noecho()

            self.loop()
        finally:
            curses.endwin()

        print "You lose!"

    def add_limb(self, pos):
        self.snake.append(pos)
        self.matrix.send_pixel(pos, self.color)

    def lose_limb(self):
        last = self.snake.pop(0)
        self.matrix.send_pixel(last, (0x00, 0x00, 0x00))

    def set_target(self, pos):
        self.target = pos
        self.matrix.send_pixel(pos, (0xff, 0xff, 0xff))

    def idle(self, duration):
        sock = self.sock
        address = self.address

        now = time.time()
        target = now - now % duration + duration

        while True:
            wait = target - time.time()

            if wait <= 0:
                break

            rlist, _, _ = select.select([sock], [], [], wait)

            if len(rlist):
                pass

    def loop(self):
        snake = self.snake
        width, height = self.size

        # start with one limb
        position = self.free_spot()
        self.add_limb(position)

        # add the target if neccessary
        if self.target == None:
            self.set_target(self.free_spot())

        # go north
        direction = (0, -1)

        # the key mappings
        key_map = {
                curses.KEY_UP: (0, -1),
                curses.KEY_DOWN: (0, 1),
                curses.KEY_RIGHT: (1, 0),
                curses.KEY_LEFT: (-1, 0),
                }

        while True:
            # where to go next?
            key = self.get_input()
            if key in key_map:
                direction = key_map[key]

            # moving
            dir_x, dir_y = direction
            pos_x, pos_y = position

            new_x = (dir_x + pos_x) % width
            new_y = (dir_y + pos_y) % height

            position = (new_x, new_y)

            # bump?
            if not self.is_free(position):
                break

            # let's grow
            self.add_limb(position)

            # eating?
            if position != self.target:
                # shrink
                self.lose_limb()
            else:
                # reposition target
                self.set_target(self.free_spot())

            # wait some time
            # TODO: constant framerate!
            self.idle(0.2)

        # shrink back
        while len(snake):
            self.lose_limb()
            time.sleep(0.05)

def main(args):
    matrix = LedMatrix()
    matrix.send_clear()

    game = SnakeGame(matrix)
    game.run()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])

