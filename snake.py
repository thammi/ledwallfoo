#!/usr/bin/env python

import curses
import random
import time
import socket
import select
import StringIO
import struct

from ledwall import LedMatrix

PORT = 38544

KEY_MAP = {
        (0, -1): [curses.KEY_UP, ord('w'), ord('k')],
        (0, 1): [curses.KEY_DOWN, ord('s'), ord('j')],
        (-1, 0): [curses.KEY_LEFT, ord('a'), ord('h')],
        (1, 0): [curses.KEY_RIGHT, ord('d'), ord('l')],
        }

class SnakeGame:

    def __init__(self, matrix, buffer_input=True, preferred_color=None):
        self.matrix = matrix
        self.size = matrix.size
        self.buffer_input = buffer_input
        self.preferred_color = preferred_color

        self.scr = None

        self.player = None
        self.color = None

        self.target = None
        self.target_ticks = 0

        self.snake = []
        self.others = {}

        self.create_colors()

        # initialize the socket
        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', PORT))

    def create_colors(self):
        self.colors = colors = []

        for i in range(6):
            color = (0xff if (i >= 3) != (i % 4 == x) else 0x00 for x in range(3))
            colors.append(tuple(color))

    def free_spot(self):
        width, height = self.size

        while True:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            pos = (x, y)

            if self.is_free(pos):
                return pos

    def is_free(self, pos):
        # eating ourselves
        if pos in self.snake:
            return False

        # bumbing against other players
        for snake in self.others.values():
            if pos in snake:
                return False

        return True

    def get_input(self):
        if self.buffer_input:
            return self.scr.getch()
        else:
            # TODO: this is madness
            scr = self.scr

            key = -1

            # we are interested in the last keystroke
            while True:
                new_key = scr.getch()

                if new_key == -1:
                    break
                else:
                    key = new_key

            return key

    def run(self):
        try:
            # initialize curses environment
            self.scr = scr = curses.initscr()

            scr.nodelay(1)
            scr.keypad(1)
            curses.noecho()

            # starting the actual loop
            self.loop()
        finally:
            # sanitizing the tty again
            curses.endwin()

            # vanish from ledmatrix and network
            snake = self.snake
            if snake:
                while snake:
                    self.lose_limb()
                self.send()

        print "You lose!"

    def add_limb(self, pos):
        self.snake.append(pos)
        self.matrix.send_pixel(pos, self.color)

    def lose_limb(self):
        last = self.snake.pop(0)
        self.matrix.send_pixel(last, (0x00, 0x00, 0x00))

    def set_target(self, pos):
        self.target = pos
        self.target_ticks += 1
        self.matrix.send_pixel(pos, (0xff, 0xff, 0xff))

    def idle(self, duration):
        sock = self.sock

        # when to stop?
        target = time.time() + duration

        while True:
            # how long?
            wait = target - time.time()

            # waiting is over?
            if wait <= 0:
                break

            # input or timeout
            rlist, _, _ = select.select([sock], [], [], wait)

            if len(rlist):
                self.receive()

    def send(self):
        # broadcasting
        address = ('<broadcast>', PORT)

        # construct snake position message
        io = StringIO.StringIO()

        io.write('S')
        io.write(chr(self.player))

        for point in self.snake:
            for coord in point:
                io.write(chr(coord))

        msg = io.getvalue()
        self.sock.sendto(msg, address)

        # send target propagation message
        target = self.target
        if target:
            target_ticks = self.target_ticks
            msg = 'T' + struct.pack('ibb', target_ticks, target[0], target[1])
            self.sock.sendto(msg, address)

    def receive(self):
        buf, address = self.sock.recvfrom(2048)

        cmd = buf[0]
        payload = buf[1:]

        if cmd == 'S':
            # snake position message
            player = ord(payload[0])
            raw_points = map(ord, payload[1:])

            self.others[player] = [tuple(raw_points[i:i+2]) for i in range(0, len(raw_points), 2)]
        elif cmd == 'T':
            # target propagation message
            ticks, target_x, target_y = struct.unpack('ibb', payload)

            # TODO: target update collision handling/detection
            # only update if newer
            if ticks > self.target_ticks:
                self.target = (target_x, target_y)
                self.target_ticks = ticks

    def loop(self):
        snake = self.snake
        others = self.others
        width, height = self.size

        # wait for incoming traffic
        self.idle(0.5)

        # pick a free player id
        player_is_free = lambda x: x not in others.keys()
        free_player = filter(player_is_free, range(len(self.colors)))
        self.player = player = min(free_player)

        # get a color
        self.color = self.colors[player]

        # start with one limb
        position = self.free_spot()
        self.add_limb(position)
        self.send()

        # are we the first?
        if self.target == None:
            # clean up
            self.matrix.send_clear()

            # set initial target
            self.set_target(self.free_spot())

        # go north
        direction = (0, -1)

        # creating key mappings
        key_map = {}
        for direction, keys in KEY_MAP.iteritems():
            for key in keys:
                key_map[key] = direction

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

            self.send()

            # wait some time
            tick = 0.2
            now = time.time()
            wait = tick - now % tick
            if wait > 0:
                self.idle(wait)

        # shrink back
        while len(snake):
            self.lose_limb()
            self.send()
            time.sleep(0.05)

def main(args):
    matrix = LedMatrix()

    game = SnakeGame(matrix)
    game.run()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])

