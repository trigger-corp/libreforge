import glob
import json
import os
from os import path
import sys
import shutil
import subprocess
from subprocess import PIPE, STDOUT
import zipfile
import uuid
import requests
import time
from copy import copy

from genshi.template import NewTextTemplate, TemplateLoader

from module_dynamic import utils
from build import ConfigurationError
from lib import task
import minify
import module_dynamic.build as module_dynamic_build

xcode_version="/opt/xcode/13.0/Xcode-beta.app"

_platform_dir_map = {
    'android': 'development/android',
    'ios': 'development/ios',
    'osx': 'development/osx',
    'web': 'development/web',
    'an-inspector': 'development/an-inspector',
    'ios-inspector': 'development/ios-inspector',
    'osx-inspector': 'development/osx-inspector',
    'ios-native': 'development/ios-native',
}

def _call_with_params(method, build_params, params):
    if isinstance(params, dict):
        return method(build_params, **params)
    elif isinstance(params, tuple):
        return method(build_params, *params)
    else:
        return method(build_params, params)

def _urlretrieve(url, destination):
    """replacement for urllib.urlretrieve that hopefully does not hang randomly on macOS"""
    response = requests.get(url, stream=True, timeout=30)
    print "downloading %s to '%s'" % (url, destination)
    with open(destination, "wb") as f:
        for chunk in response.iter_content(4096):
            f.write(chunk)
    # https://blog.petrzemek.net/2018/04/22/on-incomplete-http-reads-and-the-requests-library-in-python/
    expected_length = response.headers.get('Content-Length')
    if expected_length is not None:
        actual_length = response.raw.tell()
        expected_length = int(expected_length)
        if actual_length < expected_length:
            raise IOError('server_tasks._urlretrieve: incomplete read ({} bytes read, {} more expected)'.format(actual_length, expected_length - actual_length))


@task
def preprocess_config(build):
    '''
    preprocess config
    '''
    build.log.info('preprocessing configuration')

    # Add a UUID to config.json if not already got one.
    if 'uuid' not in build.config:
        build.config['uuid'] = str(uuid.uuid4())
        build.log.warning('generated new UUID: %s' % build.config['uuid'])

@task
def need_https_access(build):
    'If any activation has a HTTPS prefix, set the "activate_on_https" config flag'
    def pattern_needs_https(pat):
        return (
                pat == "<all_urls>" or
                pat.startswith("*") or
                pat.startswith("https")
        )
    def activation_needs_https(act):
        return any(pattern_needs_https(pat) for pat in act.get("patterns", []))

    build.config["activate_on_https"] = any(
            pattern_needs_https(pat) for pat in build.config["modules"]
                    .get("request", {})
                    .get("config", {})
                    .get("permissions", [])
    ) or any(
            activation_needs_https(act) for act in build.config["modules"]
                    .get("activations", {}).get("config", {}).get("activations", [])
    )

@task
def minify_in_place(build, *files):
    '''Minify a JS or CSS file, without renaming it.
    '''
    real_files = [utils.render_string(build.config, f) for f in files]
    minify.minify_in_place(build.source_dir, *real_files)

@task
def addon_source(build, *directories):
    for d in directories:
        from_to = (path.join(build.source_dir, d), d)
        if os.path.isdir(from_to[0]):
            build.log.info('copying source directory %s to %s' % from_to)
            shutil.copytree(*from_to, symlinks=True)
        else:
            build.log.info('copying source file %s to %s' % from_to)
            shutil.copy(*from_to)

@task
def user_source(build, directory):
    from_to = (build.usercode, directory)
    build.log.debug('copying source directory "%s" to "%s"' % from_to)
    shutil.copytree(*from_to)

@task
def concatenate_files(build, **kw):
    if 'in' not in kw or 'out' not in kw:
        raise ConfigurationError('concatentate_files requires "in" and "out" keyword arguments')

    with open(kw['out'], 'a') as out_file:
        for frm in kw['in']:
            if not path.isfile(frm):
                raise Exception("not a file: " + frm)
            build.log.debug('concatenating %s to %s' % (frm, kw['out']))
            with open(frm) as in_file:
                out_file.write(in_file.read())
            build.log.info('appended %s to %s' % (frm, kw['out'],))

@task
def add_to_all_js(build, file):
    all_js_paths = {
        'ios': ('ios/app/ForgeInspector/assets/forge/all.js',),
        'ios-native': ('ios/native/ForgeInspector/assets/forge/all.js',),
        'osx': ('osx/app/ForgeInspector/assets/forge/all.js',),
        'ios-inspector': ('ios/inspector/ForgeInspector/assets/forge/all.js',),
        'osx-inspector': ('osx/ForgeInspector/ForgeInspector/assets/forge/all.js',),
        'android': ('android/ForgeInspector/assets/forge/all.js',),
        'an-inspector': ('android/ForgeInspector/assets/forge/all.js',),
        'web': ('web/forge/all.js',),
    }
    for platform in build.enabled_platforms:
        if not platform in all_js_paths:
            continue
        for out in all_js_paths[platform]:
            kw = {
                    'in': (file,),
                    'out': out
            }
            concatenate_files(build, **kw)

@task
def extract_files(build, **kw):
    if 'from' not in kw or 'to' not in kw:
        raise ConfigurationError('extract_files requires "from" and "to" keyword arguments')

    build.log.debug('Extracting %s to %s' % (utils.render_string(build.config, kw['from']), utils.render_string(build.config, kw['to'])))
    zipf = zipfile.ZipFile(utils.render_string(build.config, kw['from']))
    zipf.extractall(utils.render_string(build.config, kw['to']))
    zipf.close()

@task
def fallback_to_default_toolbar_icon(build):
    if "button" not in build.config["modules"] or "config" not in build.config["modules"]["button"] or "default_icon" in build.config["modules"]["button"]["config"]:
        # don't need to worry about toolbar icons
        return
    # no default icon given in browser_action section
    build.log.debug("moving default toolbar icon into place")
    shutil.copytree("common-v2/graphics", "common-v2/forge/graphics")

    build.log.debug("settings browser_action.default_icon")
    build.config["modules"]["button"]["config"]["default_icon"] = "forge/graphics/icon16.png"

@task
def template_files(build, *files):
    '''apply genshi templating to files in place'''
    build.log.info('applying templates to %d files' % (len(files)))

    # Terrible hack, but at least if we do it here we don't end up with json attached to build.config
    config = copy(build.config)
    config['json'] = json

    for glob_str in files:
        found_files = glob.glob(glob_str)
        if len(found_files) == 0:
            build.log.warning('No files were found to match pattern "%s"' % glob_str)
        for _file in found_files:
            build.log.debug('templating %s' % _file)
            loader = TemplateLoader(path.dirname(_file))
            tmpl = loader.load(path.basename(_file), cls=NewTextTemplate)
            stream = tmpl.generate(**config)
            tmp_file = _file+'-tmp'
            with open(tmp_file, 'w') as out_file:
                out_file.write(stream.render('text'))
            from_to = (tmp_file, _file)
            shutil.move(*from_to)

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
def move_output(build, *output_dirs):
    for output_dir in output_dirs:
        to = path.join(build.output_dir, output_dir)
        build.log.debug("moving {0} to {1}".format(output_dir, to))
        shutil.move(output_dir, to)

@task
def move_debug_output(build, platform):
    to = path.join(build.output_dir, 'debug')
    build.log.debug("moving {0} to {1}".format(platform, to))
    shutil.move(platform, to)

@task
def remember_build_output_location(build):
    for platform in build.enabled_platforms:
        # build.unpackaged is used to locate output after build is complete,
        # when running embedded
        build.unpackaged[platform] = _platform_dir_map[platform]

# TODO lose this
@task
def ant_build(build, new_working_dir, scheme='partial'):
    original_dir = os.getcwd()

    try:
        build.log.debug('changing dir to do Ant: %s, was in %s' % (new_working_dir, original_dir))
        os.chdir(new_working_dir)

        env = copy(os.environ)
        env['ANDROID_HOME'] = build.system_config['android_sdk_dir']

        build.log.debug('running: ant %s' % scheme)
        sys.exit(-1)
        if sys.platform.startswith('win'):
            ant = subprocess.Popen(['ant.bat', scheme], stdout=PIPE, stderr=STDOUT)
        else:
            ant = subprocess.Popen(['ant', scheme], stdout=PIPE, stderr=STDOUT)
        out = ant.communicate()[0]
        if ant.returncode != 0:
            build.log.error('ant build error: %s' % out)
            raise Exception('ant build error')
        else:
            build.log.debug('ant build output: %s' % out)
    finally:
        os.chdir(original_dir)


@task
def gradle_build(build, new_working_dir, scheme):
    original_dir = os.getcwd()

    try:
        build.log.debug('changing dir to perform gradle build: %s, was in %s' % (new_working_dir, original_dir))
        os.chdir(new_working_dir)

        gradle_home = '/mnt/gradle/gradle-6.7.1'
        gradle_cmd = '%s/bin/gradle' % gradle_home

        env = copy(os.environ)
        env['ANDROID_HOME'] = build.system_config['android_sdk_dir']
        env['GRADLE_HOME'] = gradle_home

        build.log.debug('running: gradle %s %s' % (gradle_cmd, scheme))

        cmd = [ gradle_cmd, scheme, '-x', 'lint', '--console', 'plain' ]
        gradle = subprocess.Popen(cmd, stdout=PIPE, stderr=STDOUT)
        out = gradle.communicate()[0]
        if gradle.returncode != 0:
            build.log.error('gradle build error: %s' % out)
            raise Exception('gradle build error')
        else:
            build.log.debug('gradle build output: %s' % out)
    finally:
        os.chdir(original_dir)

@task
def android_copy_native_libs(build, dir): # TODO do we still need this for backwards compatibility?
    src = os.path.join(dir, 'libs')
    dst = os.path.join(dir, 'lib')
    if not os.path.isdir(src):
        return
    if not os.path.exists(dst):
        os.mkdir(dst)
    for dirpath, dirnames, filenames in os.walk(src):
        for dirname in dirnames:
            os.rename(os.path.join(src, dirname), os.path.join(dst, dirname))


@task
def provision_assets(build, destination):
    # if remote build, grab url from db & download assets from s3 to assets.zip
    if build.is_remote:
        archive = "assets.zip"
        assets_url = build.config["assets_url"]
        build.log.debug("Retrieving remote user assets archive: %s", assets_url)
        if assets_url is None:
            build.log.debug("No remote user assets archive for this build. Skipping.")
            return
        _urlretrieve(assets_url, archive)
    else:
        build.log.debug("Retrieving local user assets archive: %s", build.userassets)
        archive = os.path.basename(build.userassets)

    if not os.path.exists(archive):
        build.log.debug("No user assets folder found")
        return

    # unzip assets archive
    build.log.debug("Extracting assets archive '%s' to '%s'" % (archive, destination))
    zipf = zipfile.ZipFile(archive)
    zipf.extractall(destination)
    zipf.close()
    os.remove(archive)


def xcode_cmd(build, cmd, xcconfig=None):
    build.log.debug('running xcode command: "%s"' % (cmd))

    environment = os.environ.copy()
    if xcconfig is not None:
        environment["XCODE_XCCONFIG_FILE"] = xcconfig

    xcode = subprocess.Popen(cmd, stdout=PIPE, stderr=STDOUT, env=environment)
    out = xcode.communicate()[0]
    if xcode.returncode != 0:
        build.log.error('Xcode error:')
        while out:
            build.log.error(out[:100000])
            out = out[100000:]
        raise Exception('Xcode error')

@task
def xcode_build(build, source_dir):
    original_dir = os.getcwd()
    source_dir = path.abspath(source_dir)
    build_dir = path.join(source_dir, 'build')
    dist_dir = path.join(source_dir, 'dist')
    device_build_file = path.join(build_dir, 'Release-iphoneos', 'ForgeInspector.app')
    sim_build_file = path.join(build_dir, 'Release-iphonesimulator', 'ForgeInspector.app')

    # workaround for xcode building arm64 targets for simulator in the runup to Apple Silicon
    # also see: https://github.com/Carthage/Carthage/issues/3019
    xcconfig = os.path.abspath("%s/fix_simulator_arch.xcconfig" % source_dir)

    if not path.isdir(dist_dir):
        build.log.warning('creating iOS directory "%s"' % dist_dir)
        os.mkdir(dist_dir)

    sim_build_cmd = [
        "%s/Contents/Developer/usr/bin/xcodebuild" % xcode_version,
        '-sdk', 'iphonesimulator',
        '-configuration', 'Release',
        'EXECUTABLE_NAME=Forge'
    ]
    device_build_cmd = [
        "%s/Contents/Developer/usr/bin/xcodebuild" % xcode_version,
        '-sdk', 'iphoneos',
        '-configuration', 'Release',
        'EXECUTABLE_NAME=Forge'
    ]
    try:
        build.log.debug('changing dir to do Xcode build: %s, was in %s' % (source_dir, original_dir))
        os.chdir(source_dir)
        xcode_cmd(build, sim_build_cmd, xcconfig=xcconfig)
        xcode_cmd(build, device_build_cmd, xcconfig=xcconfig)
        shutil.copytree(device_build_file, path.join(dist_dir, 'device-ios.app'))
        shutil.copytree(sim_build_file, path.join(dist_dir, 'simulator-ios.app'))
    finally:
        os.chdir(original_dir)


@task
def xcode_core_build(build, source_dir):
    original_dir = os.getcwd()
    source_dir = path.abspath(source_dir)
    build_dir = path.join(source_dir, 'build')
    dist_dir = path.join(source_dir, 'dist')
    framework_build_file = path.join(build_dir, 'Debug-iphoneos', 'ForgeCore.framework')
    bundle_build_file = path.join(build_dir, 'Debug-iphoneos', 'ForgeCore.bundle')

    # workaround for xcode building arm64 targets for simulator in the runup to Apple Silicon
    # also see: https://github.com/Carthage/Carthage/issues/3019
    xcconfig = os.path.abspath("%s/fix_simulator_arch.xcconfig" % source_dir)

    if not path.isdir(dist_dir):
        build.log.warning('creating iOS directory "%s"' % dist_dir)
        os.mkdir(dist_dir)

    build_cmd = [
        "%s/Contents/Developer/usr/bin/xcodebuild" % xcode_version,
        '-target', 'Framework',
        '-configuration', 'Debug',
    ]
    try:
        build.log.debug('changing dir to do Xcode build: %s, was in %s' % (source_dir, original_dir))
        os.chdir(source_dir)

        xcode_cmd(build, build_cmd, xcconfig=xcconfig)
        shutil.copytree(framework_build_file, path.join(dist_dir, 'ForgeCore.framework'))
        shutil.copytree(bundle_build_file, path.join(dist_dir, 'ForgeCore.bundle'))
    finally:
        os.chdir(original_dir)

@task
def xcode_osx_core_build(build, source_dir):
    original_dir = os.getcwd()
    source_dir = path.abspath(source_dir)
    build_dir = path.join(source_dir, 'build')
    dist_dir = path.join(source_dir, 'dist')
    framework_build_file = path.join(build_dir, 'Debug', 'ForgeCore.framework')

    if not path.isdir(dist_dir):
        build.log.warning('creating iOS directory "%s"' % dist_dir)
        os.mkdir(dist_dir)

    build_cmd = [
        "%s/Contents/Developer/usr/bin/xcodebuild" % xcode_version,
        '-configuration', 'Debug',
    ]
    try:
        build.log.debug('changing dir to do Xcode build: %s, was in %s' % (source_dir, original_dir))
        os.chdir(source_dir)

        xcode_cmd(build, build_cmd)
        # TODO: This duplicates symlinked files, fix?
        shutil.copytree(framework_build_file, path.join(dist_dir, 'ForgeCore.framework'), symlinks=True)
    finally:
        os.chdir(original_dir)

@task
def xcode_osx_build(build, source_dir):
    original_dir = os.getcwd()
    source_dir = path.abspath(source_dir)
    build_dir = path.join(source_dir, 'build')
    dist_dir = path.join(source_dir, 'dist')
    app_build_file = path.join(build_dir, 'Release', 'ForgeInspector.app')

    if not path.isdir(dist_dir):
        build.log.warning('creating iOS directory "%s"' % dist_dir)
        os.mkdir(dist_dir)

    build_cmd = [
        "%s/Contents/Developer/usr/bin/xcodebuild" % xcode_version,
        '-configuration', 'Release',
    ]
    try:
        build.log.debug('changing dir to do Xcode build: %s, was in %s' % (source_dir, original_dir))
        os.chdir(source_dir)

        xcode_cmd(build, build_cmd)
        shutil.copytree(app_build_file, path.join(dist_dir, 'Forge.app'), symlinks=True)
    finally:
        os.chdir(original_dir)

@task
def copy_jquery(build, **kw):
    if 'to' not in kw:
        raise ConfigurationError('copy_jquery needs "to" keyword arguments')

    _from = 'common-v2/libs/jquery/jquery-' + build.config.get('modules')['jquery']['config']['version'] + '.min.js'
    _to = utils.render_string(build.config, kw['to'])

    dir = ''
    for next_dir in _to.split('/'):
        dir += next_dir + '/'
        if not os.path.isdir(dir):
            os.mkdir(dir)

    shutil.copy(_from, _to)

def _download_and_extract_module(build, name, version):
    if os.path.exists(os.path.join('modules', name)):
        build.log.debug("module already downloaded: %s" % name)
        return
    build.log.debug("Downloading module: %s-%s" % (name, version))

    if ('module_urls' not in build.meta_config or "%s-%s" % (name, version) not in build.meta_config['module_urls']) and 'module_urls' not in build.system_config:
        raise Exception("No URL provided in meta config to download module.")

    count = 0
    while count < 5:
        try:
            if 'module_urls' in build.system_config:
                module_url = build.system_config['module_urls'] % (name, version)
            else:
                module_url = build.meta_config['module_urls']["%s-%s" % (name, version)]
            build.log.debug("\turl: %s" % module_url)
            _urlretrieve(module_url, 'modules/download')
            count = 99
        except Exception as e:
            build.log.debug("Error retrieving module %s: %s - retrying" % (name, e))
            # Retry a few times after a short sleep
            time.sleep(3)
            count = count + 1
            if count == 5:
                build.log.debug("Exceeded retry count, exiting")
                raise e

    zipf = zipfile.ZipFile('modules/download')
    zipf.extractall(os.path.join('modules', name))
    zipf.close()
    os.remove('modules/download')


@task
def download_and_extract_modules(build):
    '''Download and extract any modules to be included in this build, a module named alert will be extracted to modules/alert'''
    build.log.info("Downloading modules")

    if 'modules' in build.config:
        try:
            os.makedirs('modules')
        except OSError:
            pass

        for module in build.config['modules']:
            if "disabled" in build.config['modules'][module] and build.config['modules'][module]["disabled"]:
                continue
            if not 'version' in build.config['modules'][module]:
                continue
            if module == "httpd":
                build.log.info("Skipping integrated module: %s" % module)
                continue
            build.log.info("Downloading module: %s" % module)
            version = build.config['modules'][module]['version']
            _download_and_extract_module(build, module, version)
            build.log.info("Downloaded module: %s" % module)

            # check for, and add any dependent modules
            if not os.path.isfile(os.path.join('modules', module, 'manifest.json')):
                continue

            with open(os.path.join('modules', module, 'manifest.json')) as manifest_file:
                manifest = json.load(manifest_file)
                if 'dependencies' in manifest:
                    for name in manifest['dependencies']:
                        module = manifest['dependencies'][name]
                        if 'maximum_version' in module:
                            version = module['maximum_version']
                        else:
                            version = module['minimum_version']
                        build.log.info("Found module dependency: %s-%s" % (name, version))
                        if 'module_urls' in build.meta_config:
                            # TODO this should really be happening in website/forge/builder.py
                            build.meta_config['module_urls']['%s-%s' % (name, version)] = ('https://s3.amazonaws.com/trigger-module-build/%s/%s.zip' % (name, version))
                        _download_and_extract_module(build, name, version)

@task
def create_module_mapping(build):
    if "module_mapping" not in build.meta_config:
        # forge-generate: we need to create the module_mapping from the module files
        build.meta_config["module_mapping"] = {}
        if os.path.isdir('modules'):
            for module in os.listdir('modules'):
                if os.path.isfile(os.path.join('modules', module, 'manifest.json')):
                    with open(os.path.join('modules', module, 'manifest.json')) as manifest_file:
                        manifest = json.load(manifest_file)
                        if 'namespace' in manifest:
                            build.meta_config["module_mapping"][manifest['namespace']] = module
                        else:
                            build.meta_config["module_mapping"][module] = module

    module_mapping_paths = {
        'ios': 'ios/app/ForgeInspector/assets/module_mapping.json',
        'ios-native': 'ios/native/ForgeInspector/assets/module_mapping.json',
        'android': 'android/ForgeInspector/assets/module_mapping.json',
    }
    for platform in build.enabled_platforms:
        if platform in module_mapping_paths:
            with open(module_mapping_paths[platform], 'w') as module_mapping_file:
                json.dump(build.meta_config['module_mapping'], module_mapping_file)

@task
def add_modules_android(build):
    build.log.info("Adding android modules to build")
    if os.path.isdir('modules'):
        added_modules = set()
        while set(os.listdir('modules')) - added_modules:
            module = (set(os.listdir('modules')) - added_modules).pop()
            added_modules.add(module)

            module_dynamic_build.apply_module_to_android_project(
                    module_path=os.path.join('modules', module),
                    project_path=os.path.join("android", "ForgeInspector"),
                    app_config=build.config
            )

@task
def add_modules_osx(build):
    build.log.info("Adding osx modules to build")
    if os.path.isdir('modules'):
        added_modules = set()
        while set(os.listdir('modules')) - added_modules:
            module = (set(os.listdir('modules')) - added_modules).pop()
            added_modules.add(module)

            module_dynamic_build.apply_module_to_osx_project(
                    module_path=os.path.join('modules', module),
                    project_path=os.path.join("osx", "app"),
                    app_config=build.config
            )

@task
def add_modules_ios(build):
    build.log.info("Adding ios modules to build")
    if os.path.isdir('modules'):
        added_modules = set()
        while set(os.listdir('modules')) - added_modules:
            module = (set(os.listdir('modules')) - added_modules).pop()
            added_modules.add(module)

            module_dynamic_build.apply_module_to_ios_project(
                    module_path=os.path.join('modules', module),
                    project_path=os.path.join("ios", "app"),
                    app_config=build.config
            )

@task
def add_modules_ios_native(build):
    build.log.info("Adding ios modules to build")
    if os.path.isdir('modules'):
        added_modules = set()
        while set(os.listdir('modules')) - added_modules:
            module = (set(os.listdir('modules')) - added_modules).pop()
            added_modules.add(module)

            module_dynamic_build.apply_module_to_ios_project(
                    module_path=os.path.join('modules', module),
                    project_path=os.path.join("ios", "native"),
                    app_config=build.config
            )

@task
def prepare_module_override(build):
    from_to = (os.path.abspath(os.path.join(build.source_dir, build.override_modules)), 'modules')
    build.log.info('copying source directory %s to %s' % from_to)
    shutil.copytree(*from_to, symlinks=True)

    modules = os.listdir('modules')
    for module in modules:
        if module.startswith('.'):
            continue

        if module not in build.config['modules']:
            shutil.rmtree(os.path.join('modules', module))
            continue

        for path in os.listdir(os.path.join('modules', module)):
            if path == 'module' or path.startswith('.'):
                continue
            shutil.rmtree(os.path.join('modules', module, path))

        for path in os.listdir(os.path.join('modules', module, 'module')):
            if path.startswith('.'):
                continue
            os.rename(os.path.join('modules', module, 'module', path), os.path.join('modules', module, path))
