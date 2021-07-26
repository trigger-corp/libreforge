from collections import namedtuple
from glob import glob
import logging
import multiprocessing
import os
from os import path
import StringIO
import re
import shutil
import subprocess
from subprocess import PIPE, STDOUT
import threading
import sys
import tempfile
import time
import zipfile
import errno

from module_dynamic import lib
from lib import task, ensure_lib_available
from module_dynamic import utils
from module_dynamic.utils import run_shell, ShellError

import android_sdkmanager as sdkmanager

LOG = logging.getLogger(__name__)

class AndroidError(lib.BASE_EXCEPTION):
    pass


# - message templates ---------------------------------------------------------

NO_JAVA_TEMPLATE = """Java was not available in your PATH nor was it found in any of these folders:

{searched}

If you already have a Java runtime installed you will need to ensure that the JAVA_HOME environment variable is set to the correct location.

Otherwise you will need to install a Java runtime in order to deploy or package for Android. You can get one from here:
https://java.com/en/download/index.jsp

"""

NO_JARSIGNER_TEMPLATE = """The Java jarsigner binary  was not available in your PATH nor was it found in any of these folders:

{searched}

If you already have a Java runtime installed you will need to ensure that the JAVA_HOME environment variable is set to the correct location.

Otherwise you will need to install a Java runtime in order to deploy or package for Android. You can get one from here:
https://java.com/en/download/index.jsp

"""


NO_SDK_TEMPLATE = """The Android SDK was not found in any of these folders:

{searched}

You can:"""


NEW_AVD_TEMPLATE = """A new emulator has been created and needs to initialize.

You can run your app again once the emulator has finished booting.
"""


# - user interactions ---------------------------------------------------------

def _find_or_install_sdk(build):
    """Searches for and returns the details of an Android SDK already existing
    on the operating system, otherwise presents the user with a choice to
    install one and returns the details of that after doing so.

    :param build: Contains information about the system, e.g. user specific SDK

    Returns an AndroidSdkBinaries object and a path to the java executable.
    """

    java, searched = sdkmanager.locate_java(build)
    if java is None:
        raise AndroidError(NO_JAVA_TEMPLATE.format(searched="\n".join(searched)))
    LOG.info("Using java: %s" % str(java))

    sdk, searched = sdkmanager.locate_sdk(build)
    if sdk is None:
        question_text = NO_SDK_TEMPLATE.format(searched="\n".join(searched))
        sdk_path = utils.value_for_platform(sdkmanager.platform_local_sdk_root)
        LOG.info("\n\n%s" % question_text)
        choice = lib.ask_multichoice(
            question_text=question_text,
            choices = [
                "Attempt to download and install the SDK automatically to {sdk_path}".format(sdk_path=sdk_path),
                "Specify the location of an already existing Android SDK installation"
            ]
        )
        if choice != 1:
            lib.local_config_problem(
                build,
                message="Couldn't find Android SDK. Please set it's location in your local config for this app.",
                examples={"android.sdk": path.abspath("/path/to/android-sdk")},
            )

        sdk, searched = sdkmanager.install(build)
        if sdk is None:
            lib.local_config_problem(
                build,
                message="Couldn't install an Android SDK. Please set it's location in your local config for this app.",
                examples={"android.sdk": path.abspath("/path/to/android-sdk")},
            )

    LOG.info("Using Android SDK: %s" % searched)

    return java, sdk


def _prompt_user_to_attach_device(build, sdk):
    """Ask user if they want to launch an AVD or attempt to find a device again."""

    choice = lib.ask_multichoice(question_text="No active Android device found, would you like to:", choices=[
        "Attempt to automatically launch the Android emulator",
        "Attempt to find the device again (choose this option after plugging in an Android device or launching the emulator)",
    ])

    return choice == 1 # should_launch_emulator




# - helpers -------------------------------------------------------------------

def _run_adb(cmd, timeout, sdk, ignore_exitcode=None):
    runner = {
        "process": None,
        "std_out": None
    }
    def target():
        try:
            runner["process"] = lib.PopenWithoutNewConsole(cmd, stdout=PIPE, stderr=STDOUT)
        except OSError as e:
            if e.errno == errno.ENOENT:
                # XXX: prompt to update the platform tools, then retry?
                raise AndroidError(NO_ADB_TEMPLATE.format(adb_location=sdk.adb))
            raise

        runner["std_out"] = runner["process"].communicate()[0]

    thread = threading.Thread(target=target)
    thread.start()

    thread.join(timeout)
    if thread.is_alive():
        LOG.debug("ADB hung, terminating process")
        _restart_adb(sdk)
        thread.join()

    # optionally override non-zero exit codes
    if ignore_exitcode and ignore_exitcode in runner["std_out"]:
        return runner["std_out"]

    if runner["process"].returncode != 0:
        LOG.debug("Communication with adb failed: %s" % (runner["std_out"]))
        raise AndroidError(runner["std_out"].split("\n")[0])

    return runner["std_out"]

def _kill_adb():
    if sys.platform.startswith('win'):
        run_shell('taskkill', '/T', '/IM', 'adb.exe', fail_silently=True)
        run_shell('taskkill', '/T', '/F', '/IM', 'adb.exe', fail_silently=True)
    else:
        run_shell('killall', 'adb', fail_silently=True)
        run_shell('killall', '-9', 'adb', fail_silently=True)

def _restart_adb(sdk):
    """Forcably kills any ADB processes running on the system and starts
    a new one detached from this process
    """
    _kill_adb()

    _run_detached([sdk.adb, 'start-server'], wait=True)

def _scrape_available_devices(text):
    """Scrapes the output of the adb devices command into a list

    :param text: Full output of adb devices command to scrape
    """
    lines = text.split('\n')
    available_devices = []

    for line in lines:
        words = line.split('\t')

        if len(words[0]) > 5 and words[0].find(" ") == -1:
            available_devices.append(words[0])

    return available_devices

def _run_detached(command, wait=True):
    """Run a process entirely detached from this one, and optionally wait
    for it to finish.

    :param command: list of shell arguments
    :param wait: don't return until the command completes
    """
    full_command = subprocess.list2cmdline(command)
    LOG.debug("Running detached: %s" % full_command)

    if sys.platform.startswith('win'):
        if wait:
            os.system("cmd /c start /WAIT "
                      "\"Detached Forge command - will automatically close\" "
                      "\""+"\" \"".join(command)+"\"")
        else:
            os.system("cmd /c start "
                      "\"Detached Forge command\" "
                      "\""+"\" \"".join(command)+"\"")
    else:
        def _run_in_shell(queue):
            '''will be invoked in by a separate process, to actually run the
            detached command'''
            # setsid detaches us completely from the caller
            try:
                os.setsid()

                proc = lib.PopenWithoutNewConsole(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                if not wait:
                    # assume success at this point if we're not waiting for process to finish
                    queue.put(0)

                for line in iter(proc.stdout.readline, ''):
                    queue.put(line)

                # signify success or error
                queue.put(proc.wait())

            except Exception as e:
                import traceback
                e._traceback = traceback.format_exc(e)
                queue.put(e)

        # to get the "finished" signal
        queue = multiprocessing.Queue()

        # multiprocessing throws an error on start() if we spawn a process from
        # a daemon process but we don't care about this
        multiprocessing.current_process().daemon = False

        proc = multiprocessing.Process(target=_run_in_shell, args=(queue, ))
        proc.daemon = True
        proc.start()

        # wait until the command completes
        aggregated_output = StringIO.StringIO()

        for output in iter(queue.get, ''):
            if isinstance(output, int):
                if output == 0:
                    return
                else:
                    raise ShellError(message="Detached command failed: %s" % full_command, output=aggregated_output.getvalue())

            elif isinstance(output, Exception):
                LOG.debug(output._traceback)
                raise ShellError(message="Exception running detached command: %s" % full_command, output=str(output))

            if isinstance(output, str):
                aggregated_output.write(output)
                LOG.debug(output.rstrip('\r\n'))

def _create_avd(build, sdk):
    sdkmanager.install_emulator_image(build)
    avd_root = utils.value_for_platform(sdkmanager.platform_avd_root)
    command = [
        sdk.avdmanager,
        "create",
        "avd",
        "--device", "pixel",
        "--name", "forge",
        "--package", sdkmanager.android_emulator_image,
        "--path", path.join(avd_root, "forge-avd"),
        "--force"
    ]
    proc = lib.PopenWithoutNewConsole(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    time.sleep(0.1)
    proc_std = proc.communicate(input='\n')[0]

    if proc.returncode != 0 or (proc_std and proc_std.startswith("Error")):
        raise ShellError(message="Error creating Android Virtual Device", output=proc_std)

def _launch_avd(build, sdk):
    _run_detached([
        sdk.emulator,
        "-avd", "forge",
        #"-gpu", "auto",
    ], wait=False)

    LOG.info("Started emulator, waiting for device to boot")
    _run_adb([sdk.adb, 'wait-for-device'], 300, sdk)

    try:
        # Keep polling for package manager being available on the device (takes some time on the emulator)
        LOG.info("Waiting for package manager to become available (this will take a while)")
        failed = "Can't find service: package"
        out = failed
        while failed in out:
            time.sleep(1)
            out = _run_adb([sdk.adb, "shell", "pm", "path", "android"], 120, sdk, ignore_exitcode=failed)
            LOG.debug(out)

        # Poll for system provider settings
        LOG.info("Waiting for settings to become available")
        failed = "Can't find service: settings"
        out = failed
        while failed in out:
            time.sleep(1)
            out = _run_adb([sdk.adb, "shell", "settings", "list", "system"], 120, sdk, ignore_exitcode=failed)
            LOG.debug(out)
    except:
        raise AndroidError(NEW_AVD_TEMPLATE)

def _sign_zipf(lib_path, java, keystore, storepass, keyalias, keypass, signed_zipf_name, zipf_name):
    apksigner_jar = path.join(lib_path, "apksigner.jar")
    if not os.path.exists(apksigner_jar):
        apksigner_jar = path.join(lib_path, "noarch.android.build-tools.29.0.3", "apksigner.jar")
    command = [
        java, "-jar", apksigner_jar, "sign",
        "--ks",           keystore,
        "--ks-pass",      "pass:%s" % storepass,
        "--ks-key-alias", keyalias,
        "--key-pass",     "pass:%s" % keypass,
        "--out",          signed_zipf_name,
        zipf_name
    ]
    run_shell(*command)

def _sign_zipf_debug(lib_path, java, zipf_name, signed_zipf_name):
    LOG.info('Signing APK with a debug key')

    return _sign_zipf(
        lib_path=lib_path,
        java=java,
        keystore=path.join(lib_path, 'debug.keystore'),
        storepass="android",
        keyalias="androiddebugkey",
        keypass="android",
        signed_zipf_name=signed_zipf_name,
        zipf_name=zipf_name,
    )

def _sign_zipf_release(lib_path, java, zipf_name, signed_zipf_name, signing_info):
    LOG.info('Signing APK with your release key')
    return _sign_zipf(
        lib_path=lib_path,
        java=java,
        keystore=signing_info['android.profile.keystore'],
        storepass=signing_info['android.profile.storepass'],
        keyalias=signing_info['android.profile.keyalias'],
        keypass=signing_info['android.profile.keypass'],
        signed_zipf_name=signed_zipf_name,
        zipf_name=zipf_name,
    )

def _align_apk(sdk, signed_zipf_name, out_apk_name):
    LOG.info('Aligning apk')
    command = [sdk.zipalign, '-v', '4', signed_zipf_name, out_apk_name]
    run_shell(*command)

def _build_aab(java, bundletool, base_zip, output):
    command = [
        java, "-jar", bundletool, "build-bundle",
        "--modules", base_zip,
        "--output",  output,
    ]
    run_shell(*command)

def _sign_aab(jarsigner, signing_info, filename):
    if signing_info['android.dontsign']:
        LOG.info("signing disabled for android app bundle, skipping")
        return
    sigalg = signing_info['android.profile.sigalg'] or "SHA256withRSA"
    digestalg = signing_info['android.profile.digestalg'] or "SHA-256"
    LOG.info("using signature algorithm: %s", sigalg)
    LOG.info("using digest algorithm: %s", digestalg)
    command = [
        jarsigner,
        "-keystore",     signing_info['android.profile.keystore'],
        "-storepass",    signing_info['android.profile.storepass'],
        "-keypass",      signing_info['android.profile.keypass'],
        "-sigalg",       sigalg,
        "-digestalg",    digestalg,
        filename,        signing_info['android.profile.keyalias'],
    ]
    run_shell(*command)

def _validate_aab(java, bundletool, filename):
    command = [
        java, "-jar", bundletool, "validate",
        "--bundle", filename,
    ]
    run_shell(*command)

def _generate_package_name(build):
    if "core" not in build.config:
        build.config["core"] = {}
    if "android" not in build.config["core"]:
        build.config["core"]["android"] = {}
    if "package_name" not in build.config["core"]["android"]:
        build.config["core"]["android"]["package_name"] = "io.trigger.forge" + build.config["uuid"]
    return build.config["core"]["android"]["package_name"]

def _follow_log(sdk, chosen_device):
    LOG.info('Clearing android log')

    command = [sdk.adb, '-s', chosen_device, 'logcat', '-c']
    run_shell(*command, command_log_level=logging.INFO)

    LOG.info('Showing android log')

    run_shell(sdk.adb, '-s', chosen_device, 'logcat', 'WebCore:D', 'Forge:D', '*:s', command_log_level=logging.INFO, check_for_interrupt=True)

def _create_avd_if_necessary(build, sdk):
    LOG.info("Checking for previously created AVD")
    avd_root = utils.value_for_platform(sdkmanager.platform_avd_root)
    if path.isdir(path.join(avd_root, "forge-avd")):
        LOG.info("Existing AVD found")
        return False
    else:
        _create_avd(build, sdk)
        return True

def _get_available_devices(sdk, try_count=0):
    proc_std = _run_adb([sdk.adb, "devices"], timeout=10, sdk=sdk)

    available_devices = _scrape_available_devices(proc_std)

    if not available_devices and try_count < 3:
        LOG.debug("No devices found, checking again")
        time.sleep(2)
        if try_count == 1:
            _restart_adb(sdk)
        return _get_available_devices(sdk, (try_count + 1))
    else:
        return available_devices


def _create_apk(build, java, sdk, target, output_filename, interactive=True):
    """Create an APK file from the the contents of development/android.

    :param output_filename: name of the file to which we'll write
    """

    lib_path = path.normpath(path.join('.template', 'lib'))
    LOG.error("LIB PATH: %s: " % lib_path)
    if not path.isdir(lib_path):
        lib_path = lib.expand_relative_path(
            build, path.join('generate', 'lib')
        )
    LOG.error("LIB PATH is now: %s: " % lib_path)
    dev_dir = path.normpath(path.join('development', target))

    LOG.info('Creating Android .apk file')

    with lib.temp_file() as stage1:
        with zipfile.ZipFile(stage1, "w") as zf:
            for dirname, subdirs, files in os.walk(dev_dir):
                destdir = path.relpath(dirname, dev_dir)
                LOG.debug("Adding: %s => %s" % (dirname, destdir))
                zf.write(dirname, destdir)
                for filename in files:
                    zf.write(os.path.join(dirname, filename), os.path.join(destdir, filename))
        with lib.temp_file() as stage2:
            _align_apk(sdk, stage1, stage2)
            _sign_zipf_debug(lib_path, java, stage2, output_filename)

def _create_output_directory(output):
    'output might be in some other directory which does not yet exist'
    directory = path.dirname(output)
    if not path.isdir(directory):
        os.makedirs(directory)

def _generate_path_to_output_apk(build):
    file_name = "{name}-{time}.apk".format(
            name=re.sub("[^a-zA-Z0-9]", "", build.config["name"].lower()),
            time=str(int(time.time()))
    )
    target = list(build.enabled_platforms)[0]
    return path.normpath(path.join("release", target, file_name))

def _generate_path_to_output_aab(build):
    file_name = "{name}-{time}.aab".format(
            name=re.sub("[^a-zA-Z0-9]", "", build.config["name"].lower()),
            time=str(int(time.time()))
    )
    target = list(build.enabled_platforms)[0]
    return path.normpath(path.join("release", target, file_name))

def _lookup_or_prompt_for_signing_info(build):
    """Obtain the required details for signing an APK, first by checking local_config.json
    and then asking the user for anything missing.
    """

    required_info = {
            'android.profile.keystore': {
                    'type': 'string',
                    '_filepicker': True,
                    'description': 'The location of your release keystore',
                    'title': 'Keystore',
                    '_order': 1,
            },
            'android.profile.storepass': {
                    'type': 'string',
                    '_password': True,
                    '_sensitive': True,
                    'description': 'The password for your release keystore',
                    'title': 'Keystore password',
                    '_order': 2,
            },
            'android.profile.keyalias': {
                    'type': 'string',
                    'description': 'The alias of your release key',
                    'title': 'Key alias',
                    '_order': 3,
            },
            'android.profile.keypass': {
                    'type': 'string',
                    '_password': True,
                    '_sensitive': True,
                    'description': 'The password for your release key',
                    'title': 'Key password',
                    '_order': 4,
            }
    }

    signing_info = lib.get_or_ask_for_local_config(
            build,
            required_info,
            question_title='Enter details for signing your app',
    )

    signing_info['android.profile.keystore'] = lib.expand_relative_path(
            build, signing_info['android.profile.keystore']
    )

    # add some optional values for signing android app bundles
    config = build.tool_config.all_config().get("android", {})
    signing_info['android.dontsign']  = config.get("dontsign", False)
    config = config.get("profile", {})
    signing_info['android.profile.sigalg']    = config.get("sigalg", None)
    signing_info['android.profile.digestalg'] = config.get("digestalg", None)

    return signing_info


# - tasks ---------------------------------------------------------------------

@task
def clean_android(build):
    pass


@task
def run_android(build, build_type_dir, sdk, device, interactive=True, purge=False):
    # TODO: remove sdk parameter from here and call sites, information is
    #       contained in build.tool_config already
    # TODO: remove build_type_dir from method and call sites, doesn't seem to
    #       be used anywhere
    # TODO: remove interactive parameter. this information is contained in the
    #       build, but we should never use this anyway, as we can now interact
    #       with the toolkit from here

    java, sdk = _find_or_install_sdk(build)
    target = list(build.enabled_platforms)[0]

    LOG.info("Starting ADB if not running")
    _run_detached([sdk.adb, "start-server"], wait=True)

    LOG.info("Looking for Android device")
    available_devices = _get_available_devices(sdk)

    if not available_devices and device and device.lower() == "emulator":
        LOG.info("Using android emulator")
        created = _create_avd_if_necessary(build, sdk)
        _launch_avd(build, sdk)
        if created:
            LOG.info(NEW_AVD_TEMPLATE)
            return
        return run_android(build, build_type_dir, sdk, device, interactive=interactive)

    if not available_devices:
        should_launch_emulator = _prompt_user_to_attach_device(build, sdk)
        if should_launch_emulator:
            created = _create_avd_if_necessary(build, sdk)
            _launch_avd(build, sdk)
            if created:
                LOG.info(NEW_AVD_TEMPLATE)
                return
        return run_android(build, build_type_dir, sdk, device, interactive=interactive)

    if device and device == "emulator":
        emulators = [d for d in available_devices if d.startswith("emulator")]
        if not emulators:
            LOG.info("No emulator found")
            created = _create_avd_if_necessary(build, sdk)
            _launch_avd(build, sdk)
            if created:
                LOG.info(NEW_AVD_TEMPLATE)
                return
            return run_android(build, build_type_dir, sdk, device, interactive=interactive)
        else:
            device = emulators[0]

    if device:
        if device in available_devices:
            chosen_device = device
            LOG.info("Using specified android device %s" % chosen_device)
        else:
            LOG.error("No such device '%s'" % device)
            LOG.error("The available devices are:")
            LOG.error("\n".join(available_devices))
            raise AndroidError
    else:
        chosen_device = available_devices[0]
        LOG.info("No android device specified, defaulting to %s" % chosen_device)

    with lib.temp_file(".apk") as out_apk_name:
        _create_apk(build, java, sdk, target, out_apk_name, interactive=interactive)
        package_name = _generate_package_name(build)

        # If required remove previous installs from device
        if purge:
            _run_adb([sdk.adb, "uninstall", package_name], 30, sdk)

        # Install APK to device
        LOG.info("Installing apk")
        command = [
            sdk.adb,
            "-s", chosen_device,
            "install",
            "-r", out_apk_name
        ]
        try:
            proc_std = _run_adb(command, 60, sdk)
        except Exception as e:
            LOG.error("Error starting app: %s" % e)
            raise AndroidError("Try running your app again once the device is available.")

    LOG.debug(proc_std)

    # Start app on device
    command = [
        sdk.adb,
        "-s", chosen_device,
        "shell", "am", "start",
        "-n", package_name + "/io.trigger.forge.android.core.ForgeActivity"
    ]
    proc_std = _run_adb(command, 60, sdk)

    LOG.debug(proc_std)

    #follow log
    _follow_log(sdk, chosen_device)


@task
def package_android(build):
    java, sdk = _find_or_install_sdk(build)
    target = list(build.enabled_platforms)[0]

    lib_path = path.normpath(path.join(".template", "lib"))
    dev_dir = path.normpath(path.join("development", target))
    output = path.abspath(_generate_path_to_output_apk(build))
    signing_info = _lookup_or_prompt_for_signing_info(build)

    LOG.info("Creating Android .apk file for target: %s" % target)
    package_name = _generate_package_name(build)
    #zip
    with lib.temp_file() as zipf_name:
        _create_apk(build, java, sdk, target, zipf_name, interactive=False)

        with lib.temp_file() as compressed_zipf_name:
            with zipfile.ZipFile(zipf_name, "r") as zipf:
                with zipfile.ZipFile(compressed_zipf_name, "w") as compressed_zipf:
                    for name in zipf.namelist():
                        compress_type = zipfile.ZIP_STORED
                        if name == "classes.dex":
                            compress_type = zipfile.ZIP_DEFLATED
                        compressed_zipf.writestr(name, zipf.read(name), compress_type=compress_type)

            with lib.temp_file() as aligned_zipf_name:
                # align
                _align_apk(sdk, compressed_zipf_name, aligned_zipf_name)

                # create output directory for APK if necessary
                _create_output_directory(output)

                # sign
                _sign_zipf_release(lib_path, java, aligned_zipf_name, output, signing_info)

                LOG.info("created APK: {output}".format(output=output))
                return output

@task
def bundle_android(build):
    target = list(build.enabled_platforms)[0]
    LOG.info("Creating Android .aab file for target: %s" % target)

    java, sdk = _find_or_install_sdk(build)
    jarsigner, searched = sdkmanager.locate_jarsigner(build)
    if jarsigner is None:
        raise AndroidError(NO_JARSIGNER_TEMPLATE.format(searched="\n".join(searched)))
    LOG.info("Using jarsigner: %s" % str(jarsigner))
    signing_info = _lookup_or_prompt_for_signing_info(build)

    lib_path = path.normpath(path.join(".template", "lib"))
    dev_path = path.normpath(path.join("development", "android_bundle"))
    package_name = _generate_package_name(build)
    output = path.abspath(_generate_path_to_output_aab(build))

    # 0. fetch bundletool.jar if needed
    bundletool = ensure_lib_available(build, "bundletool-1.7.0.jar")

    # 1. zip up aab base/ directory
    base_path = path.normpath(path.join(dev_path, "base"))
    with lib.temp_dir() as temp_dir:
        base_zip = path.join(temp_dir, "base.zip")
        with zipfile.ZipFile(base_zip, "w") as zf:
            for dirname, subdirs, files in os.walk(base_path):
                dest_path = path.relpath(dirname, base_path)
                if dirname != base_path:
                    LOG.debug("Adding: %s => %s" % (dirname, dest_path))
                    zf.write(dirname, dest_path)
                for filename in files:
                    zf.write(os.path.join(dirname, filename), os.path.join(dest_path, filename))

        # 2. create android app bundle file
        LOG.info("Creating android app bundle file")
        _build_aab(java, bundletool, base_zip, output)

        # 3. sign android app bundle file
        LOG.info("Signing android app bundle file")
        _sign_aab(jarsigner, signing_info, output)

        # 4. validate android app bundle file
        LOG.info("Validating android app bundle file")
        _validate_aab(java, bundletool, output)

        LOG.info("Created AAB: {output}".format(output=output))
        return output
