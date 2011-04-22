#!/usr/bin/env python
# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# sinkelement.py
# (c) 2005 Edward Hervey <edward@fluendo.com>
# Licensed under LGPL
#
# Small test application to show how to write a sink element
# in 20 lines in python
#
# Run this script with GST_DEBUG=python:5 to see the debug
# messages

from ledwall import LedMatrix

import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('file', metavar='FILE', type=str, nargs='+',
                   help='filename to play')
parser.add_argument('--server', dest="server", type=str,
                   default='127.0.0.1',
                   help='server ip address')
parser.add_argument('--vis', dest='visualize', #action='store_const',
                   default="libvisual_bumpscope",
                   help='use gstreamer visualize plugin')
parser

args = parser.parse_args()

if not args:
    print parser.usage()

import time
import pygst
pygst.require('0.10')
import gst

import gobject
import sys
gobject.threads_init ()

#
# Simple Sink element created entirely in python
#

def log(*args):
    print "\n".join(args)



class LedVideoSink(gst.BaseSink):

    __gsttemplates__ = (
          gst.PadTemplate ("sink",
                            gst.PAD_SINK,
                            gst.PAD_ALWAYS,
                            gst.caps_from_string("video/x-raw-rgb,width=16,height=15,bpp=24,framerate=23/1")
                          ),
     )

    sinkpad = property(lambda self: self.get_pad("sink"))

    def __init__(self, matrix):
        gst.BaseSink.__init__(self)
        self.matrix = matrix
        self.set_sync(True)

        gst.info('setting chain/event functions')
        self.sinkpad.set_event_function(self.eventfunc)

    def do_render(self, buffer):
        self.matrix.send_raw_image(buffer)
        return gst.FLOW_OK

    def eventfunc(self, pad, event):
        self.info("%s event:%r" % (pad, event.type))
        return True

gobject.type_register(LedVideoSink)

class LedPipe:
  def __init__(self, location, matrix, visualize=None, mainloop=None):
    # The pipeline

    self.visualize = visualize

    self.pipeline = gst.Pipeline()
    self.pipeline.auto_clock()

    # Create bus and connect several handlers
    self.bus = self.pipeline.get_bus()
    self.bus.add_signal_watch()
    self.bus.connect('message::eos', self.on_eos)
    self.bus.connect('message::tag', self.on_tag)
    self.bus.connect('message::error', self.on_error)

    # Create elements
    self.src = gst.element_factory_make('filesrc')
    self.player = player = gst.element_factory_make('playbin2')
    self.player.set_property("volume", 2)
    self.player.set_property("flags", 0x00000001 | 0x00000002 | 0x00000008 | 0x00000010 | 0x00000200)

    self.sink = gst.Bin() #gst.element_factory_make('alsasink')
    self.led = LedVideoSink(matrix) #gst.element_factory_make('alsasink')
    self.color = gst.element_factory_make('ffmpegcolorspace')
    self.rate = gst.element_factory_make('videorate')
    self.scale = gst.element_factory_make('ffvideoscale')
    self.scale.set_property("method", 5)

    self.sink.add(self.color, self.rate, self.scale, self.led)
    ghostpad = gst.GhostPad("sink", self.color.get_pad("sink"))
    self.sink.add_pad(ghostpad)
    gst.element_link_many(self.color, self.rate, self.scale, self.led)
    if self.visualize:    
        self.vis = gst.element_factory_make(self.visualize)
        player.set_property("vis-plugin", self.vis)

    player.set_property("video-sink", self.sink)
    player.connect("about-to-finish", self.on_finish)

    # Set 'location' property on filesrc
    player.set_property('uri', gst.uri_is_valid(location) and location or "file://" + location)

    # Connect handler for 'new-decoded-pad' signal 
    #self.dec.connect('new-decoded-pad', self.on_new_decoded_pad)

    # Add elements to pipeline
    self.pipeline.add(player)

    # The MainLoop
    self.mainloop = mainloop or gobject.MainLoop()

    # And off we go!
    self.pipeline.set_state(gst.STATE_PLAYING)

  def quit(self):
    self.pipeline.set_state(gst.STATE_NULL)


  def on_finish(self, unused):
    self.mainloop.quit()

  def on_eos(self, bus, msg):
    log('on_eos')
    self.mainloop.quit()

  def on_tag(self, bus, msg):
    taglist = msg.parse_tag()
    log('on_tag:')
    for key in taglist.keys():
      log('\t%s = %s' % (key, taglist[key]))

  def on_error(self, bus, msg):
    error = msg.parse_error()
    log('on_error: %s' %error[1])
    self.mainloop.quit()

#
# Code to test the MySink class
#
matrix = LedMatrix(server=args.server)
#matrix = LedMatrix(server="127.0.0.1")

pipe = LedPipe(args.file[0], matrix, visualize=args.visualize)

import glib, sys, os, fcntl


class ProgressBar:
    def __init__(self, min_value = 0, max_value = 100, width=77,**kwargs):
        self.char = kwargs.get('char', '#')
        self.mode = kwargs.get('mode', 'dynamic') # fixed or dynamic
        if not self.mode in ['fixed', 'dynamic']:
            self.mode = 'fixed'
 
        self.bar = ''
        self.min = min_value
        self.max = max_value
        self.span = max_value - min_value
        self.width = width
        self.amount = 0       # When amount == max, we are 100% done 
        self.update_amount(0) 
 
 
    def increment_amount(self, add_amount = 1):
        """
        Increment self.amount by 'add_ammount' or default to incrementing
        by 1, and then rebuild the bar string. 
        """
        new_amount = self.amount + add_amount
        if new_amount < self.min: new_amount = self.min
        if new_amount > self.max: new_amount = self.max
        self.amount = new_amount
        self.build_bar()
 
 
    def update_amount(self, new_amount = None):
        """
        Update self.amount with 'new_amount', and then rebuild the bar 
        string.
        """
        if not new_amount: new_amount = self.amount
        if new_amount < self.min: new_amount = self.min
        if new_amount > self.max: new_amount = self.max
        self.amount = new_amount
        self.build_bar()
 
 
    def build_bar(self):
        """
        Figure new percent complete, and rebuild the bar string base on 
        self.amount.
        """
        diff = float(self.amount - self.min)
        percent_done = int(round((diff / float(self.span)) * 100.0))
 
        # figure the proper number of 'character' make up the bar 
        all_full = self.width - 2
        num_hashes = int(round((percent_done * all_full) / 100))
 
        if self.mode == 'dynamic':
            # build a progress bar with self.char (to create a dynamic bar
            # where the percent string moves along with the bar progress.
            self.bar = self.char * num_hashes
        else:
            # build a progress bar with self.char and spaces (to create a 
            # fixe bar (the percent string doesn't move)
            self.bar = self.char * num_hashes + ' ' * (all_full-num_hashes)
 
        percent_str = str(percent_done) + "%"
        self.bar = '[ ' + self.bar + ' ] ' + percent_str + "  [%s/%s]"  %((self.amount/gst.SECOND),(self.max/gst.SECOND))
 
 
    def __str__(self):
        return str(self.bar)

prog = ProgressBar(0, 100, 0, mode='fixed')

def update_scrollbar():
    prog = globals().get("prog", None)
    try:
       dur = pipe.player.query_duration(gst.FORMAT_TIME)[0]/(1000*1000)
       cur = pipe.player.query_position(gst.FORMAT_TIME)[0]/(1000*1000)
       if prog and prog.max != dur:
          prog = ProgressBar(0, dur, 77, mode='fixed')
       prog.max = dur
       prog.update_amount(cur)
    except gst.QueryError, e:
       print e
       prog.max = 100
       prog.update_amount(0)

    print prog, "\r",
    sys.stdout.flush()

    return True

import sys, tty, termios

class IODriver(object):
    def __init__(self, line_callback=None, key_callback=None):
        self.buffer = ''
        self.line_callback = line_callback
        self.key_callback = key_callback
        flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
        flags |= os.O_NONBLOCK # | os.O_NDELAY
        fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flags)
        fd = sys.stdin.fileno()
        #tty.setraw(sys.stdin.fileno())
        #old_settings = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~termios.ECHO & ~termios.ICANON
        #new[6][termios.VMIN] = 1
        #new[6][termios.VTIME] = 0
        #termios.tcsetattr(fd, termios.TCSADRAIN, new)
        termios.tcsetattr(fd, termios.TCSANOW, new)
        glib.io_add_watch(sys.stdin, glib.IO_IN, self.io_callback)

    def io_callback(self, fd, condition):
        chunk = fd.read()
        log( "got %s" %repr(chunk))
        if self.key_callback:
            self.key_callback(chunk)
        for char in chunk:
            self.buffer += char
            if char == '\n':
                if self.line_callback:
                    self.line_callback(self.buffer)
                self.buffer = ''

        return True

def usage():
    log("############## Shortcuts ##############")
    log("< >   seek")
    log("q     quit")
    log("R S   record/stop")
    log("v     switch visualization")
    log("#######################################")

SEEKS = {
  '\x1b[D': -5,
  '\x1b[C': 5,
  # shift key
  '\x1b[1;2C': 30,
  '\x1b[1;2D': -30,
  # ctrl key
  '\x1b[1;5C': 300,
  '\x1b[1;5D': -300,
}


def key_entered(key):
    k = key.strip()
    if k == "q":
       pipe.mainloop.quit()
    elif k in SEEKS:
       # seek backwards
       if not pipe.player.get_state():
          return
       try:
          cur = pipe.player.query_position(gst.FORMAT_TIME)[0]
          print(cur, cur + (SEEKS[k] * gst.SECOND))
          #pipe.pipeline.set_state(gst.STATE_PAUSED)
          if not pipe.player.seek_simple(gst.FORMAT_TIME,
                                  gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT,
                                  max(cur + (SEEKS[k] * gst.SECOND), 0)):
             log("seek failed")
          pipe.pipeline.set_state(gst.STATE_PLAYING)
          pipe.player.get_state(-1)
          #pipe.pipeline.set_state(gst.STATE_PLAYING)
       except gst.QueryError, e:
          log(e)
       update_scrollbar()
    elif k == "R":
       matrix.record_start()
    elif k == "S":
       matrix.record_stop() 
    elif k == "v":
       #FIXME
       pass
    else:
        log("You have typed: %s" %k)



d = IODriver(key_callback=key_entered)

glib.timeout_add(500, update_scrollbar)

usage()
pipe.mainloop.run()

#
#
# class IODriver(object):
#     def __init__(self, line_callback=None, key_callback=None):
#         self.buffer = ''
#         self.line_callback = line_callback
#         self.key_callback = key_callback
#         flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
#         flags |= os.O_NONBLOCK | os.O_NDELAY
#         fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flags)
#         glib.io_add_watch(sys.stdin, glib.IO_IN, self.io_callback)
#
#     def io_callback(self, fd, condition):
#         chunk = fd.read()
#         if self.key_callback:
#             self.key_callback(chunk)
#         for char in chunk:
#             self.buffer += char
#             if char == '\n':
#                 if self.line_callback:
#                     self.line_callback(self.buffer)
#                 self.buffer = ''
#
#         return True
#
# def line_entered(line):
#     print "You have typed:", line.strip()
#
# d = IODriver(key_callback=line_entered)
# def update_scrollbar():
#     try:
#        log(str(pipe.player.query_position())) 
#        prog_bar.current = pipe.player.query_position()
#        prog_bar.done = pipe.player.query_duration()
#     except gst.QueryError, e:
#        prog_bar.current = 0
#        prog_bar.done = 1
#
#     log("jo")
#
#     return True

if False:

    import urwid
    import urwid.raw_display


    ufile = urwid.Text("test", align='left')


    screen = urwid.raw_display.Screen()
    header = urwid.AttrWrap(urwid.Text("pentavideo"), 'header')

    blank = urwid.Divider()
    prog_bar = urwid.ProgressBar('pg normal', 'pg complete', 0, 1, 'pg smooth')
    log_text = urwid.Text("BLA")

    def log(*args):
        log_text.set_text(log_text.text + "\n".join([str(x) for x in args]))

    listbox_content = [
        blank,
        log_text,
        urwid.Padding(urwid.Text("hi there"), ('fixed left',2), 
            ('fixed right',2), 20),    
        blank,
        prog_bar,
    ]

    listbox = urwid.ListBox(urwid.SimpleListWalker(listbox_content))
    frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'), header=header)

    palette = [
        ('body','black','light gray', 'standout'),
        ('reverse','light gray','black'),
        ('header','white','dark red', 'bold'),
        ('important','dark blue','light gray',('standout','underline')),
        ('editfc','white', 'dark blue', 'bold'),
        ('editbx','light gray', 'dark blue'),
        ('editcp','black','light gray', 'standout'),
        ('bright','dark gray','light gray', ('bold','standout')),
        ('buttn','black','dark cyan'),
        ('buttnf','white','dark blue','bold'),
        ]

    def unhandled(key):
        if key == 'f8':
            raise urwid.ExitMainLoop()

    loop = urwid.MainLoop(frame, palette, screen,
                          unhandled_input=unhandled, event_loop=urwid.GLibEventLoop())
    loop.run()
#urwid.GLibEventLoop().run()
# if True:
#   
#     import curses
#     stdscr = curses.initscr()
#     curses.noecho()
#     curses.cbreak()
#     stdscr.keypad(1)
#     pipe.mainloop.run()
#     begin_x = 20 ; begin_y = 7
#     height = 5 ; width = 40
#     win = curses.newwin(height, width, begin_y, begin_x)
#     curses.endwin()
#
# else:
#     pipe.mainloop.run()
