import json
import logging
import os
from os import path
import platform
import subprocess
import sys

from build import ConfigurationError
from module_dynamic import lib
from module_dynamic.lib import BASE_EXCEPTION
from lib import task, path_to_lib

log = logging.getLogger(__name__)

@task
def lint_javascript(build):
	if build.forge_root is None:
		raise BASE_EXCEPTION("We don't know where the Forge tools are")

	log.info("Checking JavaScript files...")
	if sys.platform.startswith("linux"):
		if platform.architecture()[0] == '64bit':
			command = path.join(build.forge_root, "bin", "jsl-64")
		else:
			command = path.join(build.forge_root, "bin", "jsl")
	elif sys.platform.startswith("darwin"):
		command = path.join(build.forge_root, "bin", "jsl-mac")
	elif sys.platform.startswith("win"):
		command = path.join(build.forge_root, "bin", "jsl.exe")
	
	data = lib.PopenWithoutNewConsole(
		[
			command,
			"-conf",
			path.join(build.forge_root, "jsl.conf"),

			"-process",
			path.join(os.getcwd(), "src", "*.js"),

			"-nologo",
			"-nofilelisting",
			"-nosummary"
		],
		stdout=subprocess.PIPE
	).communicate()[0]
	map(log.warning, [line for line in data.split('\n') if line])
	log.info("JavaScript check complete")

@task
def check_local_config_schema(build):
	log.info("Verifying your configuration settings...")
	# leave this import here: might not be on sys.path in some situations
	import validictory

	local_conf_filename = build.tool_config.get('general.local_config')
	if local_conf_filename is not None:
		# explicit conf file defined
		if not path.isfile(local_conf_filename):
			raise ConfigurationError("{file} does not exist!".format(file=local_conf_filename))
	else:
		local_conf_filename = 'local_config.json'
		if not path.isfile(local_conf_filename):
			log.warning("Local configuration file '{file}' does not exist!".format(file=local_conf_filename))
	
	with open(local_conf_filename) as local_conf_file:
		local_conf = json.load(local_conf_file)

	from forge.remote import Remote
	from forge import build_config
	remote = Remote(build_config.load())
	local_conf_schema = remote._api_get('platform/{platform_version}/local_config_schema'.format(
			platform_version=build.config['platform_version']))
	
	try:
		validictory.validate(local_conf, local_conf_schema)
	except validictory.validator.UnexpectedPropertyError as e:
		log.warning('Unexpected setting: "{error}" in "{file}". This will be ignored.'.format(
			file=local_conf_filename,
			error=e)
		)
	log.info("Configuration settings check complete")
