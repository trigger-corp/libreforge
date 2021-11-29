import sys
import os
from os import path
import shutil
import subprocess
import tempfile
import zipfile
import argparse
import logging
import json

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)7s] %(asctime)s -- %(message)s')
log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Generate a new Forge app')
    parser.add_argument('--temp', help='directory to use for temporary files (default system generated)', default=None)
    parser.add_argument('-t', '--target', help='target to build (an-inspector or ios-inspector)')
    parser.add_argument('-z', '--modules_folder', default='../modules', help='Location of modules to generate app from')
    parser.add_argument('-m', '--module', help='module to build for (e.g. prefs)')
    parser.add_argument('--system_config', help='configuration file for this system. defaults to system_config.json. see generate/example_system_config.json', required=False, default='system_config.json')

    args = parser.parse_args()

    module_path = os.path.abspath(os.path.join(os.getcwd(), args.modules_folder, args.module))
    log.info("Module path: {}".format(module_path))

    # Read the (optional) system config and merge it with the user config.
    system_config = {}
    if path.isfile(args.system_config):
        with open(args.system_config) as system_conf_file:
            system_config = json.load(system_conf_file)
            log.debug('read system config file from %s' % args.system_config)
        if len(system_config) == 0:
            log.error("no config options read from the system config file")

    platform_source_location = os.path.abspath(os.path.join(__file__, '..', '..', '..'))
    log.info("Setting up environment variable to find platform in {}".format(platform_source_location))
    os.environ['FORGE_PLATFORM_LOCATION'] = platform_source_location

    if os.path.exists(os.path.join(module_path, '.trigger')):
        shutil.rmtree(os.path.join(module_path, '.trigger'))

    log.info("Copying module dynamic to .trigger")
    shutil.copytree(os.path.join(os.getcwd(), 'module'), os.path.join(module_path, '.trigger'))

    log.info("Writing fake platform version")
    with open(os.path.join(module_path, '.trigger', 'platform_version.txt'), 'w') as platform_version:
        platform_version.write("__local__")

    log.info("Generating inspector project")

    # Generate inspector
    tempdir = tempfile.mkdtemp()

    if args.temp:
        command  = ['forge-generate', '--temp', args.temp, '--platforms', args.target, '-r', '-v', '-u', 'test-apps/inspector', '-o', tempdir, 'build']
    else:
        command  = ['forge-generate', '--platforms', args.target, '-r', '-v', '-u', 'test-apps/inspector', '-o', tempdir, 'build']

    subprocess.call(command, stdout=sys.stdout, stderr=sys.stderr)

    if not os.path.exists(os.path.join(module_path, '.trigger', 'cache')):
        os.mkdir(os.path.join(module_path, '.trigger', 'cache'))

    log.info("Zipping inspector project into module_dynamic")
    # Put inspector in "cache"
    with zipfile.ZipFile(os.path.join(module_path, '.trigger', 'cache', args.target+".zip"), 'w') as zip:
        source = os.path.join(tempdir, 'development')
        shutil.rmtree(os.path.join(source, 'reload'))
        rootlen = len(source) + 1
        for base, dirs, files in os.walk(source):
            for file in files:
                fn = os.path.join(base, file)
                zip.write(fn, fn[rootlen:])

    shutil.rmtree(tempdir)

    sys.path.append(os.path.join(module_path, '.trigger', 'module_dynamic'))

    log.info("Importing module dynamic")
    import inspector

    log.info("Updating inspector")
    if args.target == 'ios-inspector':
        inspector.update_ios({}, {}, system_config=system_config)
    elif args.target == 'an-inspector':
        inspector.update_android({}, {}, system_config=system_config)
    elif args.target == 'osx-inspector':
        inspector.update_osx({})

    log.info("Removing .trigger")
    if os.path.exists(os.path.join(module_path, '.trigger')):
        shutil.rmtree(os.path.join(module_path, '.trigger'))

if __name__ == '__main__':
    main()
