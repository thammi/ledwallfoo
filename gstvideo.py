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
    self.player.set_property("flags", 0x00000001 | 0x00000002 | 0x00000008 | 0x00000010 | 0x00000100 | 0x00000200)

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
    print 'on_eos'
    self.mainloop.quit()

  def on_tag(self, bus, msg):
    taglist = msg.parse_tag()
    print 'on_tag:'
    for key in taglist.keys():
      print '\t%s = %s' % (key, taglist[key])

  def on_error(self, bus, msg):
    error = msg.parse_error()
    print 'on_error:', error[1]
    self.mainloop.quit()

#
# Code to test the MySink class
#
matrix = LedMatrix(server=args.server)
#matrix = LedMatrix(server="127.0.0.1")

pipe = LedPipe(args.file[0], matrix, visualize=args.visualize)

import glib, sys, os, fcntl

class IODriver(object):
    def __init__(self, line_callback=None, key_callback=None):
        self.buffer = ''
        self.line_callback = line_callback
        self.key_callback = key_callback
        flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
        flags |= os.O_NONBLOCK | os.O_NDELAY
        fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, flags)
        glib.io_add_watch(sys.stdin, glib.IO_IN, self.io_callback)

    def io_callback(self, fd, condition):
        chunk = fd.read()
        if self.key_callback:
            self.key_callback(chunk)
        for char in chunk:
            self.buffer += char
            if char == '\n':
                if self.line_callback:
                    self.line_callback(self.buffer)
                self.buffer = ''

        return True

def line_entered(line):
    print "You have typed:", line.strip()

d = IODriver(key_callback=line_entered)

pipe.mainloop.run()
