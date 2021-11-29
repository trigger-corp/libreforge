import json
import os
import shutil
import zipfile

from build import cd

def create_template(name, path, namespace=None, **kw):
	if namespace is None:
		namespace = name
	os.makedirs(os.path.join(path, 'module'))
	with open(os.path.join(path, 'module', 'manifest.json'), 'w') as manifest_file:
		manifest = {
			"namespace": namespace,
			"version": "0.1",
			"description": "My module template"
		}

		with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'platform_version.txt'))) as platform_version_file:
			manifest['platform_version'] = platform_version_file.read()
			manifest['min_platform_version'] = manifest['platform_version']

		json.dump(manifest, manifest_file, indent=4, sort_keys=True)

	with open(os.path.join(path, 'module', 'identity.json'), 'w') as identity_file:
		identity = {
			"name": name
		}

		json.dump(identity, identity_file, indent=4, sort_keys=True)

	# Copy template module
	template_path = os.path.abspath(os.path.join(os.path.split(__file__)[0], 'templatemodule'))

	for root, dirnames, filenames in os.walk(template_path):
		for filename in filenames:
			relative_path = os.path.join(root, filename)[len(template_path)+1:]
			with open(os.path.join(root, filename), 'r') as source:
				lines = source.readlines()
			new_dir = os.path.split(os.path.join(path, 'module', relative_path.replace('templatemodule', namespace)))[0]
			if not os.path.isdir(new_dir):
				os.makedirs(new_dir)
			with open(os.path.join(path, 'module', relative_path.replace('templatemodule', namespace)), 'w') as output:
				for line in lines:
					output.write(line.replace('templatemodule', namespace))

	return load(path, manifest)

def load(path, manifest, **kw):
	if not os.path.exists(os.path.join(path, 'module', 'identity.json')):
		identity = {
			'name': manifest['name']
		}
		with open(os.path.join(path, 'module', 'identity.json'), 'w') as identity_file:
			json.dump(identity, identity_file, indent=4, sort_keys=True)

	def write_manifest():
		manifest_path = os.path.join(path, 'module', 'manifest.json')
		with open(manifest_path, 'w') as manifest_file:
			json.dump(manifest, manifest_file, sort_keys=True, indent=4)

	if 'namespace' not in manifest:
		with open(os.path.join(path, 'module', 'identity.json'), 'r') as identity_file:
			identity = json.load(identity_file)
		manifest['namespace'] = identity['name']
		write_manifest()

	if 'name' in manifest:
		del manifest['name']
		write_manifest()

	module_model = {}
	module_model['local_path'] = path
	module_model['module_dynamic_path'] = os.path.join(path, ".trigger", "module_dynamic")
	module_model['files'] = {
		'manifest': os.path.join(path, 'module', 'manifest.json'),
		'identity': os.path.join(path, 'module', 'identity.json'),
		'inspector_config': os.path.join(path, 'module', 'inspector_config.json'),
		'module_structure': os.path.join(path, ".trigger", "schema", "module_structure.json"),
		'config_schema': os.path.join(path, 'module', 'config_schema.json'),
	}
	module_model['rawfiles'] = {
		'dynamic_platform_version': os.path.join(path, ".trigger", "platform_version.txt")
	}
	module_model['directories'] = {
		'module_directory': os.path.join(path, 'module')
	}
	return module_model

def create_upload_zip(path, subdirs = [], **kw):
	module_path = os.path.abspath(os.path.join(path, 'module'))

	zip_base = os.path.abspath(os.path.join(path, '.trigger', 'upload_tmp'))

	if os.path.exists(zip_base+".zip"):
		os.unlink(zip_base+".zip")

	if len(subdirs):
		zip_path = _make_partial_archive(zip_base, subdirs, root_dir=module_path)	
	else:		
		zip_path = shutil.make_archive(zip_base, 'zip', root_dir=module_path)

	return zip_path

def _make_partial_archive(zip_base, subdirs, root_dir):
	zip = zipfile.ZipFile(zip_base + ".zip", "w")
	with cd(root_dir):
		for subdir in subdirs:
			if not os.path.exists(subdir):
				continue
			for root, dirs, files in os.walk(subdir):
				for file in files:
					zip.write(os.path.join(root, file))
	zip.close()
	return zip_base + ".zip"
