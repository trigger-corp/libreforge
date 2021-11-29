'''Goals are a collection of phases which are automatically added to a build, then executed.

The idea here is for the calling code to not need to know about the right phases to include
when getting a higher-level "goal" done; e.g. running or generating an app.
'''
import platform
import sys
import os
import tempfile
import json

from module_dynamic.lib import BASE_EXCEPTION
from lib import dig
import migrate_tasks

def log_build(build, action):
    '''
    Bundle together some stats and send it to the server for tracking
    This is called by every other function in this module, just before running
    the build.
    '''
    from forge import build_config
    import forge
    from forge.remote import Remote

    log = {}
    log['action']        = action
    log['platform']      = platform.platform()
    log['version']       = sys.version
    log['uuid']          = build.config['uuid']
    log['tools_version'] = forge.VERSION
    if len(build.enabled_platforms):
        target = list(build.enabled_platforms)[0]
        log['target'] = target
    log['package_name'] = dig(build.config, ['core',target,'package_name'], "io.trigger.forge" + build.config["uuid"])
    config = build_config.load()
    remote = Remote(config)
    remote._authenticate()
    remote._api_post('track/', data=log)


def generate_app_from_template(generate_module, build_to_run):
    '''Inject code into a previously built template.

    :param generate_module: the :mod:`generate.generate` module
    :param build_to_run: a :class:`build.Build` instance
    '''
    add_check_settings_steps(generate_module, build_to_run)
    build_to_run.add_steps(generate_module.customer_phases.resolve_urls())
    if os.path.isdir('hooks/prebuild'):
        # Create a temp dir
        tempdir = tempfile.mkdtemp()
        os.rmdir(tempdir)
        build_to_run.add_steps(generate_module.customer_phases.copy_user_source_to_tempdir(ignore_patterns=build_to_run.ignore_patterns, tempdir=tempdir))
        build_to_run.add_steps(generate_module.customer_phases.run_hook(hook='prebuild', dir=tempdir))
        build_to_run.add_steps(generate_module.customer_phases.validate_user_source(src=tempdir))
        build_to_run.add_steps(generate_module.customer_phases.copy_user_source_to_template(ignore_patterns=build_to_run.ignore_patterns, src=tempdir))
        # Delete temp dir
        build_to_run.add_steps(generate_module.customer_phases.delete_tempdir(tempdir=tempdir))
    else:
        build_to_run.add_steps(generate_module.customer_phases.validate_user_source())
        build_to_run.add_steps(generate_module.customer_phases.copy_user_source_to_template(ignore_patterns=build_to_run.ignore_patterns))
    build_to_run.add_steps(generate_module.customer_phases.include_platform_in_html())
    build_to_run.add_steps(generate_module.customer_phases.compile_ios_native_app())
    build_to_run.add_steps(generate_module.customer_phases.include_name(build_to_run))
    build_to_run.add_steps(generate_module.customer_phases.include_uuid())
    build_to_run.add_steps(generate_module.customer_phases.include_author())
    build_to_run.add_steps(generate_module.customer_phases.include_description())
    build_to_run.add_steps(generate_module.customer_phases.include_version(build_to_run))
    build_to_run.add_steps(generate_module.customer_phases.include_reload())
    build_to_run.add_steps(generate_module.customer_phases.include_requirements())
    build_to_run.add_steps(generate_module.customer_phases.run_module_build_steps(build_to_run)) # TODO must we pass in the build?
    if (set(['web']) & set(build_to_run.enabled_platforms)):
        build_to_run.add_steps(generate_module.legacy_phases.customer_phase())
    build_to_run.add_steps(generate_module.customer_phases.include_config())
    build_to_run.add_steps(generate_module.customer_phases.make_installers())
    if os.path.isdir('hooks/postbuild'):
        build_to_run.add_steps(generate_module.customer_phases.run_hook(hook='postbuild', dir='development'))

    log_build(build_to_run, "generate")

    build_to_run.run()

def run_app(generate_module, build_to_run):
    '''Run a generated app on a device or emulator.

    :param generate_module: the :mod:`generate.generate` module
    :param build_to_run: a :class:`build.Build` instance
    '''

    if len(build_to_run.enabled_platforms) != 1:
        raise BASE_EXCEPTION("Expected to run exactly one platform at a time")

    build_to_run.add_steps(generate_module.customer_phases.set_is_development(True))

    target = list(build_to_run.enabled_platforms)[0]
    _disable_live(build_to_run, target)
    if target == 'android':
        interactive = build_to_run.tool_config.get('general.interactive', True)
        sdk = build_to_run.tool_config.get('android.sdk')
        device = build_to_run.tool_config.get('android.device')
        purge = build_to_run.tool_config.get('android.purge')

        build_to_run.add_steps(
                generate_module.customer_phases.run_android_phase(
                        build_to_run.output_dir,
                        sdk=sdk,
                        device=device,
                        interactive=interactive,
                        purge=purge,
                )
        )
    elif target == 'ios':
        device = build_to_run.tool_config.get('ios.device')
        build_to_run.add_steps(
                generate_module.customer_phases.run_ios_phase(device)
        )
    elif target == 'ios-native':
        device = build_to_run.tool_config.get('ios.device')
        build_to_run.add_steps(
                generate_module.customer_phases.run_ios_native_phase(device)
        )
    elif target == 'osx':
        build_to_run.add_steps(
                generate_module.customer_phases.run_osx_phase()
        )
    elif target == 'web':
        build_to_run.add_steps(
                generate_module.customer_phases.run_web_phase()
        )

    log_build(build_to_run, "run")
    build_to_run.run()


def serve_app(generate_module, build_to_run):

    if len(build_to_run.enabled_platforms) != 1:
        raise BASE_EXCEPTION("Expected to serve exactly one platform at a time")

    build_to_run.add_steps(generate_module.customer_phases.set_is_development(True))
    build_to_run.add_steps(generate_module.customer_phases.serve(build_to_run.output_dir))

    target = list(build_to_run.enabled_platforms)[0]

    if target == 'android':
        interactive = build_to_run.tool_config.get('general.interactive', True)
        sdk = build_to_run.tool_config.get('android.sdk')
        device = build_to_run.tool_config.get('android.device')
        purge = build_to_run.tool_config.get('android.purge')
        build_to_run.add_steps(
                generate_module.customer_phases.run_android_phase(
                        build_to_run.output_dir,
                        sdk=sdk,
                        device=device,
                        interactive=interactive,
                        purge=purge,
                )
        )
    elif target == 'ios':
        device = build_to_run.tool_config.get('ios.device')
        build_to_run.add_steps(
                generate_module.customer_phases.run_ios_phase(device)
        )
    elif target == 'osx':
        build_to_run.add_steps(
                generate_module.customer_phases.run_osx_phase()
        )
    elif target == 'web':
        build_to_run.add_steps(
                generate_module.customer_phases.run_web_phase()
        )

    log_build(build_to_run, "serve")
    build_to_run.run()

    # linux requires manual app startup for iOS so we can't exit yet
    if target == 'ios' and sys.platform.startswith('linux'):
        import time
        time.sleep(3600)


def package_app(generate_module, build_to_run):

    if len(build_to_run.enabled_platforms) != 1:
        raise BASE_EXCEPTION("Expected to package exactly one platform at a time")

    build_to_run.add_steps(generate_module.customer_phases.set_is_development(False))

    target = list(build_to_run.enabled_platforms)[0]
    _disable_live(build_to_run, target)

    build_to_run.add_steps(generate_module.customer_phases.package(build_to_run.output_dir))

    log_build(build_to_run, "package")
    build_to_run.run()


def _disable_live(build, target):
    def _disable_for_target(build, dest):
        app_config = os.path.join(dest, "app_config.json")
        with open(app_config) as f:
            config = json.load(f)
            if "core" in config and "general" in config["core"] and "live" in config["core"]["general"]:
                del config["core"]["general"]["live"]
                with open(app_config, "w") as f:
                    json.dump(config, f, indent=4, sort_keys=True)

    if target == 'ios':
        _disable_for_target(build, os.path.join("development", "ios", "simulator-ios.app", "assets"))
        _disable_for_target(build, os.path.join("development", "ios", "device-ios.app", "assets"))
    elif target == 'android':
        _disable_for_target(build, os.path.join("development", "android", "assets"))

def add_check_settings_steps(generate_module, build_to_run):
    """
    Required steps to sniff test the JavaScript and local configuration
    """
    build_to_run.add_steps(generate_module.customer_phases.check_javascript())
    build_to_run.add_steps(generate_module.customer_phases.check_local_config_schema())

def check_settings(generate_module, build_to_run):
    """
    Check the validity of locally configured settings.
    """
    add_check_settings_steps(generate_module, build_to_run)

    build_to_run.run()

def cleanup_after_interrupted_run(generate_module, build_to_run):
    """
    Cleanup after a run operation that was interrupted forcefully.

    This is exposed so the Trigger Toolkit can cleanup anything lingering from a run operation,
    e.g. node, adb, and any locks they have on files in the development folder
    """
    build_to_run.add_steps(generate_module.customer_phases.clean_phase())
    build_to_run.run()

def migrate_app_to_current(path, **kw):
    """
    Update an app compatible with an old platform version to be compatible with this one.
    e.g. transform config.json

    :returns: True if some migration occured, False if no changes happened
    """
    return migrate_tasks.migrate_to_config_version_4(path)
