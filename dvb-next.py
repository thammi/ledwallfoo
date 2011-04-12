#/usr/bin/env python

import json
import urllib

#wget --user-agent=foo -o- --header='Connection: close' --header='Accept: */*' -O -

dvbhandle = urllib.urlopen('http://widgets.vvo-online.de/abfahrtsmonitor/Abfahrten.do?ort=Dresden&hst=Pirnaischer+Platz&vs=0')

rawjson = dvbhandle.read()
data = json.loads(rawjson)

output = u''

for line in data:
    entry = tuple(line)
    stripped_linenumber = int(entry[0].replace('E', ''))
    if stripped_linenumber in [1,2,3,4,6,7,8,9,10,11,12,13]:
        output += u'\U0001F68B %s \U00002794 %s \U00008986 %s\t' % entry # tram
    elif stripped_linenumber > 60:
        output += u'\U0001F68C %s \U00002794 %s \U00008986 %s\t' % entry # bus
    else:
        output += '? %s \U00002794 %s \U00008986 %s\t' % entry

print output
