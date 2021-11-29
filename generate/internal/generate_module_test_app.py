import logging
import argparse
import shutil
import os
import json
from copy import deepcopy

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

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)7s] %(asctime)s -- %(message)s')
log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Generate a new Forge app')
    parser.add_argument('-o', '--output', default='generated', help='Location to put the generated app')
    parser.add_argument('-z', '--modules_folder', default='../modules', help='Location of modules to generate app from')
    parser.add_argument('-t', '--type', default='automated', help='Type of tests to include (either automated or interactive)')
    parser.add_argument('modules', nargs='+', help='A list of modules to include in the test app (or all for all modules)')

    args = parser.parse_args()

    if os.path.exists(args.output):
        log.info("Removing existing output folder")
        shutil.rmtree(args.output)

    log.info("Copying template test app to output folder")
    shutil.copytree(os.path.join('test-apps', 'module'), args.output)

    if not os.path.isdir(os.path.join(args.output, 'tests')):
        os.makedirs(os.path.join(args.output, 'tests'))

    if not os.path.isdir(os.path.join(args.output, 'fixtures')):
        os.makedirs(os.path.join(args.output, "fixtures"))

    with open(os.path.join(args.output, 'config.json')) as app_config_file:
        app_config = json.load(app_config_file)

    if "all" in args.modules:
        modules = os.listdir(args.modules_folder)
        modules = filter(lambda x: x.endswith(".git"), modules)
        modules = sorted(modules)
    else:
        modules = args.modules

    log.info("Processing modules: %s" % modules)
    for module in modules:
        if module.startswith(".") or not os.path.exists(os.path.join(args.modules_folder, module, "module", "manifest.json")):
            continue
        if not os.path.exists(os.path.join(args.modules_folder, module)):
            log.error("Missing module: %s" % module)
            return

        manifest = {}
        module_name = module
        with open(os.path.join(args.modules_folder, module, "module", "manifest.json")) as module_manifest_file:
            manifest = json.load(module_manifest_file)
            if "namespace" in manifest:
                module_name = manifest["namespace"]
            elif "name" in manifest:
                module_name = manifest["name"]

        if os.path.exists(os.path.join(args.modules_folder, module, "module", "tests", "%s.js" % args.type)):
            log.info("Copying tests for module: %s" % module_name)
            shutil.copy2(os.path.join(args.modules_folder, module, "module", "tests", "%s.js" % args.type), os.path.join(args.output, 'tests', '%s.js' % module_name))
        else:
            log.warn("Module has no %s tests: %s" % (args.type, module_name))

        if os.path.exists(os.path.join(args.modules_folder, module, "module", "tests", "fixtures")) and not os.path.exists(os.path.join(args.output, "fixtures", module_name)):
            shutil.copytree(os.path.join(args.modules_folder, module, "module", "tests", "fixtures"), os.path.join(args.output, "fixtures", module_name))

        if os.path.exists(os.path.join(args.modules_folder, module, "module", "tests", "config_" + args.type + ".json")):
            with open(os.path.join(args.modules_folder, module, "module", "tests", "config_" + args.type + ".json")) as module_config_file:
                app_config['modules'][module] = {"version": "2.0", "config": json.load(module_config_file)}
        elif os.path.exists(os.path.join(args.modules_folder, module, "module", "inspector_config.json")):
            with open(os.path.join(args.modules_folder, module, "module", "inspector_config.json")) as module_config_file:
                inspector_config = json.load(module_config_file)
                config = { "modules": {} }
                if "this_module" in inspector_config:
                    config["modules"][module_name] = inspector_config["this_module"]
                    config["modules"][module_name]["version"] = manifest["version"]
                app_config = dict_merge(app_config, config)
        else:
            app_config['modules'][module] = {"version": "2.0"}

    log.info("Writing app config")
    with open(os.path.join(args.output, 'config.json'), 'w') as app_config_file:
        json.dump(app_config, app_config_file, indent=4, sort_keys=True)

    log.info("Done.")


if __name__ == "__main__":
    main()
