import codecs
import logging
import shutil
import json
import os

from module_dynamic.lib import BASE_EXCEPTION, current_call
from lib import task

LOG = logging.getLogger(__name__)

class MigrationError(BASE_EXCEPTION):
	pass

MIGRATE_CONFIG_MESSAGE = """
<p class="lead">
  Your app config needs to be updated to make it compatible with this platform version.
</p>
<p>
  This will change <strong>src/config.json</strong>, so if you're using version control then you will want to check it in afterwards.
</p>
<p>
  We'll back up your original config to <strong>src/config.json.bak</strong> in case you need it. If you're using any of your own
  native plugins then you will need to convert these to modules.
</p>
"""

@task
def migrate_to_config_version_4(path):
	old_config_path = os.path.join(path, 'src', 'config.json')
	with codecs.open(old_config_path, 'r', 'utf8') as config_file:
		config = json.load(config_file)

	if int(config['config_version']) >= 4:
		return False

	LOG.info("Detected config version older than 4, need to migrate.")

	call = current_call()
	
	event_id = call.emit(
		'confirm', title='Confirm config migration',
		content=MIGRATE_CONFIG_MESSAGE, cancellable=False)
	response = call.wait_for_response(event_id)
	if not response.get('data'):
		raise BASE_EXCEPTION("User cancelled migration")
	
	LOG.info("Migrating config.json from version %s to version 4" % config['config_version'])

	new_config = {
		# Required config
		"config_version": "4",
		"name": config["name"],
		"author": config["author"],
		"platform_version": config["platform_version"],
		"version": config["version"],
		"modules": {},
		"core": config.get("requirements", {}),
	}

	if "general" not in new_config["core"]:
		new_config["core"]["general"] = {}
	if "reload" not in new_config["core"]["general"]:
		new_config["core"]["general"]["reload"] = False
	if "trusted_urls" not in new_config["core"]["general"] and "trusted_urls" in config:
		new_config["core"]["general"]["trusted_urls"] = config["trusted_urls"]

	if "description" in config:
		new_config["description"] = config["description"]
	if "homepage" in config:
		new_config["homepage"] = config["homepage"]

	if "partners" in config and "parse" in config["partners"]:
		new_config["modules"]["parse"] = {
			"version": "2.0",
			"config": config["partners"]["parse"]
		}

	for module in config["modules"]:
		# previously setting a module config to false would just enable it with no configuration
		# preserve backwards compatibility
		if config["modules"][module] is False:
			config["modules"][module] = True

		if module == "requirements":
			# These modules are now core and configured under top level core
			for platform in config["modules"][module]:
				if platform not in new_config["core"]:
					new_config["core"][platform] = {}
				for setting in config["modules"][module][platform]:
					new_config["core"][platform][setting] = config["modules"][module][platform][setting]
			continue

		if module == "package_names":
			for platform in config["modules"]["package_names"]:
				if platform not in new_config["core"]:
					new_config["core"][platform] = {}
				new_config["core"][platform]["package_name"] = config["modules"]["package_names"][platform]
			continue

		if module == "reload":
			new_config["core"]["general"]["reload"] = True
			continue

		if module == "logging":
			new_config["core"]["general"]["logging"] = config["modules"][module]
			continue

		if module in ["is", "event", "internal", "message", "tools"]:
			# These are now core, ignore them
			continue

		new_config["modules"][module] = {
			"version": "2.0"
		}
		if config["modules"][module] is True:
			continue

		if module == "activations":
			new_config["modules"]["activations"]["config"] = {
				"activations": config["modules"]["activations"]
			}
			continue

		new_config["modules"][module]["config"] = config["modules"][module]

	# back up old config
	LOG.info("Backing up src/config.json to src/config.json.bak")
	shutil.copy(old_config_path, old_config_path + '.bak')

	# write out new config
	LOG.info("Writing out new config")
	with codecs.open(old_config_path, 'w', 'utf8') as old_config_file:
		json.dump(new_config, old_config_file, indent=4)

	LOG.warning("Updated src/config.json to config version 4 - you may want to check it into version control!")
	return True

