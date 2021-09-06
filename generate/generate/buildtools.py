'''Stuff that used to live in build-tools/ that really needs to be
part of the platform.
'''
import logging
LOG = logging.getLogger(__name__)
import sys
import os
from os import path
import shutil
import json
import time
import hashlib
from datetime import datetime
from copy import copy
from zipfile import ZipFile, ZIP_DEFLATED

from module_dynamic.lib import temp_file

try:
    import forge
except:
    LOG.info("Running on command line")

# these are only used when imported by build-tools, not when server imports
try:
    from forge.generate import Generate
    from forge import defaults, build_config, ForgeError
    from forge.lib import try_a_few_times, AccidentHandler, FilterHandler, CurrentThreadHandler, classify_platform
    from forge import cli
    LOG.info("Running from build-tools")
except:
    LOG.info("Running on the server")

# force 'full' to also mean 'force_rebuild' if --nocache is also specified
try:
    if forge.settings['full'] and ("--nocache" in sys.argv):
        forge.settings['force_rebuild'] = True
    else:
        forge.settings['force_rebuild'] = False
except:
    pass

import customer_phases

ENTRY_POINT_NAME = 'forge'
FORGE_BUILD_NEEDS_TARGET = """Target required for 'forge build', e.g. 'forge build android'"""

def development_build_dynamic(unhandled_args, has_target, manager, remote, app_config, stable_platform, frepeat):

    # Peek at target
    try:
        target = unhandled_args[0]
    except IndexError:
        target = ""

    config_changed = manager.need_new_templates_for_config()
    if config_changed and target in ["ios-native", "android-native"]:
        moved_to = moved_to = os.path.join('development', '%s.%s' % (target, datetime.now().isoformat().replace(":", "-")))
        LOG.warn("")
        LOG.warn("========================================================================")
        LOG.warn("Your application's configuration has changed and the Xcode project needs")
        LOG.warn("to be regenerated.")
        LOG.warn("")
        LOG.warn("Proceeding will reset any changes you've made to the Xcode project and")
        LOG.warn("require you to repopulate your ForgeExtensions/ folder.")
        LOG.warn("")
        LOG.warn("Your existing Xcode project will be backed up to:")
        LOG.warn("")
        LOG.warn("\t%s" % moved_to)
        LOG.warn("========================================================================")
        time.sleep(1) # cli.ask_yes_no isn't buffered
        proceed = cli.ask_yes_no("Backup Xcode project directory and continue build?", False)
        if not proceed:
            LOG.info("Aborting build and restoring app configuration.")
            shutil.copy(path.join(defaults.TEMPLATE_DIR, "config.json"), path.join(defaults.SRC_DIR, "config.json"))
            LOG.info("App configuration restored.")
            return
        else: # backup existing Xcode directory
            moved_from = path.join('development', target)
            if os.path.exists(moved_from):
                shutil.move(moved_from, moved_to)
            pass


    # Invalidate any existing build if injected assets don't match
    assets_changed = False
    LOG.info("Comparing app assets against build cache")
    build_usercode   = os.path.join(os.getcwd(), "src")
    build_userassets = os.path.join(os.getcwd(), "assets")
    with temp_file() as temp:
        assets_hash = zip_local_assets(log=LOG,
                                       target=target,
                                       config=app_config,
                                       build_usercode=build_usercode,
                                       build_userassets=build_userassets,
                                       destpath=temp)
        if assets_hash:
            url = "app/{uuid}/assets/invalidate".format(uuid=app_config["uuid"])
            data = {}
            data['config'] = json.dumps(app_config)
            data['target'] = target
            data['assets_hash'] = assets_hash
            response = remote._api_post(url, data=data)
            if response["exists"]:
                assets_changed = False
                LOG.info("Found cached build matching app assets.")
            else:
                assets_changed = True
                LOG.info("Could not find a cached build matching app assets. A remote build will be required.")

    if config_changed:
        # Need new builds due to local config change
        LOG.info("Your local config has been changed, downloading updated build instructions.")
        manager.fetch_instructions()

        # repeat the whole procedure, as we may have migrated the app in some way
        forge.settings['full'] = False
        return frepeat(unhandled_args, has_target) # TODO This is a really ugly approach

    # create
    reload_result = remote.create_buildevent(app_config)['data']
    if not has_target:
        # No need to go further if we aren't building a target
        return
    reload_config = json.loads(reload_result['config'])
    reload_config_hash = reload_result['config_hash']

    try:
        target = unhandled_args.pop(0)
        if target.startswith("-"):
            raise ForgeError(FORGE_BUILD_NEEDS_TARGET)
    except IndexError:
        raise ForgeError(FORGE_BUILD_NEEDS_TARGET)

    # Not all targets output into a folder by the same name.
    target_dirs = {
        # Now they do again. But maybe not always in future.
    }
    target_dir = target
    if target in target_dirs:
        target_dir = target_dirs[target]

    # Invalidate any existing build if --full option has been passed to command line
    if forge.settings["force_rebuild"]:
        LOG.info("Performing user requested server-side rebuild of the app")
        url = "app/{uuid}/build/invalidate".format(uuid=reload_config["uuid"])
        data = {}
        data['config'] = json.dumps(reload_config)
        data['target'] = target
        response = remote._api_post(url, data=data)
        if response["exists"]:
            LOG.info("Build has been invalidated for hash: %s" % response["build_hash"])
        else:
            LOG.info("No existing build for hash: %s" % response["build_hash"])

    # Do a server side build if necessary
    if (assets_changed or not path.exists(path.join(defaults.TEMPLATE_DIR, target_dir))) and target != "reload":
        LOG.info("Your app configuration has changed since your last build of this platform, performing a remote build of your app. Once this is downloaded future builds will be faster.")
        # inject local assets into remote build if needed
        assets_url = inject_local_assets(log=LOG,
                                         target=target,
                                         config=reload_config,
                                         build_usercode=build_usercode,
                                         build_userassets=build_userassets,
                                         remote=remote,
                                         build=None)
        # TODO assets_url should really go into remote.build rather than the app config
        reload_config["assets_url"] = assets_url
        build = remote.build(config=reload_config, target=target)
        remote.fetch_unpackaged(build, to_dir=defaults.TEMPLATE_DIR, target=target)
    else:
        LOG.info('Config matches previously downloaded build, performing local build.')

    current_platform = app_config['platform_version']

    # Advise user about state of their current platform
    platform_category = classify_platform(stable_platform, current_platform)
    if platform_category == 'nonstandard':
        LOG.warning("Platform version: %s is a non-standard platform version, it may not be receiving updates and it is recommended you update to the stable platform version: %s" % (current_platform, stable_platform))

    elif platform_category == 'minor':
        # do nothing: not an issue to be on a minor platform since v2.0.0
        pass

    elif platform_category == 'old':
        LOG.warning("Platform version: %s is no longer the current platform version, it is recommended you switch to a newer version." % current_platform)

    def move_files_across():
        shutil.rmtree(path.join('development', target_dir), ignore_errors=True)
        if target != "reload":
            # Delete reload as other targets may build it
            shutil.rmtree(path.join('development', 'reload'), ignore_errors=True)
            # No reload server template
            shutil.copytree(path.join(defaults.TEMPLATE_DIR, target_dir), path.join('development', target_dir), symlinks=True)
        # also copy over android_bundle/
        if target == "android":
            shutil.rmtree(path.join('development', 'android_bundle'), ignore_errors=True)
            shutil.copytree(path.join(defaults.TEMPLATE_DIR, 'android_bundle'), path.join('development', 'android_bundle'), symlinks=True)

    if target in ["ios-native", "android-native"]:
        if not os.path.isdir(path.join('development', 'ios-native')):
            try_a_few_times(move_files_across)
        else:
            # Just delete the source files
            shutil.rmtree(customer_phases.locations_normal[target])
            # Delete reload as other targets may build it
            shutil.rmtree(path.join('development', 'reload'), ignore_errors=True)
    else:
        # Windows often gives a permission error without a small wait
        try_a_few_times(move_files_across)

    # Put config hash in config object for local generation
    # copy first as mutating dict makes assertions about previous uses tricky
    reload_config_for_local = reload_config.copy()
    reload_config_for_local['config_hash'] = reload_config_hash

    # have templates and instructions - inject code
    generator = Generate()
    generator.all('development', defaults.SRC_DIR, extra_args=unhandled_args, config=reload_config_for_local, target=target)

    if target in ["ios-native", "android-native"]:
        LOG.info("Development build created. You can access your native project files in the 'development/{target}' directory.".format(
                target=target
        ))
    else:
        LOG.info("Development build created. Use {prog} run to run your app.".format(
                prog=ENTRY_POINT_NAME
        ))



# - inject local assets into local or remote build -------------------------


def zip_local_assets(log, target, config, build_usercode, build_userassets, destpath):
    # TODO this should be specified in build_steps and not hardcoded into the platform

    assets = {}

    if target == "android" and config.get("modules", {}).get("parse", {}).get("config", {}).get("android", {}).get("googleServicesJson", {}):
        services = {
            "googleServicesJson": config["modules"]["parse"]["config"]["android"]["googleServicesJson"]
        }
        assets.update(services)
        LOG.info("zip_local_assets parse -> %s" % assets)

    if target == "ios" and config.get("modules", {}).get("icons", {}).get("config", {}).get("ios", {}):
        icons = copy(config["modules"]["icons"]["config"]["ios"])
        if "prerendered" in icons:
            del icons["prerendered"]
        assets.update(icons)

    # return None if there are no assets
    if not assets:
        return None

    # zip assets & either upload to s3 or copy to build directory
    with ZipFile(destpath, "w", compression=ZIP_DEFLATED) as assets_zip:
        for name, asset in sorted(assets.iteritems()): # make sure to always sort :-)
            asset = path.normcase(asset)
            if asset.startswith("/") or asset.startswith(".."):
                raise ConfigurationError("Asset '%s: %s' has to be a relative path" % (name, asset))

            source = path.join(build_usercode, asset)
            if not path.exists(source):
                source = path.join(build_userassets, asset)
            log.debug("Adding asset to build: {%s: %s}" % (name, path.relpath(source)))
            assets_zip.write(source, asset)

    f = open(destpath, "rb")
    hash = hashlib.sha1(f.read()).hexdigest()
    return hash


def inject_local_assets(log, target, config, build_usercode, build_userassets, remote=None, build=None):
    """With iOS 11 we first hit a limit on our ability to replace assets on the customer side
    and needed to start uploading customer assets for injection into the remote build
    """

    # zip assets & either upload to s3 or copy to build directory
    with temp_file() as temp:
        assets_hash = zip_local_assets(log=LOG,
                                       target=target,
                                       config=config,
                                       build_usercode=build_usercode,
                                       build_userassets=build_userassets,
                                       destpath=temp)

        if assets_hash is None:
            log.info("no assets to inject")
            return
        elif remote is None:
            # if local, just copy it over to build dir
            userassets = path.join(os.getcwd(), "assets.zip")
            build.userassets = userassets
            shutil.copy(temp, userassets)
        else:
            # if remote, upload it to s3 and add the url to the app config with the key "assets_url"
            response = remote._api_post("app/{uuid}/assets".format(uuid=config["uuid"]),
                                        files={"assets.zip": ("assets.zip", open(temp, "rb"))})
            userassets = response["url"]

    return userassets
