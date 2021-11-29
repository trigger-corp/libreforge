import codecs
import fnmatch
import glob
import os
from os import path
import re
import shutil
import sys
import uuid
import json
from copy import copy
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED

import hashlib
import pystache

from xml.etree import ElementTree
# Any namespaces must be registered or the parser will rename them
ElementTree.register_namespace('android', 'http://schemas.android.com/apk/res/android')
ElementTree.register_namespace('tools', 'http://schemas.android.com/tools')

from build import ConfigurationError
from module_dynamic import lib
from module_dynamic.lib import temp_file
from module_dynamic.lib import walk_with_depth, read_file_as_str, cd
from lib import task

import android_tasks
import ios_tasks
import osx_tasks
import serve_tasks

from module_dynamic import utils
from module_dynamic import build_steps_local
from module_dynamic import build_steps_predicates


@task
def add_element_to_xml(build, file, element, to=None, unless=None):
    '''add new element to an XML file

    :param file: filename or file object
    :param element: dict containing tag and optionally attributes, text and children
    :param to: sub element tag name or path we will append to
    :param unless: don't add anything if this tag name or path already exists
    '''
    def create_element(tag, attributes={}, text=None, children=[]):
        for attribute in attributes:
            if isinstance(attributes[attribute], str) or isinstance(attributes[attribute], unicode):
                attributes[attribute] = pystache.render(attributes[attribute], build.config)
        element = ElementTree.Element(tag, attributes)
        if text is not None:
            if isinstance(text, str) or isinstance(text, unicode):
                text = pystache.render(text, build.config)
            element.text = text
        for child in children:
            element.append(create_element(**child))

        return element

    xml = ElementTree.ElementTree()
    xml.parse(file)
    if to is None:
        el = xml.getroot()
    else:
        el = xml.find(to, dict((v,k) for k,v in ElementTree._namespace_map.items()))
    if not unless or xml.find(unless, dict((v,k) for k,v in ElementTree._namespace_map.items())) is None:
        new_el = create_element(**element)
        el.append(new_el)
        xml.write(file)

@task
def set_element_value_xml(build, file, value, element=None):
    '''set text contents of an XML element

    :param build: the current build.Build
    :param file: filename or file object
    :param value: the new element contents (will be templated)
    :param element: tag name or path to change (defaults to root node)
    '''
    xml = ElementTree.ElementTree()
    xml.parse(file)
    if element is None:
        el = xml.getroot()
    else:
        el = xml.find(element, dict((v,k) for k,v in ElementTree._namespace_map.items()))
    el.text = utils.render_string(build.config, value).decode('utf8', errors='replace')
    xml.write(file)

@task
def set_attribute_value_xml(build, file, value, attribute, element=None):
    '''set contents of an XML element's attribute

    :param build: the current build.Build
    :param file: filename or file object
    :param value: the new attribute value (will be templated)
    :param attribute: attribute name
    :param element: tag name or path to change (defaults to root node)
    '''
    xml = ElementTree.ElementTree()
    xml.parse(file)
    if element is None:
        el = xml.getroot()
    else:
        el = xml.find(element, dict((v,k) for k,v in ElementTree._namespace_map.items()))

    # set is not aware of namespaces, so we have to replace "namespace" with "{schema}"
    namespaces = dict((v,k) for k,v in ElementTree._namespace_map.items())
    if ":" in attribute:
        parts = attribute.split(":")
        attribute = "{%s}%s" % (namespaces[parts[0]], parts[1])

    el.set(attribute, utils.render_string(build.config, value))

    xml.write(file)

@task
def rename_files(build, **kw):
    if 'from' not in kw or 'to' not in kw:
        raise ConfigurationError('rename_files requires "from" and "to" keyword arguments')

    return _rename_or_copy_files(build, kw['from'], kw['to'], rename=True)

@task
def copy_files(build, **kw):
    if 'from' not in kw or 'to' not in kw:
        raise ConfigurationError('copy_files requires "from" and "to" keyword arguments')

    return _rename_or_copy_files(build, kw['from'], kw['to'], rename=False, ignore_patterns=kw.get('ignore_patterns'))

class Pattern(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

def git_ignore(root, patterns):
    classified_patterns = []
    with cd(root):
        for pattern in patterns:
            if pattern:
                if '/' in pattern[:-1]:
                    ignored_paths = (Pattern('path', match) for match in glob.glob(pattern))
                    classified_patterns.extend(ignored_paths)
                else:
                    classified_patterns.append(Pattern('file', pattern))

    def git_ignorer(src, names):
        relative_src = src[len(root):].lstrip(r"""\/""")
        ignored = []
        for name in names:
            for pattern in classified_patterns:
                if pattern.type == 'path':
                    if path.join(relative_src, name) == os.path.normpath(pattern.value):
                        ignored.append(name)
                elif pattern.type == 'file':
                    ignore_name = pattern.value
                    if pattern.value[-1] in ('/', '\\'):
                        if path.isdir(path.join(src, name)):
                            ignore_name = ignore_name[:-1]

                    if fnmatch.fnmatch(name, ignore_name):
                        ignored.append(name)

        return set(ignored)

    return git_ignorer

@task
def _rename_or_copy_files(build, frm, to, rename=True, ignore_patterns=None):
    if ignore_patterns is None:
        ignore_patterns = []

    from_, to = utils.render_string(build.config, frm), utils.render_string(build.config, to)
    if path.isdir(from_):
        ignore_func = git_ignore(from_, ignore_patterns)
    else:
        ignore_func = None

    if not path.exists(from_):
        build.log.debug('%s does not exist. Skipping operation' % from_)
        return
    elif rename:
        build.log.debug('renaming {from_} to {to}'.format(**locals()))
        shutil.move(from_, to)
    else:
        if '*' in to:
            # looks like a glob - last directory in path might not exist.
            tos = glob.glob(path.dirname(to))
            tos = [path.join(t,path.basename(to)) for t in tos]
        else:
            # don't glob in case the to path doesn't exist yet
            tos = [to]

        for found_to in tos:
            build.log.debug('copying {from_} to {found_to}'.format(**locals()))
            if path.isdir(from_):
                shutil.copytree(from_, found_to, ignore=ignore_func)
            else:
                shutil.copy(from_, found_to)

@task
def find_and_replace(build, *files, **kwargs):
    '''replace one string with another in a set of files

    :param kwargs: must contain ``find`` and ``replace`` keys,
    representing the string to look for, and string to replace
    with, respectively.

    :param kwargs: can also contain the ``template`` boolean
    argument, which determines if we will run the ``replace``
    argument through genshi templating first (defaults to True).

    :param files: array of glob patterns to select files
    :param kwargs: must contain ``find`` and ``replace`` keys
    '''
    if "in" in kwargs:
        files = kwargs['in']
    if "find" not in kwargs:
        raise ConfigurationError("Find not passed in to find_and_replace")
    if "replace" not in kwargs:
        raise ConfigurationError("Replace not passed in to find_and_replace")
    template = kwargs.get('template', True)
    find = kwargs["find"]
    replace = kwargs['replace']
    if template:
        replace = utils.render_string(build.config, replace)

    replace_summary = replace[:60]+'...' if len(replace) > 60 else replace
    build.log.debug("replacing %s with %s" % (find, repr(replace_summary)))

    for glob_str in files:
        found_files = glob.glob(utils.render_string(build.config, glob_str))
        if len(found_files) == 0:
            build.log.warning('No files were found to match pattern "%s"' % glob_str)
        for _file in found_files:
            _replace_in_file(build, _file, find, replace)

@task
def write_config(build, filename, content, mapping_file=None):
    # We hang various things we shouldn't off config, this is pretty horrible
    clean_config = copy(build.config)
    if 'json' in clean_config:
        clean_config.pop('json')
    if 'android_sdk_dir' in clean_config:
        clean_config.pop('android_sdk_dir')

    if mapping_file is None:
        module_mapping = {}
    else:
        with open(mapping_file) as mapping_fileobj:
            module_mapping = json.load(mapping_fileobj)

    content = utils.render_string({
        'config': json.dumps(clean_config, indent=4, sort_keys=True),
        'module_mapping': json.dumps(module_mapping, indent=4, sort_keys=True)
    }, content)

    with open(filename, 'w') as fileobj:
        fileobj.write(content)

@task
def find_and_replace_in_dir(build, root_dir, find, replace, file_suffixes=("html",), template=False, **kw):
    'For all files ending with one of the suffixes, under the root_dir, replace ``find`` with ``replace``'
    if template:
        replace = utils.render_string(build.config, replace)

    build.log.debug("replacing {find} with {replace} in {files}".format(
            find=find, replace=replace, files="{0}/**/*.{1}".format(root_dir, file_suffixes)
    ))

    found_roots = glob.glob(root_dir)
    if len(found_roots) == 0:
        build.log.warning('No files were found to match pattern "%s"' % root_dir)
    for found_root in found_roots:
        for root, _, files, depth in walk_with_depth(found_root):
            for file_ in files:
                if file_.rpartition('.')[2] in file_suffixes:
                    find_with_fixed_path = find.replace("%{back_to_parent}%", "../" * (depth+1))
                    replace_with_fixed_path = replace.replace("%{back_to_parent}%", "../" * (depth+1))
                    _replace_in_file(build, path.join(root, file_), find_with_fixed_path, replace_with_fixed_path)

def _replace_in_file(build, filename, find, replace):
    build.log.debug(u"replacing {find} with {replace} in {filename}".format(**locals()))

    tmp_file = uuid.uuid4().hex
    in_file_contents = read_file_as_str(filename)
    in_file_contents = in_file_contents.replace(find, replace)
    with codecs.open(tmp_file, 'w', encoding='utf8') as out_file:
        out_file.write(in_file_contents)
    os.remove(filename)
    shutil.move(tmp_file, filename)

@task
def remove_lines_in_file(build, filename, containing):
    build.log.debug("removing lines containing '{containing}' in {filename}".format(**locals()))

    tmp_file = uuid.uuid4().hex
    in_file_contents = read_file_as_str(filename)
    in_file_contents = re.sub(r".*"+re.escape(containing)+r".*\r?\n?", "", in_file_contents)
    with codecs.open(tmp_file, 'w', encoding='utf8') as out_file:
        out_file.write(in_file_contents)
    os.remove(filename)
    shutil.move(tmp_file, filename)

@task
def regex_replace_in_file(build, filename, find, replace, template=False):
    build.log.debug("regex replace in {filename}".format(**locals()))

    if template:
        replace = utils.render_string(build.config, replace)

    tmp_file = uuid.uuid4().hex
    in_file_contents = read_file_as_str(filename)
    in_file_contents = re.sub(find, replace, in_file_contents)
    with codecs.open(tmp_file, 'w', encoding='utf8') as out_file:
        out_file.write(in_file_contents)
    os.remove(filename)
    shutil.move(tmp_file, filename)

@task
def set_in_biplist(build, filename, key, value):
    # biplist import must be done here, as in the server context, biplist doesn't exist
    import biplist

    if isinstance(value, str) or isinstance(value, unicode):
        value = utils.render_string(build.config, value)

    build.log.debug(u"setting {key} to {value} in {files}".format(
            key=key, value=value, files=filename
    ))

    found_files = glob.glob(filename)
    if len(found_files) == 0:
        build.log.warning('No files were found to match pattern "%s"' % filename)
    for found_file in found_files:
        plist = biplist.readPlist(found_file)
        plist = utils.transform(plist,
                                key,
                                lambda x: x + value if (isinstance(x, list) and isinstance(value, list)) else value,
                                allow_set=True)
        biplist.writePlist(plist, found_file)

@task
def set_in_info_plist(build, key, value):
    set_in_biplist(build, "ios/app/ForgeInspector/ForgeInspector-Info.plist", key, value)

@task
def set_in_json(build, filename, key, value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = utils.render_string(build.config, value)

    build.log.debug("setting {key} to {value} in {files}".format(
            key=key, value=value, files=filename
    ))

    found_files = glob.glob(filename)
    if len(found_files) == 0:
        build.log.warning('No files were found to match pattern "%s"' % filename)
    for found_file in found_files:
        file_json = {}
        with open(found_file, "r") as opened_file:
            file_json = json.load(opened_file)
            # TODO: . separated keys?
            file_json[key] = value
        with open(found_file, "w") as opened_file:
            json.dump(file_json, opened_file, indent=2, sort_keys=True)

@task
def set_in_config(build, key, value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = utils.render_string(build.config, value)

    build.log.debug("Setting {key} to {value} in app_config.json".format(key=key, value=value))

    key = key.split(".")
    last = key.pop()
    at = build.config
    for part in key:
        if not part in at or not isinstance(at[part], dict):
            at[part] = {}
        at = at[part]

    at[last] = value

@task
def add_to_json_array(build, filename, key, value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = utils.render_string(build.config, value)

    build.log.debug("adding '{value}' to '{key}' in {files}".format(
            key=key, value=value, files=filename
    ))

    found_files = glob.glob(filename)
    if len(found_files) == 0:
        build.log.warning('No files were found to match pattern "%s"' % filename)
    for found_file in found_files:
        file_json = {}
        with open(found_file, "r") as opened_file:
            file_json = json.load(opened_file)
            # TODO: . separated keys?
            file_json[key].append(value)
        with open(found_file, "w") as opened_file:
            json.dump(file_json, opened_file, indent=2, sort_keys=True)

@task
def resolve_urls(build, *url_locations):
    '''Include "src" prefix for relative URLs, e.g. ``file.html`` -> ``src/file.html``

    ``url_locations`` uses::

    * dot-notation to descend into a dictionary
    * ``[]`` at the end of a field name to denote an array
    * ``*`` means all attributes on a dictionary
    '''
    def resolve_url_with_uuid(url):
        return utils._resolve_url(build.config, url, 'src')
    for location in url_locations:
        build.config = utils.transform(build.config, location, resolve_url_with_uuid)

@task
def wrap_activations(build, location):
    '''Wrap user activation code to prevent running in frames if required

    '''
    if "activations" in build.config['modules'] and \
       "config" in build.config['modules']['activations'] and \
       "activations" in build.config['modules']['activations']['config']:
        for activation in build.config['modules']['activations']['config']['activations']:
            if not 'all_frames' in activation or activation['all_frames'] is False:
                for script in activation['scripts']:
                    tmp_file = uuid.uuid4().hex
                    filename = location+script[3:]
                    build.log.debug("wrapping activation {filename}".format(**locals()))
                    in_file_contents = read_file_as_str(filename)
                    in_file_contents = 'if (forge._disableFrames === undefined || window.location == window.parent.location) {\n'+in_file_contents+'\n}';
                    with codecs.open(tmp_file, 'w', encoding='utf8') as out_file:
                        out_file.write(in_file_contents)
                    os.remove(filename)
                    shutil.move(tmp_file, filename)

@task
def populate_icons(build, platform, icon_list):
    '''
    adds a platform's icons to a build config.
    platform is a string platform, eg. "android"
    icon_list is a list of string dimensions, eg. [36, 48, 72]
    '''
    if "icons" in build.config["modules"] and "config" in build.config["modules"]["icons"]:
        if not platform in build.config["modules"]["icons"]["config"]:
            build.config["modules"]["icons"]["config"][platform] = {}
        for icon in icon_list:
            str_icon = str(icon)
            if not str_icon in build.config["modules"]["icons"]["config"][platform]:
                try:
                    build.config["modules"]["icons"]["config"][platform][str_icon] = \
                            build.config["modules"]["icons"]["config"][str_icon]
                except KeyError:
                    build.log.warning('missing icon "%s" for platform "%s"' % (str_icon, platform))
    else:
        pass #no icons is valid, though it should have been caught priorly.

@task
def run_hook(build, **kw):
    for file in sorted(os.listdir(os.path.join('hooks', kw['hook']))):
        if os.path.isfile(os.path.join('hooks', kw['hook'], file)):
            cwd = os.getcwd()
            os.chdir(kw['dir'])

            target = iter(build.enabled_platforms).next()

            # Get the extension
            ext = os.path.splitext(file)[-1][1:]

            proc = None
            if ext == "py":
                build.log.info('Running (Python) hook: '+file)
                proc = lib.PopenWithoutNewConsole(["python", os.path.join(cwd, 'hooks', kw['hook'], file), target])
            elif ext == "js":
                build.log.info('Running (node) hook: '+file)
                proc = lib.PopenWithoutNewConsole(["node", os.path.join(cwd, 'hooks', kw['hook'], file), target])
            elif ext == "bat" and sys.platform.startswith('win'):
                build.log.info('Running (Windows Batch file) hook: '+file)
                proc = lib.PopenWithoutNewConsole([os.path.join(cwd, 'hooks', kw['hook'], file), target])
            elif ext == "sh" and not sys.platform.startswith('win'):
                build.log.info('Running (shell) hook: '+file)
                proc = lib.PopenWithoutNewConsole([os.path.join(cwd, 'hooks', kw['hook'], file), target])

            if proc != None:
                proc.wait()

            os.chdir(cwd)

            if proc != None and proc.returncode != 0:
                raise ConfigurationError('Hook script exited with a non-zero return code.')

@task
def remove_files(build, *removes):
    build.log.info('deleting %d files' % len(removes))
    for rem in removes:
        real_rem = utils.render_string(build.config, rem)
        build.log.debug('deleting %s' % real_rem)
        if path.isfile(real_rem):
            os.remove(real_rem)
        else:
            shutil.rmtree(real_rem, ignore_errors=True)

@task
def populate_package_names(build):
    if "core" not in build.config:
        build.config["core"] = {}
    if "android" not in build.config["core"]:
        build.config["core"]["android"] = {}
    build.config["core"]["android"]["package_name"] = android_tasks._generate_package_name(build)
    if "ios" not in build.config["core"]:
        build.config["core"]["ios"] = {}
    build.config["core"]["ios"]["package_name"] = ios_tasks._generate_package_name(build)
    if "osx" not in build.config["core"]:
        build.config["core"]["osx"] = {}
    build.config["core"]["osx"]["package_name"] = osx_tasks._generate_package_name(build)

@task
def populate_trigger_domain(build):
    try:
        from forge import build_config
        config = build_config.load()
        build.config['trigger_domain'] = config['main']['server'][:-5]
    except ImportError:
        build.config['trigger_domain'] = "TRIGGER_DOMAIN_HERE"

    if not "config_hash" in build.config:
        build.config['config_hash'] = "CONFIG_HASH_HERE"

@task
def make_dir(build, dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    build.log.debug("make_dir %s - skipping, directory already exists" % dir)

@task
def generate_sha1_manifest(build, input_folder, output_file):
    with open(output_file, 'w') as out:
        manifest = dict()
        for root, dirs, files in os.walk(input_folder):
            for filename in files:
                filename = os.path.join(root, filename)
                with open(filename, 'rb') as file:
                    hash = hashlib.sha1(file.read()).hexdigest()
                    manifest[hash] = filename[len(input_folder)+1:].replace('\\','/')
        json.dump(manifest, out, ensure_ascii=False)

@task
def check_index_html(build, src='src'):
    index_path = os.path.join(src, 'index.html')
    if not os.path.isfile(index_path):
        raise Exception("Missing index.html in source directory, index.html is required by Forge.")

    with open(index_path) as index_file:
        index_html = index_file.read()

        if index_html.find("<head>") == -1:
            raise Exception("index.html does not contain '<head>', this is required to add the Forge javascript library.")

@task
def run_module_build_steps(build, steps_path, src_path, project_path):
    if not os.path.isdir(steps_path):
        return

    modules = os.listdir(steps_path)
    for module in modules:
        build.log.debug("Running local build steps for: %s" % module)
        with open(os.path.join(steps_path, module), 'r') as module_steps_file:
            module_steps = json.load(module_steps_file)
            for step in module_steps:
                # XXX: only supports dict of args, could be better?
                build_params = {}
                build_params['app_config'] = build.config
                build_params['project_path'] = project_path
                build_params['src_path'] = src_path

                if "when" in step:
                    should_continue = False
                    for predicate in step["when"]:
                        predicate_func = getattr(build_steps_predicates, predicate, None)
                        if predicate_func is not None:
                            if not utils.call_with_params(predicate_func, build_params, step["when"][predicate]):
                                should_continue = True
                                break
                        else:
                            should_continue = True
                            break
                    if should_continue:
                        continue

                if "do" in step:
                    for task in step['do']:
                        task_func = getattr(build_steps_local, task, None)
                        if task_func is not None:
                            task_func(build_params, **step["do"][task])

@task
def merge_resources(build, **kw):
    if 'from' not in kw or 'to' not in kw:
        raise ConfigurationError('merge_resources requires "from" and "to" keyword arguments')
    root_src_dir = kw['from']
    root_dst_dir = kw['to']
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file) and dst_file.endswith('.xml'):
                build.log.info("App resource filename '%s' already exists. Merging into '%s'." % (src_file, dst_file))
                merged = _merge_android_resources((src_file, dst_file))
                with open(dst_file, 'w') as f:
                    f.write(merged)
            elif os.path.exists(dst_file):
                build.log.warn("App resource filename '%s' already exists: '%s'. Skipping file." % (src_file, dst_file))
            else:
                shutil.copy(src_file, dst_file)

# Unfortunately we cannot rely on the right version of module_dynamic.utils to be present
def _merge_android_resources(filenames):
    assert len(filenames) > 0, 'No filenames!'
    roots = [ElementTree.parse(f).getroot() for f in filenames]
    for r in roots[1:]:
        roots[0].extend(r)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ElementTree.tostring(roots[0])


@task
def android_set_min_sdk_version(build, gradle_json, value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = utils.render_string(build.config, value)
    gradle = {}
    if os.path.exists(gradle_json):
        with open(gradle_json) as f:
            gradle = json.load(f)
    if not "minSdkVersion" in gradle.keys():
        gradle["minSdkVersion"] = value
    elif "minSdkVersion" in gradle.keys() and int(value) > int(gradle["minSdkVersion"]):
        gradle["minSdkVersion"] = value

    with open(gradle_json, "w") as f:
        json.dump(gradle, f, indent=4, sort_keys=True)


@task
def android_set_gradle_json(build, gradle_json, key, value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = utils.render_object(build.config, value)
    if value is None:
        build.log.error("android_set_gradle_json failed to set key '%s'")
        return
    gradle = {}
    if os.path.exists(gradle_json):
        with open(gradle_json) as f:
            gradle = json.load(f)
    if not key in gradle.keys():
        gradle[key] = value
    else:
        gradle[key] = value

    with open(gradle_json, "w") as f:
        json.dump(gradle, f, indent=4, sort_keys=True)


@task
def inject_local_assets(build):
    """only ever run from forge-generate"""
    import buildtools
    assets_url = buildtools.inject_local_assets(log=build.log,
                                                target=iter(build.enabled_platforms).next(),
                                                config=build.config,
                                                build_usercode=build.usercode,
                                                build_userassets=build.userassets,
                                                remote=None,
                                                build=build)
