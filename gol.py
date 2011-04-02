import sys
import time

from ledwall import LedMatrix

class GameOfLife:

    def __init__(self, matrix):
        self.matrix = matrix
        self.size = matrix.size

        self.new_field()

    def new_field(self):
        size = self.size
        self.field = [[False]*size[0] for i in range(size[0])]

    def load(self, file_name):
        data = open(file_name).readlines()

        for y, line in enumerate(data):
            print line
            for x, char in enumerate(line):
                if char == '#':
                    self.create(x, y)

    def create(self, x, y):
        print "create: %02i %02i" % (x,y)
        self.field[x][y] = True
        self.matrix.send_pixel((x, y), (0x00, 0x00, 0xff))

    def die(self, x, y):
        print "die: %02i %02i" % (x,y)
        self.field[x][y] = False
        self.matrix.send_pixel((x, y), (0x00, 0x00, 0x00))

    def survive(self, x, y):
        self.field[x][y] = True

    def step(self):
        width, height = self.size

        old_field = self.field
        self.new_field()

        for x in range(width):
            for y in range(height):
                # get proximity
                prox = 0
                for n in range(x-1, x+2):
                    for m in range(y-1, y+2):
                        if old_field[n%width][m%height]:
                            prox += 1

                if old_field[x][y]:
                    prox -= 1
                    if prox < 2:
                        print "lonely ", prox
                        self.die(x, y)
                    elif prox > 3:
                        print "crowded ", prox
                        self.die(x, y)
                    else:
                        self.survive(x, y)
                elif prox == 3:
                    self.create(x, y)

matrix = LedMatrix()
game = GameOfLife(matrix)
game.load(sys.argv[1])

while True:
    game.step()
    time.sleep(0.1)
    print "step"

