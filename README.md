# ledwallfoo

## About

This repository contains a small python library to interact with the
[pentawall](https://github.com/sebseb7/pentawall). It additionally contains
several small applications using this library.

You can use the [Simulator](https://github.com/carwe/pentawallsim) if you don't
have a pentawall handy.

## ledwall.py

This is the library. It contains the following features:

* send\_pixel(): Set a single pixel to the specified RGB value
* send\_image(): Sends a Python Imaging Library image to the wall
* send\_raw\_image(): Send a raw image consisting of $height lines of $width
  RGB pixels. The data is supposed to be a string(-like) object containing
  binary data.
* send\_clear(): Resets the whole screen to black
* change\_priority(): Changes the priority of the connection. Default is 1 and
  higher priority connections paint over lower priority connections.

The address of the server can be passed to the Object in its constructor, is
copied from the environment variable LEDWALL\_IP or defaults to 'localhost'.

Most quirks of the pentawall protocol will be hidden from the user. Coordinates
start at 0x0 and the library rotates the image to fit the current orientation.

## Configuration

You should specify the IP address of the pentawall in the environment variable
`LEDWALL_IP`. If you are at the c3d2 HQ type the following line into your POSIX
compatible shell:

    export LEDWALL_IP=172.22.99.6

If the environment variable `LEDWALL_PRIORITY` is set the specified priority
will be set at the initialization of the matrix.

## Applications

### Game of Life

Conways Game of Life wrapped to fit the screen. Start it with:

    ./gol.py $SEED

$SEED is the initial configuration file. Some seeds are in `gol_seeds/`.

### Pacman

A pacman eating the previos content of the ledwall

    ./pacman.py

### Fading Text

A scrolling text with fading colors

    ./fade_text.py "My text"

### Image Viewer

A simple image viewer scaling the image down keeping the aspect ratio without
cropping:

    ./imageviewer.py $IMAGE

### Snake

A snake game with built-in chaotic massive multiplayer experience. To start the
game simply run:

    ./snake.py

You can add `-p [0-5]` to prefer a player id and its color. A random free
player id will be assigned to you if you did not specify an id or it was
already taken.

With `--direct` or `-d` you deactivate input buffering which is more direct and
might be more suitable for you.

You will automatically play together with everybody else playing in your
subnet. Every player should use the same output device as each client only
paints the output of the corresponding player.

The network protocol is based on pure chaos and might have many bugs. Feel free
to report any undetected collisions and duplicate targets.

