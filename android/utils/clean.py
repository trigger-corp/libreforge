# Remove all io.trigger.* apps from a device

import subprocess

adb = 'adb'

p = subprocess.Popen([adb, 'shell', 'pm', 'list', 'packages'], stdout=subprocess.PIPE)

packages = p.communicate()[0].split()

for package in packages:
	if package[0:19] == 'package:io.trigger.':
		print "Uninstalling: "+package[8:];
		subprocess.Popen([adb, 'uninstall', package[8:]]).wait()
		