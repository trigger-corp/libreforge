from xml.etree import ElementTree
import json
import os
import shutil
from contextlib import contextmanager
import logging

import validictory_module

import build_steps
import build_steps_local
import build_steps_predicates
from xcode import XcodeProject
import utils

LOG = logging.getLogger(__name__)

@contextmanager
def cd(target_dir):
    'Change directory to :param:`target_dir` as a context manager - i.e. rip off Fabric'
    old_dir = os.getcwd()
    try:
        os.chdir(target_dir)
        yield target_dir
    finally:
        os.chdir(old_dir)

# Needed to prevent elementtree screwing with namespace names
ElementTree.register_namespace('android', 'http://schemas.android.com/apk/res/android')
ElementTree.register_namespace('tools', 'http://schemas.android.com/tools')


def _apply_build_steps(target_name, project_path, app_config, local_build_steps, module_name, assets_path, module_steps_path):
    LOG.info("%s module '%s': Performing build steps" % (target_name, module_name))
    with open(module_steps_path, 'r') as build_steps_file:
        module_build_steps = json.load(build_steps_file)
        with cd(project_path):
            build_params = {
                'app_config': app_config,
                'project_path': project_path if target_name != "iOS" else os.path.join(project_path, "ForgeInspectors"),
                'src_path': local_build_steps,
                'assets_path': assets_path
            }
            for step in module_build_steps:
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
                    for task in step["do"]:
                        task_func = getattr(build_steps, task, None)
                        if task_func is not None:
                            utils.call_with_params(task_func, build_params, step["do"][task])
                        elif local_build_steps is not None:
                            task_func = getattr(build_steps_local, task, None)
                            if task_func is not None:
                                utils.call_with_params(task_func, build_params, step["do"][task])


def apply_module_to_osx_project(module_path, project_path, skip_framework=False, inspector_config=False, include_tests=False, local_build_steps=None, app_config=None):
    """Take the module in a specific folder and apply it to an xcode ios project in another folder"""
    if not os.path.exists(os.path.join(module_path, 'manifest.json')):
        LOG.warning("Failed to include module: %s" % module_path)
        return

    if os.path.exists(os.path.join(module_path, 'identity.json')):
        with open(os.path.join(module_path, 'identity.json')) as identity_file:
            module_name = json.load(identity_file)['name']
    else:
        with open(os.path.join(module_path, 'manifest.json')) as manifest_file:
            module_name = json.load(manifest_file)['name']

    # JS
    if os.path.exists(os.path.join(module_path, 'javascript', 'module.js')):
        with open(os.path.join(module_path, 'javascript', 'module.js')) as module_js:
            with open(os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'all.js'), 'a') as alljs:
                alljs.write('(function () {\n')
                alljs.write(module_js.read())
                alljs.write('\n})();')

    # Tests
    if include_tests:
        if os.path.exists(os.path.join(module_path, 'tests', 'fixtures')):
            if os.path.exists(os.path.join(project_path, 'ForgeInspector', 'assets', 'src', 'fixtures', module_name)):
                shutil.rmtree(os.path.join(project_path, 'ForgeInspector', 'assets', 'src', 'fixtures', module_name))
            if not os.path.exists(os.path.join(project_path, 'ForgeInspector', 'assets', 'src', 'fixtures')):
                os.makedirs(os.path.join(project_path, 'ForgeInspector', 'assets', 'src', 'fixtures'))
            shutil.copytree(os.path.join(module_path, 'tests', 'fixtures'), os.path.join(project_path, 'ForgeInspector', 'assets', 'src', 'fixtures', module_name))
        if os.path.exists(os.path.join(module_path, 'tests', 'automated.js')):
            try:
                os.makedirs(os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'tests', 'automated'))
            except OSError:
                pass
            shutil.copy2(os.path.join(module_path, 'tests', 'automated.js'), os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'tests', 'automated', module_name+'.js'))
        if os.path.exists(os.path.join(module_path, 'tests', 'interactive.js')):
            try:
                os.makedirs(os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'tests', 'interactive'))
            except OSError:
                pass
            shutil.copy2(os.path.join(module_path, 'tests', 'interactive.js'), os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'tests', 'interactive', module_name+'.js'))

    # Add module a if we want it
    if not skip_framework:
        module_framework = os.path.join(module_path, 'osx', '%s.framework' % module_name)
        if os.path.isdir(module_framework):
            shutil.copytree(module_framework, os.path.join(project_path, '%s.framework' % module_name))
            xcode_project = XcodeProject(os.path.join(project_path, 'ForgeInspector.xcodeproj', 'project.pbxproj'))
            xcode_project.add_framework(module_name+'.framework', "<group>")
            xcode_project.add_saved_framework(module_name+'.framework', "<group>")
            xcode_project.save()

    if inspector_config:
        # Add inspector config for module to app_config.js(on).
        if app_config is None:
            with open(os.path.join(project_path, 'ForgeInspector', 'assets', 'app_config.json')) as app_config_json:
                app_config = json.load(app_config_json)
        if os.path.exists(os.path.join(module_path, 'inspector_config.json')):
            with open(os.path.join(module_path, 'inspector_config.json'), "r") as inspector_config_file:
                inspector_config = json.load(inspector_config_file)
        else:
            inspector_config = {
                    "modules": {
                            module_name: {
                                    "version": "exampleversion"
                            }
                    }
            }

        app_config = dict_merge(app_config, inspector_config)

        with open(os.path.join(project_path, 'ForgeInspector', 'assets', 'app_config.json'), 'w') as app_config_json:
            json.dump(app_config, app_config_json)
        with open(os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'app_config.js'), 'w') as app_config_js:
            app_config_js.write("window.forge = {}; window.forge.config = %s;" % json.dumps(app_config))

    # Validate app_config for module being added
    if os.path.exists(os.path.join(module_path, 'config_schema.json')) and \
                    "config" in app_config['modules'][module_name]:
        with open(os.path.join(module_path, 'config_schema.json')) as schema_file:
            config_schema = json.load(schema_file)

        try:
            validictory_module.validate(app_config['modules'][module_name]['config'], config_schema)
        except validictory_module.ValidationError as e:
            raise Exception("Validation failed for module '%s' with error: %s" % (module_name, str(e)))

    # frameworks
    module_frameworks = os.path.join(module_path, 'osx', 'frameworks')
    if os.path.isdir(module_frameworks):
        if os.path.exists(os.path.join(project_path, 'ForgeModule')):
            xcode_project = XcodeProject(os.path.join(project_path, 'ForgeModule', 'ForgeModule.xcodeproj', 'project.pbxproj'))
        xcode_inspector_project = XcodeProject(os.path.join(project_path, 'ForgeInspector.xcodeproj', 'project.pbxproj'))
        for framework in os.listdir(module_frameworks):
            if framework.endswith(".framework"):
                shutil.copytree(os.path.join(module_frameworks, framework), os.path.join(project_path, framework))
                if os.path.exists(os.path.join(project_path, 'ForgeModule')):
                    xcode_project.add_framework(os.path.join('..', framework), '<group>')
                xcode_inspector_project.add_saved_framework(framework, '<group>')

        if os.path.exists(os.path.join(project_path, 'ForgeModule')):
            xcode_project.save()
        xcode_inspector_project.save()

    # Run build steps - osx
    assets_path = os.path.join(os.getcwd(), "assets")
    module_steps_path = os.path.join(module_path, 'osx', 'build_steps.json')
    if not os.path.isfile(module_steps_path):
        return
    _apply_build_steps("OSX", project_path, app_config, local_build_steps, module_name, assets_path, module_steps_path)
    if not os.path.exists(os.path.join(project_path, "dist", "build_steps")):
        os.makedirs(os.path.join(project_path, "dist", "build_steps"))
    shutil.copy2(module_steps_path, os.path.join(project_path, "dist", "build_steps", module_name + ".json"))


def apply_module_to_ios_project(module_path, project_path, app_config, skip_a=False, include_tests=False, local_build_steps=None):
    """Take the module in a specific folder and apply it to an xcode ios project in another folder"""
    if not os.path.exists(os.path.join(module_path, 'manifest.json')):
        LOG.warning("Failed to include module: %s" % module_path)
        return

    if os.path.exists(os.path.join(module_path, 'identity.json')):
        with open(os.path.join(module_path, 'identity.json')) as identity_file:
            module_name = json.load(identity_file)['name']
    else:
        with open(os.path.join(module_path, 'manifest.json')) as manifest_file:
            module_name = json.load(manifest_file)['name']

    # JS
    if os.path.exists(os.path.join(module_path, 'javascript', 'module.js')):
        LOG.info("iOS module '%s': Appending module.js to all.js" % module_name)
        with open(os.path.join(module_path, 'javascript', 'module.js')) as module_js:
            with open(os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'all.js'), 'a') as alljs:
                alljs.write('(function () {\n')
                alljs.write(module_js.read())
                alljs.write('\n})();')

    # Tests
    if include_tests:
        LOG.info("iOS module '%s': Including test files" % module_name)
        if os.path.exists(os.path.join(module_path, 'tests', 'fixtures')):
            if os.path.exists(os.path.join(project_path, 'ForgeInspector', 'assets', 'src', 'fixtures', module_name)):
                shutil.rmtree(os.path.join(project_path, 'ForgeInspector', 'assets', 'src', 'fixtures', module_name))
            if not os.path.exists(os.path.join(project_path, 'ForgeInspector', 'assets', 'src', 'fixtures')):
                os.makedirs(os.path.join(project_path, 'ForgeInspector', 'assets', 'src', 'fixtures'))
            shutil.copytree(os.path.join(module_path, 'tests', 'fixtures'), os.path.join(project_path, 'ForgeInspector', 'assets', 'src', 'fixtures', module_name))
        if os.path.exists(os.path.join(module_path, 'tests', 'automated.js')):
            try:
                os.makedirs(os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'tests', 'automated'))
            except OSError:
                pass
            shutil.copy2(os.path.join(module_path, 'tests', 'automated.js'), os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'tests', 'automated', module_name+'.js'))
        if os.path.exists(os.path.join(module_path, 'tests', 'interactive.js')):
            try:
                os.makedirs(os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'tests', 'interactive'))
            except OSError:
                pass
            shutil.copy2(os.path.join(module_path, 'tests', 'interactive.js'), os.path.join(project_path, 'ForgeInspector', 'assets', 'forge', 'tests', 'interactive', module_name+'.js'))

    # Add module a if we want it
    if not skip_a:
        LOG.info("iOS module '%s': Including module.a" % module_name)
        module_a = os.path.join(module_path, 'ios', 'module.a')
        if os.path.isfile(module_a):
            # Copy to libs
            shutil.copy2(module_a, os.path.join(project_path, module_name+'.a'))

            # Add to xcode build
            xcode_project = XcodeProject(os.path.join(project_path, 'ForgeInspector.xcodeproj', 'project.pbxproj'))
            xcode_project.add_framework(module_name+'.a', "<group>")
            xcode_project.save()

    # Validate config
    if os.path.exists(os.path.join(module_path, 'config_schema.json')) and \
                    "config" in app_config['modules'][module_name]:
        with open(os.path.join(module_path, 'config_schema.json')) as schema_file:
            config_schema = json.load(schema_file)

        try:
            validictory_module.validate(app_config['modules'][module_name]['config'], config_schema)
        except validictory_module.ValidationError as e:
            raise Exception("Validation failed for module '%s' with error: %s" % (module_name, str(e)))

    # bundles
    module_bundles = os.path.join(module_path, 'ios', 'bundles')
    if os.path.isdir(module_bundles):
        LOG.info("iOS module '%s': Including bundles" % module_name)
        xcode_project = XcodeProject(os.path.join(project_path, 'ForgeInspector.xcodeproj', 'project.pbxproj'))
        for bundle in os.listdir(module_bundles):
            if bundle.endswith(".bundle"):
                shutil.copytree(os.path.join(module_bundles, bundle), os.path.join(project_path, bundle))
                xcode_project.add_resource(bundle)

        xcode_project.save()

    # headers
    module_headers = os.path.join(module_path, 'ios', 'headers')
    if os.path.isdir(module_headers):
        LOG.info("iOS module '%s': Including headers" % module_name)
        shutil.copytree(module_headers, os.path.join(project_path, 'ForgeModule', 'forge_headers', module_name))

    # Run build steps - iOS
    assets_path = os.path.join(os.getcwd(), "assets")
    module_steps_path = os.path.join(module_path, 'ios', 'build_steps.json')
    if not os.path.isfile(module_steps_path):
        return
    _apply_build_steps("iOS", project_path, app_config, local_build_steps, module_name, assets_path, module_steps_path)
    if not os.path.exists(os.path.join(project_path, "dist", "build_steps")):
        os.makedirs(os.path.join(project_path, "dist", "build_steps"))
    shutil.copy2(module_steps_path, os.path.join(project_path, "dist", "build_steps", module_name + ".json"))


def apply_module_to_android_project(module_path, project_path, app_config, skip_jar=False, include_tests=False, local_build_steps=None):
    """Take the module in a specific folder and apply it to an eclipse android project in another folder"""
    if not os.path.exists(os.path.join(module_path, 'manifest.json')):
        LOG.warning("Failed to include module: %s" % module_path)
        return

    if os.path.exists(os.path.join(module_path, 'identity.json')):
        with open(os.path.join(module_path, 'identity.json')) as identity_file:
            module_name = json.load(identity_file)['name']
    else:
        with open(os.path.join(module_path, 'manifest.json')) as manifest_file:
            module_name = json.load(manifest_file)['name']

    # Some paths
    module_jar = os.path.join(module_path, 'android', 'module.jar')
    module_libs = os.path.join(module_path, 'android', 'libs')
    module_res = os.path.join(module_path, 'android', 'res')
    vanilla_aar = os.path.join(module_path, 'android', 'ForgeModule-vanilla-release.aar')

    # JS
    if os.path.exists(os.path.join(module_path, 'javascript', 'module.js')):
        LOG.info("Android module '%s': Appending module.js to all.js" % module_name)
        with open(os.path.join(module_path, 'javascript', 'module.js')) as module_js:
            with open(os.path.join(project_path, 'assets', 'forge', 'all.js'), 'a') as alljs:
                alljs.write('(function () {\n')
                alljs.write(module_js.read())
                alljs.write('\n})();')

    # Tests
    if include_tests:
        LOG.info("Android module '%s': Including test files" % module_name)
        if os.path.exists(os.path.join(module_path, 'tests', 'fixtures')):
            if os.path.exists(os.path.join(project_path, 'assets', 'src', 'fixtures', module_name)):
                shutil.rmtree(os.path.join(project_path, 'assets', 'src', 'fixtures', module_name))
            if not os.path.exists(os.path.join(project_path, 'assets', 'src', 'fixtures')):
                os.makedirs(os.path.join(project_path, 'assets', 'src', 'fixtures'))
            shutil.copytree(os.path.join(module_path, 'tests', 'fixtures'), os.path.join(project_path, 'assets', 'src', 'fixtures', module_name))
        if os.path.exists(os.path.join(module_path, 'tests', 'automated.js')):
            try:
                os.makedirs(os.path.join(project_path, 'assets', 'forge', 'tests', 'automated'))
            except OSError:
                pass
            shutil.copy2(os.path.join(module_path, 'tests', 'automated.js'), os.path.join(project_path, 'assets', 'forge', 'tests', 'automated', module_name+'.js'))
        if os.path.exists(os.path.join(module_path, 'tests', 'interactive.js')):
            try:
                os.makedirs(os.path.join(project_path, 'assets', 'forge', 'tests', 'interactive'))
            except OSError:
                pass
            shutil.copy2(os.path.join(module_path, 'tests', 'interactive.js'), os.path.join(project_path, 'assets', 'forge', 'tests', 'interactive', module_name+'.js'))

    # Add module jar if we want it
    if not skip_jar:
        if not os.path.exists(os.path.join(project_path, 'libs')):
            os.makedirs(os.path.join(project_path, 'libs'))
        if os.path.exists(vanilla_aar):
            LOG.info("Android module '%s': Adding module aar to libs" % module_name)
            shutil.copy2(vanilla_aar, os.path.join(project_path, 'libs', module_name+'-vanilla-release.aar'))
        elif os.path.exists(module_jar):
            LOG.info("Android module '%s': Adding module jar to libs" % module_name)
            shutil.copy2(module_jar, os.path.join(project_path, 'libs', 'io.trigger.forge.android.modules.'+module_name+'.jar'))

    # Validate app_config for module being added
    if os.path.exists(os.path.join(module_path, 'config_schema.json')) and \
                    "config" in app_config['modules'][module_name]:
        with open(os.path.join(module_path, 'config_schema.json')) as schema_file:
            config_schema = json.load(schema_file)

        try:
            validictory_module.validate(app_config['modules'][module_name]['config'], config_schema)
        except validictory_module.ValidationError as e:
            raise Exception("Validation failed for module '%s' with error: %s" % (module_name, str(e)))

    # res
    module_res = os.path.join(module_path, 'android', 'res')
    if os.path.isdir(module_res):
        LOG.info("Android module '%s': Adding module res files" % module_name)
        for dirpath, _, filenames in os.walk(module_res):
            app_res = os.path.join(project_path, 'res_module_%s' % module_name, dirpath[len(module_res)+1:])
            if not os.path.exists(app_res):
                os.makedirs(app_res)
            for filename in filenames:
                if (filename.startswith('.')):
                    continue
                src = os.path.join(dirpath, filename)
                dst = os.path.join(app_res, filename)
                if os.path.exists(dst):
                    # TODO we should no longer be hitting this codepath with gradle - remove before pushing to stable
                    if os.path.splitext(dst)[1] != '.xml':
                        raise Exception("File '%s' already exists, module resources may only add files, not replace them." % dst)
                    LOG.info("Module resource filename '%s' already exists. Merging into '%s'." % (src, dst))
                    merged = utils.merge_android_resources((src, dst))
                    with open(dst, 'w') as f:
                        f.write(merged)
                else:
                    shutil.copy2(src, dst)

    # libs - only add if we don't have .aar files for the module as they will already be compiled in
    if os.path.isdir(module_libs) and (not os.path.exists(vanilla_aar)):
        LOG.info("Android module '%s': Adding module lib files" % module_name)
        for dirpath, _, filenames in os.walk(module_libs):
            if not os.path.exists(os.path.join(project_path, 'libs', dirpath[len(module_libs)+1:])):
                os.makedirs(os.path.join(project_path, 'libs', dirpath[len(module_libs)+1:]))
            for filename in filenames:
                shutil.copy2(os.path.join(dirpath, filename), os.path.join(project_path, 'libs', dirpath[len(module_libs)+1:], filename))

    # Run build steps - android
    assets_path = os.path.join(os.getcwd(), "assets")
    module_steps_path = os.path.join(module_path, 'android', 'build_steps.json')
    if not os.path.isfile(module_steps_path):
        return
    _apply_build_steps("Android", project_path, app_config, local_build_steps, module_name, assets_path, module_steps_path)
    if not os.path.exists(os.path.join(project_path, "build_steps")):
        os.makedirs(os.path.join(project_path, "build_steps"))
    shutil.copy2(module_steps_path, os.path.join(project_path, "build_steps", module_name + ".json"))
