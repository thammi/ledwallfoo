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

import curses
import random
import time
import socket
import select
import StringIO
import struct

from ledwall import LedMatrix, brightness_adjust

PORT = 38544

BRIGHT = int(brightness_adjust() * 0xff)

KEY_MAP = {
        (0, -1): [curses.KEY_UP, ord('w'), ord('k')],
        (0, 1): [curses.KEY_DOWN, ord('s'), ord('j')],
        (-1, 0): [curses.KEY_LEFT, ord('a'), ord('h')],
        (1, 0): [curses.KEY_RIGHT, ord('d'), ord('l')],
        }

TICK = 0.2

class AppleFx:

    def __init__(self, game):
        self.matrix = matrix = game.matrix
        self.snake = snake = game.snake
        self.color = color = game.color

        get_limb = lambda n: snake[-n-1] if n < len(snake) else None
        self.get_limb = get_limb

        bright = tuple(min(c + BRIGHT * 0.5, BRIGHT) for c in color)
        self.bright = bright

        self.pos = pos = 0
        self.cur = cur = self.get_limb(pos)

        # highlight the first limb
        matrix.send_pixel(cur, bright)

    def step(self):
        snake = self.snake
        matrix = self.matrix
        color = self.color
        bright = self.bright

        get_limb = self.get_limb

        pos = self.pos
        cur = self.cur


        # reset previous to normal color
        if self.cur in snake:
            matrix.send_pixel(cur, color)

        # check whether the snake moved
        if cur != get_limb(pos):
            pos += 1

        # move the highlight
        pos += 1
        cur = get_limb(pos)

        # update the values
        self.pos = pos
        self.cur = cur

        # are we at the end?
        if cur:
            # highlight the limb
            matrix.send_pixel(cur, bright)

            return True
        else:
            return False

class SnakeGame:

    def __init__(self, matrix, buffer_input=True, preferred_player=None):
        self.matrix = matrix
        self.size = matrix.size
        self.buffer_input = buffer_input
        self.preferred_player = preferred_player

        self.scr = None

        self.player = None
        self.color = None

        self.target = None
        self.target_ticks = 0

        self.animations = []

        self.snake = []
        self.others = {}

        self.create_colors()

        # initialize the socket
        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', PORT))

    def create_colors(self):
        self.colors = colors = []

        for i in range(3):
            color = (BRIGHT * 0.8 if i == x else 0x00 for x in range(3))
            colors.append(tuple(color))

        for i in range(3):
            color = (BRIGHT * 0.8 if i != x else 0x00 for x in range(3))
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

            self.sock.close()

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
        self.matrix.send_pixel(pos, (BRIGHT,) * 3)

    def assure_target(self):
        surrounding = lambda i: range(i - 1, i + 2)
        target_x, target_y = self.target

        # check whether repaint is safe
        for x in surrounding(target_x):
            for y in surrounding(target_y):
                if not self.is_free((x, y)):
                    break
        else:
            # actual repaint
            self.matrix.send_pixel(self.target, (BRIGHT,)*3)

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

    def idle_tick(self, tick):
        now = time.time()
        wait = tick - now % tick
        if wait > 0:
            self.idle(wait)

    def animate(self):
        animations = self.animations

        del_list = []

        for index, animation in enumerate(animations):
            # activate animation
            res = animation.step()

            # list for deletion if False returned
            if not res:
                del_list.append(index)

        # delete
        for index in reversed(del_list):
            del animations[index]

    def send(self):
        # broadcasting
        address = ('<broadcast>', PORT)

        # construct the message
        io = StringIO.StringIO()

        # adding magic number
        io.write('S')

        # adding player info
        io.write(chr(self.player))

        # adding target information
        target = self.target
        if target:
            target_ticks = self.target_ticks
            io.write(struct.pack('ibb', target_ticks, target[0], target[1]))
        else:
            io.write('\0' * 6)

        # adding taken space
        for point in self.snake:
            for coord in point:
                io.write(chr(coord))

        # send it out
        self.sock.sendto(io.getvalue(), address)

    def receive(self):
        buf, address = self.sock.recvfrom(2048)

        cmd = buf[0]

        if cmd == 'S':
            # split up message
            player_part = buf[1]
            target_part = buf[2:8]
            space_part = buf[8:]

            # snake position message
            player = ord(player_part)

            # target propagation message
            ticks, target_x, target_y = struct.unpack('ibb', target_part)

            # TODO: target update collision handling/detection
            # only update if newer
            if ticks > self.target_ticks:
                self.target = (target_x, target_y)
                self.target_ticks = ticks

            raw_points = map(ord, space_part)
            slices = range(0, len(raw_points), 2)
            self.others[player] = [tuple(raw_points[i:i+2]) for i in slices]

    def loop(self):
        snake = self.snake
        others = self.others
        animations = self.animations
        preferred_player = self.preferred_player
        width, height = self.size

        half_tick = TICK / 2

        # wait for incoming traffic
        self.idle(0.5)

        # pick a free player id ...
        player_is_free = lambda x: x not in others.keys()

        # check whether preferred player is available
        if preferred_player != None:
            if player_is_free(preferred_player):
                self.player = preferred_player

        # pick random player if none chosen yet
        if self.player == None:
            free_player = filter(player_is_free, range(len(self.colors)))
            self.player = random.choice(free_player)

        # pick a color
        self.color = self.colors[self.player]

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

                # start the special effects
                sfx = AppleFx(self)
                animations.append(sfx)

            # repaint target from time to time
            if random.randint(0, 10) == 0:
                self.assure_target()

            self.send()

            # wait some time
            self.idle_tick(half_tick)
            self.animate()

            self.idle_tick(half_tick)
            self.animate()

        # shrink back
        quarter_tick = TICK / 4
        parity = False
        while len(snake):
            self.lose_limb()
            self.send()

            if parity:
                self.animate()

            parity = not parity

            time.sleep(quarter_tick)

def main(args):
    from optparse import OptionParser

    optp = OptionParser()

    optp.add_option("-p", "--player",
            help="Set preferred player (0-5)",
            metavar="PLAYER",
            type="int",
            default=None)

    optp.add_option("-d", "--direct-input",
            help="Get more direct input",
            action="store_false",
            default=True)

    optp.add_option("--priority",
            help="Change priority, default is 2",
            metavar="PRIORITY",
            type="int",
            default=2)

    (options, args) = optp.parse_args()

    matrix = LedMatrix(args[0] if args else None)

    try:
        matrix.change_priority(options.priority)

        game = SnakeGame(matrix, options.direct_input, options.player)
        game.run()
    finally:
        matrix.close()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])

