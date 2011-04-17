#!/usr/bin/env python
# TODO: licence and copyright by core

import json
import urllib

from fade_text import FadingText
from ledwall import LedMatrix

def fetchDVBData():
    dvbhandle = urllib.urlopen('http://widgets.vvo-online.de/abfahrtsmonitor/Abfahrten.do?ort=Dresden&hst=Pirnaischer+Platz&vs=0')

    rawjson = dvbhandle.read()
    data = json.loads(rawjson)

    output = u''

    for line in data:
        entry = tuple(line)
        stripped_linenumber = int(entry[0].replace('E', ''))
        if stripped_linenumber in [1,2,3,4,6,7,8,9,10,11,12,13]:
            output += u'T %s \U00002192 %s \U00002694 %s +++' % entry # tram
        elif stripped_linenumber > 60:
            output += u'B %s \U00002192 %s \U00002694 %s +++' % entry # bus
        else:
            output += '? %s \U00002192 %s \U00002694 %s +++' % entry
    return output

if __name__ == '__main__':
    matrix = LedMatrix()
    try:
        ft = FadingText(matrix, fetchDVBData()).endless()
    finally:
        matrix.close()

