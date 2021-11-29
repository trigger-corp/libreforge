from collections import defaultdict
import socket
import time
import errno
import json
import logging
import os
from os import path
import re
import shutil
import sys
import subprocess
import tempfile
import threading
from urlparse import urljoin

import requests

from module_dynamic import lib
from module_dynamic.lib import cd
from lib import task
from module_dynamic import utils
from module_dynamic.utils import run_shell, ShellError

LOG = logging.getLogger(__name__)

class ServeError(lib.BASE_EXCEPTION):
	pass

NODEJS_HELP = """\
Failed to find the node.js '{tool}' executable on your PATH or the
default install location.

You can download the latest version of node.js from: 

    http://nodejs.org/download/

You can also use the 'node_path' setting in your app's tools configuration if
node.js has been installed in a custom location."""

@task
def serve_ios(build):
	address = get_local_address(build)
	port = get_local_port(build)
	_setup_app_config(build, path.join("development", "ios", "simulator-ios.app", "assets"), address, port)
	_setup_app_config(build, path.join("development", "ios", "device-ios.app", "assets"), address, port)
	_serve(build, "ios", address, port)

@task
def serve_android(build):
	address = get_local_address(build)
	port = get_local_port(build)
	target = list(build.enabled_platforms)[0]
	_setup_app_config(build, path.join("development", target, "assets"), address, port)
	_serve(build, target, address, port)

@task
def serve_web(build):
	raise ServeError("Forge Live is not yet supported for web targets")
	address = get_local_address(build)
	port = get_local_port(build)
	_serve(build, "web", address, port)

def _serve(build, target, address, port):
	LOG.info("Initializing Forge Live...");

	_update_path_for_node(build)
	_setup_livereload(build, target)

	LOG.info("Serving live updates for '%s' on: http://%s:%s" % (target, address, port));

	# call grunt serve
	if sys.platform.startswith("win"):
		grunt = path.join("node_modules", ".bin", "grunt.cmd")
	else:
		grunt = path.join("node_modules", ".bin", "grunt")

	grunt_serve_cmd = [grunt, "serve", 
					   "--address", address,
					   "--port", "{port}".format(port=port),
					   "--target", target,
					   "--no-color"]

	def could_not_start_grunt(line):
		return line.startswith("TODO error condition")

	with cd(path.join("development", "live")):
		process_group = utils.ProcessGroup()
		process_group.spawn(
			grunt_serve_cmd,
			fail_if=could_not_start_grunt,
			command_log_level=logging.DEBUG
		)


def _setup_app_config(build, dest, address, port):
	app_config = path.join(dest, "app_config.json")
	with open(app_config) as f:
		config = json.load(f)
		if not "general" in config["core"]:
			config["core"]["general"] = {}
		config["core"]["general"]["live"] = {
			"enabled": True,
			"url": "http://{address}:{port}/src/index.html".format(
				address=address,
				port=port
			)
		}
	with open(app_config, "w") as f:
		json.dump(config, f, indent=4, sort_keys=True)


def _setup_livereload(build, target):
	'''setup livereload service'''	

	template = lib.expand_relative_path(build, path.join('.template', 'lib', 'live'))
	live = lib.expand_relative_path(build, path.join('development', 'live'))

	if not path.isdir(live):
		os.mkdir(live)

	with cd(live):
		shutil.copyfile(path.join(template, "package.json"), "package.json")
		shutil.copyfile(path.join(template, "Gruntfile.js"), "Gruntfile.js")
		_npm(build, "install")


def _update_path_for_node(build):
	'''change sys.path to include the directory which holds node and npm

	:param build: :class:`Build` instance
	'''
	path_chunks = os.environ["PATH"].split(os.pathsep)

	# configuration setting overrides all
	manual = build.tool_config.get('web.node_path')
	if manual is None:
		manual = build.tool_config.get('general.live.node_path')

	if manual is None:
		possible_locations = defaultdict(list)
		possible_locations.update({
			'darwin': ['/opt/local/bin', '/usr/local/bin'],
			'linux': ['/usr/bin', '/usr/local/bin', '/opt/local/bin'],
			'win': ['C:/Program Files (x86)/nodejs', 'C:/Program Files/nodejs']
		})
		for location in possible_locations[sys.platform]:
			if not location in path_chunks:	
				path_chunks.append(location)
	else:
		# override given
		if not isinstance(manual, list):
			manual = [manual]

		if sys.platform.startswith("win"):
			# Popen will fail if os.environ has unicodes in on windows
			# not sure what encoding environ values should be in
			manual = [m.encode('ascii', errors='replace') for m in manual]

		LOG.info('Adding node locations from local_config.json to PATH %r' % manual)
		for manual_path in manual:
			abs_manual_path = os.path.abspath(manual_path)
			if abs_manual_path not in path_chunks:
				path_chunks.insert(0, abs_manual_path)
	
	new_path = os.pathsep.join(path_chunks)
	LOG.debug('Setting PATH to %r' % new_path)
	os.environ["PATH"] = new_path

	# check if we have node
	if sys.platform.startswith("win"):
		node = "node.exe"
	else:
		node = "node"

	if not utils.which(node):
		raise ServeError(NODEJS_HELP.format(tool=node))

	return new_path


def _npm(build, *args, **kw):
	if sys.platform.startswith("win"):
		npm = "npm.cmd"
	else:
		npm = "npm"
	if not utils.which(npm):
		raise ServeError(NODEJS_HELP.format(tool=npm))

	kw['check_for_interrupt'] = True
	run_shell(npm, *args, **kw)


# - get local address ---------------------------------------------------
# from: http://stackoverflow.com/a/20710035/1737472

# imports
import errno
import socket

# localhost prefixes
_local_networks = ("127.", "0:0:0:0:0:0:0:1")

# ignore these prefixes -- localhost, unspecified, and link-local
_ignored_networks = _local_networks + ("0.", "0:0:0:0:0:0:0:0", "169.254.", "fe80:")

def detect_family(addr):
	if "." in addr:
		assert ":" not in addr
		return socket.AF_INET
	elif ":" in addr:
		return socket.AF_INET6
	else:
		raise ValueError("invalid ipv4/6 address: %r" % addr)

def expand_addr(addr):
	"""convert address into canonical expanded form --
	no leading zeroes in groups, and for ipv6: lowercase hex, no collapsed groups.
	"""
	family = detect_family(addr)
	addr = socket.inet_ntop(family, socket.inet_pton(family, addr))
	if "::" in addr:
		count = 8-addr.count(":")
		addr = addr.replace("::", (":0" * count) + ":")
		if addr.startswith(":"):
			addr = "0" + addr
	return addr

def _get_local_address(family, remote):
	try:
		s = socket.socket(family, socket.SOCK_DGRAM)
		try:
			s.connect((remote, 9))
			return s.getsockname()[0]
		finally:
			s.close()
	except socket.error:
		return None

def get_local_port(build):
	manual = build.tool_config.get('general.live.port')
	if manual is not None:
		LOG.debug("Using manually specified port: %s" % manual)
		return manual
	else:
		LOG.debug("Using default port: %s" % "31337")
		return "31337"

def get_local_address(build, remote=None, ipv6=True):
	manual = build.tool_config.get('general.live.address')
	if manual is not None:
		LOG.debug("Using manually specified address: %s" % manual)
		return manual

	# TODO windows doesn't support socket.inet_ntop(family, socket.inet_pton(family, addr))
	if sys.platform.startswith("win"):
		address = socket.gethostbyname(socket.gethostname())
		return address

	"""get LAN address of host

	:param remote:
		return	LAN address that host would use to access that specific remote address.
		by default, returns address it would use to access the public internet.

	:param ipv6:
		by default, attempts to find an ipv6 address first.
		if set to False, only checks ipv4.

	:returns:
		primary LAN address for host, or ``None`` if couldn't be determined.
	"""
	if remote:
		family = detect_family(remote)
		local = _get_local_address(family, remote)
		if not local:
			return None
		if family == socket.AF_INET6:
			# expand zero groups so the startswith() test works.
			local = expand_addr(local)
		if local.startswith(_local_networks):
			# border case where remote addr belongs to host
			return local
	else:
		# NOTE: the two addresses used here are TESTNET addresses,
		#		which should never exist in the real world.
		if ipv6:
			local = _get_local_address(socket.AF_INET6, "2001:db8::1234")
			# expand zero groups so the startswith() test works.
			if local:
				local = expand_addr(local)
		else:
			local = None
		if not local:
			local = _get_local_address(socket.AF_INET, "192.0.2.123")
			if not local:
				return None
	if local.startswith(_ignored_networks):
		return None
	return local
