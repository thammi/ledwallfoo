#/usr/bin/env python

import json
import urllib

#wget --user-agent=foo -o- --header='Connection: close' --header='Accept: */*' -O -

dvbhandle = urllib.urlopen('http://widgets.vvo-online.de/abfahrtsmonitor/Abfahrten.do?ort=Dresden&hst=Pirnaischer+Platz&vs=0')

rawjson = dvbhandle.read()
data = json.loads(rawjson)

for line in data:
    print u'\U0001F68B %s \U00002794 %s \U00008986 %s' % tuple(line)
