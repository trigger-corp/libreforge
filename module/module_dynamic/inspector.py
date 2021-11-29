import time
import json
import os
import shutil
import zipfile
import hashlib
import sys
import subprocess
import re
import urllib
from datetime import datetime
from copy import deepcopy

import build
import utils

def _include_inspector_config_in_app_config(this_module_name, this_module_version, current_path):
    """Update app_config.js(on) for inspector project, and return inspector
    config and app config dicts.
    """
    project_path = os.path.join(current_path, 'ForgeInspector')

    app_config_path = os.path.join(project_path, 'assets', 'app_config.json')
    with open(app_config_path) as app_config_file:
        app_config = json.load(app_config_file)

    this_module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module'))
    inspector_config_path =  os.path.join(this_module_path, 'inspector_config.json')
    with open(inspector_config_path) as inspector_config_file:
        inspector_config = json.load(inspector_config_file)

    # merge in module, this_module and (optionally) core & flags
    app_config['modules'] = dict_merge(app_config['modules'], inspector_config['modules'])
    app_config['modules'][this_module_name] = {
            'version': this_module_version,
            'config': inspector_config['this_module'].get('config', {})
    }
    if 'core' in inspector_config:
        core = app_config['core'] if 'core' in app_config else {}
        app_config['core'] = dict_merge(core, inspector_config['core'])
    if 'flags' in inspector_config:
        flags = app_config['flags'] if 'flags' in app_config else {}
        app_config['flags'] = dict_merge(flags, inspector_config['flags'])

    # write out app_config.js(on)
    with open(app_config_path, 'w') as app_config_file:
        json.dump(app_config, app_config_file)

    app_config_js_path = os.path.join(project_path, 'assets', 'forge', 'app_config.js')
    with open(app_config_js_path, 'w') as app_config_js_file:
        app_config_js_file.write("window.forge = {}; window.forge.config = %s;" % json.dumps(app_config))

    return inspector_config, app_config

def dict_merge(a, b):
    '''recursively merges dict's. not just simple a['key'] = b['key'], if
    both a and b have a key who's value is a dict then dict_merge is called
    on both values and the result stored in the returned dictionary.'''
    if not isinstance(b, dict):
        return b
    result = deepcopy(a)
    for k, v in b.iteritems():
        if k in result and isinstance(result[k], dict):
            result[k] = dict_merge(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result

def _hash_folder(hash, path, ignore=[]):
    '''Update a hash with all of the file/dirnames in a folder as well as all the file contents that aren't in ignore'''
    if not os.path.exists(path):
        return
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            relative_path = full_path[len(path)+1:]
            if not relative_path in ignore and os.path.exists(full_path):
                hash.update(relative_path)
                with open(full_path, 'rb') as cur_file:
                    hash.update(cur_file.read())
        for dirname in dirnames:
            full_path = os.path.join(dirpath, dirname)
            relative_path = full_path[len(path)+1:]
            if not relative_path in ignore:
                hash.update(relative_path)

def _hash_file(hash, path):
    '''Update a hash with the contents for a file'''
    if os.path.isfile(path):
        with open(path, 'rb') as open_file:
            hash.update(open_file.read())

def _update_target(target, cookies):
    """Update the inspector app to a clean one for the current platform version

    returns the location the previous inspector app was moved to"""

    module_dynamic_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    module_path = os.path.abspath(os.path.join(module_dynamic_path, '..'))

    if not os.path.exists(os.path.join(module_dynamic_path, 'cache')):
        os.makedirs(os.path.join(module_dynamic_path, 'cache'))

    # If we don't have an inspector build... get it
    if not os.path.exists(os.path.join(module_dynamic_path, 'cache', '%s.zip' % target)):

        # Do this import here so we can run without the toolkit
        from trigger import forge_tool

        with open(os.path.join(module_dynamic_path, 'platform_version.txt')) as platform_version_file:
            platform_version = platform_version_file.read()

        data = {}

        data['config'] = json.dumps({
                "platform_version": platform_version,
                "uuid": "0",
                "config_version": "2",
                "name": "-",
                "author": "-",
                "version": "0.1",
                "description": "-",
                "modules": {},
        })
        data['target'] = target

        build_state = {
                "state": "pending"
        }
        while build_state['state'] in ('pending', 'working'):
            build_state = forge_tool.singleton.remote._api_post('module/inspector_build/', data=data, cookies=cookies)
            data['id'] = build_state['id']

            if build_state['state'] in ('pending', 'working'):
                time.sleep(3)

        if build_state['state'] != 'complete':
            raise Exception('build failed: %s' % build_state['log_output'])

        forge_tool.singleton.remote._get_file(build_state['file_output'], os.path.join(module_dynamic_path, 'cache', '%s.zip' % target))

    # If we already have an inspector move it out of the way
    moved_to = None
    if os.path.exists(os.path.join(module_path, 'inspector', target)):
        moved_to = os.path.join(module_path, 'inspector', '%s.%s' % (target, datetime.now().isoformat().replace(":", "-")))
        shutil.move(os.path.join(module_path, 'inspector', target), moved_to)

    # Extract new inspector
    with zipfile.ZipFile(os.path.join(module_dynamic_path, 'cache', '%s.zip' % target)) as inspector_zip:
        inspector_zip.extractall(os.path.join(module_path, 'inspector'))

    return moved_to

def hash_android():
    '''Get the current hash for the Android module files'''
    hash = hashlib.sha1()
    _hash_folder(hash, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'android')), ['module.jar'])
    _hash_folder(hash, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'tests')))
    _hash_folder(hash, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'javascript')))
    _hash_file(hash, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'inspector_config.json')))
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'platform_version.txt'))) as platform_version_file:
        hash.update(platform_version_file.read())
    return hash.hexdigest()

def check_android_hash(**kw):
    current_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'inspector', 'an-inspector', '.hash'))
    if not os.path.exists(current_path):
        return {'message': 'Android inspector not found.', 'type': 'error'}
    with open(current_path, 'r') as hash_file:
        if hash_android() == hash_file.read():
            return {'message': 'Android inspector up to date.', 'type': 'good'}
        else:
            return {'message': 'Android inspector out of date.', 'type': 'warning'}

def update_android(cookies, dependencies, system_config={}, **kw):
    previous_path = _update_target('an-inspector', cookies=cookies)
    current_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'inspector', 'an-inspector'))

    # If we're updating copy the module source from the previous inspector
    if previous_path is not None:
        shutil.rmtree(os.path.join(current_path, 'ForgeModule', 'src'))
        if os.path.exists(os.path.join(previous_path, 'src')):
            shutil.copytree(os.path.join(previous_path, 'src'), os.path.join(current_path, 'ForgeModule', 'src'))
        else:
            shutil.copytree(os.path.join(previous_path, 'ForgeModule', 'src'), os.path.join(current_path, 'ForgeModule', 'src'))

        shutil.rmtree(os.path.join(current_path, 'ForgeModule', 'res'))
        if os.path.exists(os.path.join(previous_path, 'res')):
            shutil.copytree(os.path.join(previous_path, 'res'), os.path.join(current_path, 'ForgeModule', 'res'))
        else:
            shutil.copytree(os.path.join(previous_path, 'ForgeModule', 'res'), os.path.join(current_path, 'ForgeModule', 'res'))

        if os.path.exists(os.path.join(previous_path, 'ForgeModule', 'flavors')):
            shutil.copytree(os.path.join(previous_path, 'ForgeModule', 'flavors'), os.path.join(current_path, 'ForgeModule', 'flavors'))

    # If we're updating copy the Android Studio project files (if any) from the previous inspector
    if previous_path is not None:
        if os.path.isdir(os.path.join(previous_path, ".idea")):
            shutil.copytree(os.path.join(previous_path, ".idea"), os.path.join(current_path, ".idea"))
        if os.path.isdir(os.path.join(previous_path, ".gradle")):
            shutil.copytree(os.path.join(previous_path, ".gradle"), os.path.join(current_path, ".gradle"))
        if os.path.isfile(os.path.join(previous_path, "local.properties")):
            shutil.copy(os.path.join(previous_path, "local.properties"), os.path.join(current_path, "local.properties"))
        if os.path.isfile(os.path.join(previous_path, "an-inspector.iml")):
            shutil.copy(os.path.join(previous_path, "an-inspector.iml"), os.path.join(current_path, "an-inspector.iml"))
        if os.path.isfile(os.path.join(previous_path, "ForgeInspector", "ForgeInspector.iml")):
            shutil.copy(os.path.join(previous_path, "ForgeInspector", "ForgeInspector.iml"), os.path.join(current_path, "ForgeInspector", "ForgeInspector.iml"))
        if os.path.isfile(os.path.join(previous_path, "ForgeModule", "ForgeModule.iml")):
            shutil.copy(os.path.join(previous_path, "ForgeModule", "ForgeModule.iml"), os.path.join(current_path, "ForgeModule", "ForgeModule.iml"))

    # Prepare example module code
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'manifest.json'))) as manifest_file:
        manifest = json.load(manifest_file)

    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'identity.json'))):
        with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'identity.json'))) as identity_file:
            this_module_name = str(json.load(identity_file)['name'])
    else:
        this_module_name = str(manifest['name'])

    if "namespace" in manifest:
        namespace = str(manifest['namespace'])
    else:
        namespace = this_module_name

    module_mapping = {
            'inspector': 'inspector',
            namespace: this_module_name
    }

    for root, dirnames, filenames in os.walk(os.path.join(current_path, 'ForgeModule')):
        for filename in filenames:
            with open(os.path.join(root, filename), 'rb') as source:
                lines = source.readlines()
            if 'templatemodule' in os.path.join(root, filename):
                os.remove(os.path.join(root, filename))
                old_dir = os.path.split(os.path.join(root, filename))[0]
                if len(os.listdir(old_dir)) == 0:
                    os.removedirs(old_dir)
                new_dir = os.path.split(os.path.join(root, filename).replace('templatemodule', namespace))[0]
                if not os.path.isdir(new_dir):
                    os.makedirs(new_dir)
            with open(os.path.join(root, filename).replace('templatemodule', namespace), 'wb') as output:
                for line in lines:
                    output.write(line.replace('templatemodule', namespace))

    # Include inspector_config.json in app_config.json/app_config.js
    inspector_config, app_config = _include_inspector_config_in_app_config(this_module_name, manifest['version'], current_path)

    # Dependencies
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'inspector_config.json'))):
        cache_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cache'))
        if "modules" in inspector_config:
            for module, details in inspector_config["modules"].items():
                if details.get("disabled", False):
                    continue
                version = details["version"]

                cached_version_path = os.path.join(cache_path, "%s-%s.zip" % (module, version))
                if not os.path.exists(cached_version_path):
                    # Do this import here so we can run without the toolkit
                    try:
                        from trigger import forge_tool
                        forge_tool.singleton.remote._get_file(dependencies["%s-%s" % (module, version)], cached_version_path)
                    except:
                        # probably running in dev environment
                        module_url = system_config['module_urls'] % (module, version)
                        urllib.urlretrieve(module_url, cached_version_path)

                    with zipfile.ZipFile(cached_version_path) as module_zip:
                        module_zip.extractall(os.path.join(cache_path, "%s-%s" % (module, version)))

                # Add to module_mapping
                manifest_path = os.path.join(cache_path, "%s-%s" % (module, version), 'manifest.json')
                with open(manifest_path) as manifest_file:
                    module_manifest = json.load(manifest_file)
                if 'namespace' in module_manifest:
                    module_namespace = module_manifest['namespace']
                else:
                    module_namespace = module
                module_mapping[module_namespace] = module

                build.apply_module_to_android_project(
                        module_path=os.path.join(cache_path, "%s-%s" % (module, version)),
                        project_path=os.path.join(current_path, 'ForgeInspector'),
                        app_config=app_config,
                        skip_jar=False,
                        include_tests=False,
                        local_build_steps=os.path.join(current_path, 'ForgeInspector', 'assets', 'src')
                )

    # Update inspector with module specific build details
    try:
        build.apply_module_to_android_project(
                module_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module')),
                project_path=os.path.join(current_path, 'ForgeInspector'),
                app_config=app_config,
                skip_jar=True,
                include_tests=True,
                local_build_steps=os.path.join(current_path, 'ForgeInspector', 'assets', 'src')
        )

        # In the Android inspectors case we want any libs to be attached to the ForgeModule project, not the ForgeInspector
        if os.path.exists(os.path.join(current_path, 'ForgeInspector', 'libs')):
            for file_ in os.listdir(os.path.join(current_path, 'ForgeInspector', 'libs')):
                if not file_.startswith("."):
                    shutil.move(
                            os.path.join(current_path, 'ForgeInspector', 'libs', file_),
                            os.path.join(current_path, 'ForgeModule', 'libs'))

        if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'android', 'res'))):

            if not os.path.exists(os.path.join(current_path, 'ForgeModule', 'src')):
                os.makedirs(os.path.join(current_path, 'ForgeModule', 'src'))


    except Exception:
        shutil.rmtree(current_path)
        try:
            raise
            #raise Exception("Applying build steps failed, check build steps and re-update inspector: %s" % e)
        finally:
            try:
                shutil.move(previous_path, current_path)
            except Exception:
                pass

    # Prefix eclipse project names with this module name
    for project in ('ForgeInspector', 'ForgeModule'):
        with open(os.path.join(current_path, project, '.project')) as project_file:
            project_conf = project_file.read()
        project_conf = project_conf.replace('<name>Forge', '<name>%s_Forge' % this_module_name)
        with open(os.path.join(current_path, project, '.project'), 'w') as project_file:
            project_file.write(project_conf)

    with open(os.path.join(current_path, 'ForgeInspector', 'assets', 'module_mapping.json'), 'w') as module_mapping_file:
        json.dump(module_mapping, module_mapping_file)

    with open(os.path.join(current_path, 'ForgeInspector', 'assets', 'app_config.json')) as app_config_json:
        app_config = json.load(app_config_json)

    with open(os.path.join(current_path, 'ForgeInspector', 'assets', 'forge', 'app_config.js'), 'w') as app_config_js:
        app_config_js.write("window.forge = {}; window.forge.config = %s; window.forge.module_mapping = %s;" % (json.dumps(app_config), json.dumps(module_mapping)))

    # Create hash for inspector
    with open(os.path.join(current_path, '.hash'), 'w') as hash_file:
        hash_file.write(hash_android())

def hash_ios():
    '''Get the current hash for the iOS module files'''
    hash = hashlib.sha1()
    _hash_folder(hash, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'ios')), ['module.a'])
    _hash_folder(hash, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'tests')))
    _hash_folder(hash, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'javascript')))
    _hash_file(hash, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'inspector_config.json')))
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'platform_version.txt'))) as platform_version_file:
        hash.update(platform_version_file.read())
    return hash.hexdigest()

def check_ios_hash(**kw):
    current_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'inspector', 'ios-inspector', '.hash'))
    if not os.path.exists(current_path):
        return {'message': 'iOS inspector not found.', 'type': 'error'}
    with open(current_path, 'r') as hash_file:
        if hash_ios() == hash_file.read():
            return {'message': 'iOS inspector up to date.', 'type': 'good'}
        else:
            return {'message': 'iOS inspector out of date.', 'type': 'warning'}

def update_ios(cookies, dependencies, system_config={}, **kw):
    if not sys.platform.startswith('darwin'):
        raise Exception("iOS inspector can only be used on OS X.")

    previous_path = _update_target('ios-inspector', cookies=cookies)
    current_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'inspector', 'ios-inspector'))

    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'manifest.json'))) as manifest_file:
        manifest = json.load(manifest_file)

    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'identity.json'))):
        with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'identity.json'))) as identity_file:
            this_module_name = str(json.load(identity_file)['name'])
    else:
        this_module_name = str(manifest['name'])

    if 'namespace' in manifest:
        namespace = str(manifest['namespace'])
    else:
        namespace = this_module_name

    module_mapping = {
            'inspector': 'inspector',
            namespace: this_module_name
    }

    # If we're updating copy the module source from the previous inspector
    if previous_path is not None:
        shutil.rmtree(os.path.join(current_path, 'ForgeModule'))
        shutil.copytree(os.path.join(previous_path, 'ForgeModule'), os.path.join(current_path, 'ForgeModule'))
    else:
        # Prepare example module code

        for root, dirnames, filenames in os.walk(os.path.join(current_path, 'ForgeModule')):
            for filename in filenames:
                with open(os.path.join(root, filename), 'r') as source:
                    lines = source.readlines()
                if 'templatemodule' in filename:
                    os.remove(os.path.join(root, filename))
                with open(os.path.join(root, filename.replace('templatemodule', namespace)), 'w') as output:
                    for line in lines:
                        output.write(line.replace('templatemodule', namespace))

    if os.path.exists(os.path.join(current_path, 'ForgeModule', 'forge_headers')):
        shutil.rmtree(os.path.join(current_path, 'ForgeModule', 'forge_headers'))

    # Include inspector_config.json in app_config.json/app_config.js
    inspector_config, app_config = _include_inspector_config_in_app_config(this_module_name, manifest['version'], current_path)

    # Dependencies
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'inspector_config.json'))):
        cache_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cache'))

        if "modules" in inspector_config:
            for module, details in inspector_config["modules"].items():
                if details.get("disabled", False):
                    continue
                version = details["version"]

                cached_version_path = os.path.join(cache_path, "%s-%s.zip" % (module, version))

                if not os.path.exists(cached_version_path):
                    # Do this import here so we can run without the toolkit
                    try:
                        from trigger import forge_tool
                        forge_tool.singleton.remote._get_file(dependencies["%s-%s" % (module, version)], cached_version_path)
                    except:
                        # probably running in dev environment
                        module_url = system_config['module_urls'] % (module, version)
                        urllib.urlretrieve(module_url, cached_version_path)

                    with zipfile.ZipFile(cached_version_path) as module_zip:
                        module_zip.extractall(os.path.join(cache_path, "%s-%s" % (module, version)))

                # Add to module_mapping
                manifest_path = os.path.join(cache_path, "%s-%s" % (module, version), 'manifest.json')
                with open(manifest_path) as manifest_file:
                    module_manifest = json.load(manifest_file)
                if 'namespace' in module_manifest:
                    module_namespace = module_manifest['namespace']
                else:
                    module_namespace = module
                module_mapping[module_namespace] = module

                build.apply_module_to_ios_project(
                        os.path.join(cache_path, "%s-%s" % (module, version)),
                        current_path,
                        app_config=app_config,
                        skip_a=False,
                        include_tests=False,
                        local_build_steps=os.path.join(current_path, 'ForgeInspector', 'assets', 'src')
                )

    # Update inspector with module specific build details
    try:
        build.apply_module_to_ios_project(
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module')),
                current_path,
                app_config=app_config,
                skip_a=True,
                include_tests=True,
                local_build_steps=os.path.join(current_path, 'ForgeInspector', 'assets', 'src')
        )
    except Exception:
        shutil.rmtree(current_path)
        try:
            raise
            #raise Exception("Applying build steps failed, check build steps and re-update inspector: %s" % e)
        finally:
            try:
                shutil.move(previous_path, current_path)
            except Exception:
                pass

    with open(os.path.join(current_path, 'ForgeInspector', 'assets', 'module_mapping.json'), 'w') as module_mapping_file:
        json.dump(module_mapping, module_mapping_file)

    with open(os.path.join(current_path, 'ForgeInspector', 'assets', 'app_config.json')) as app_config_json:
        app_config = json.load(app_config_json)

    with open(os.path.join(current_path, 'ForgeInspector', 'assets', 'forge', 'app_config.js'), 'w') as app_config_js:
        app_config_js.write("window.forge = {}; window.forge.config = %s; window.forge.module_mapping = %s;" % (json.dumps(app_config), json.dumps(module_mapping)))

    # Create hash for inspector
    with open(os.path.join(current_path, '.hash'), 'w') as hash_file:
        hash_file.write(hash_ios())

def hash_osx():
    '''Get the current hash for the Android module files'''
    hash = hashlib.sha1()
    _hash_folder(hash, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'tests')))
    _hash_folder(hash, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module', 'javascript')))
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'platform_version.txt'))) as platform_version_file:
        hash.update(platform_version_file.read())
    return hash.hexdigest()

def update_osx(cookies, **kw):
    if not sys.platform.startswith('darwin'):
        raise Exception("OSX inspector can only be used on OS X.")

    previous_path = _update_target('osx-inspector', cookies=cookies)
    current_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'inspector', 'osx-inspector'))

    # If we're updating copy the module source from the previous inspector
    if previous_path is not None:
        shutil.rmtree(os.path.join(current_path, 'ForgeModule'))
        shutil.copytree(os.path.join(previous_path, 'ForgeModule'), os.path.join(current_path, 'ForgeModule'))

    # Update inspector with module specific build details
    try:
        build.apply_module_to_osx_project(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'module')), current_path, skip_framework=True, inspector_config=True, include_tests=True, local_build_steps=os.path.join(current_path, 'ForgeInspector', 'assets', 'src'))
    except Exception:
        shutil.rmtree(current_path)
        try:
            raise
            #raise Exception("Applying build steps failed, check build steps and re-update inspector: %s" % e)
        finally:
            try:
                shutil.move(previous_path, current_path)
            except Exception:
                pass

    # Create hash for inspector
    with open(os.path.join(current_path, '.hash'), 'w') as hash_file:
        hash_file.write(hash_osx())
