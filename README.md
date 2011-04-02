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
* send\_image(): Sends a Python Imaging Library image to the wall. *Warning:*
  This method currently sends single pixels
* send\_clear(): Resets the whole screen to black

The address of the server can be passed to the Object in its constructor, is
copied from the environment variable LEDWALL\_IP or defaults to 'localhost'.

Most quirks of the pentawall protocol will be hidden from the user. Coordinates
start at 0x0 and the library rotates the image to fit the current orientation.

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

