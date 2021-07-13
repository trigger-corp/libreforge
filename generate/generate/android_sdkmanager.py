import collections
from copy import deepcopy
from glob import glob
import logging
import os
from os import path
import shutil
import subprocess
import sys

from module_dynamic import lib
from module_dynamic import utils

LOG = logging.getLogger(__name__)

class AndroidSdkError(lib.BASE_EXCEPTION):
    pass


# - android sdk components ----------------------------------------------------

android_sdk_packages = [
    "platform-tools",     # adb
    "build-tools;30.0.3", # aapt, android, apksigner, emulator, zipalign
    # TODO "build-tools;31.0.0-rc5", # aapt, android, apksigner, emulator, zipalign
]

android_emulator_packages = [
    "emulator"
]

if sys.platform.startswith("win32"):
    # for some reason this is currently (10/2020) the latest image that actually installs on windows
    android_emulator_image = "system-images;android-27;default;x86_64"
else:
    android_emulator_image = "system-images;android-30;google_apis;x86_64"

android_sdk_binaries = {
    "aapt": [
        path.join("build-tools", "*", "aapt"),
        path.join("build-tools", "*", "aapt.exe")
    ],
    "adb": [
        path.join("platform-tools", "adb"),
        path.join("platform-tools", "adb.exe"),
    ],
    "apksigner": [
        path.join("build-tools", "*", "apksigner"),
        path.join("build-tools", "*", "apksigner.bat"),
    ],
    "apksigner_jar": [
        path.join("build-tools", "*", "lib", "apksigner.jar"),
    ],
    "avdmanager": [
        path.join("tools", "bin", "avdmanager"),
        path.join("tools", "bin", "avdmanager.bat"),
    ],
    "emulator": [
        path.join("tools", "emulator"),
        path.join("tools", "emulator.exe"),
    ],
    "sdkmanager": [
        path.join("tools", "bin", "sdkmanager"),
        path.join("tools", "bin", "sdkmanager.bat"),
    ],
    "zipalign": [
        path.join("build-tools", "*", "zipalign"),
        path.join("build-tools", "*", "zipalign.exe"),
    ]
}

AndroidSdkBinaries = collections.namedtuple("AndroidSdkBinaries", sorted(android_sdk_binaries.keys()))


# - platform support ----------------------------------------------------------

platform_sdkmanager_url = {
    "darwin": "https://dl.google.com/android/repository/commandlinetools-mac-6609375_latest.zip",
    "linux":  "https://dl.google.com/android/repository/commandlinetools-linux-6609375_latest.zip",
    "win32":  "https://dl.google.com/android/repository/commandlinetools-win-6609375_latest.zip",
}

platform_avd_root = {
    "darwin":  path.expanduser("~/.forge/darwin/Android/avd"),
    "linux":   path.expanduser("~/.forge/linux/Android/avd"),
    "win32":   "{appdata}\\Local\\TriggerCorp\\Android\\avd".format(appdata=os.getenv("APPDATA")),
}

platform_local_sdk_root = {
    "darwin":  path.expanduser("~/.forge/darwin/Android/sdk"),
    "linux":   path.expanduser("~/.forge/linux/Android/sdk"),
    "win32":   "{appdata}\\Local\\TriggerCorp\\Android\\Sdk".format(appdata=os.getenv("APPDATA")),
}

platform_system_sdk_root = {
    "darwin": path.expanduser("~/Library/Android/sdk"),
    "linux":  path.expanduser("~/Android/Sdk"),
    "win32":  "{appdata}\\Local\\Android\\Sdk".format(appdata=os.getenv("APPDATA")),
}

platform_java_binary = {
    "darwin": "java",
    "linux":  "java",
    "win32":  "java.exe"
}

platform_jarsigner_binary = {
    "darwin": "jarsigner",
    "linux":  "jarsigner",
    "win32":  "jarsigner.exe"
}

platform_emulator_packages = {
    "darwin": [ "platforms;android-30", "extras;intel;Hardware_Accelerated_Execution_Manager" ],
    "linux":  [ "platforms;android-30" ],
    "win32":  [ "platforms;android-27", "extras;intel;Hardware_Accelerated_Execution_Manager" ]
}



# - exports -------------------------------------------------------------------

def locate_jdk_binary(build, platform_binaries):
    platform_binary = utils.value_for_platform(platform_binaries)

    # look in path
    which_binary = utils.which(platform_binary)
    if which_binary:
        return which_binary, None

    # look in common locations
    locations = []
    locations += os.getenv("JAVA_HOME") and [ os.getenv("JAVA_HOME") ] or [ ]
    locations += os.getenv("JDK_HOME")  and [ os.getenv("JDK_HOME")  ] or [ ]
    locations += sys.platform.startswith("win32") and [
        path.join("C:\\" "Program Files", "Java", "*"),
        path.join("C:\\" "Program Files (x86)", "Java", "*"),
    ] or []

    LOG.info("Looking for java in:")
    map(LOG.info, locations)
    locations = map(glob, locations)                    # glob binary paths
    locations = _flatten(locations)                     # flatten glob results

    for location in locations:
        binary = path.join(location, "bin", platform_binary)
        if path.isfile(binary) and os.access(binary, os.X_OK):
            return binary, location

    return None, locations

def locate_java(build):
    return locate_jdk_binary(build, platform_java_binary)

def locate_jarsigner(build):
    return locate_jdk_binary(build, platform_jarsigner_binary)


def locate_sdk(build):
    # order of preference is:
    #  1. local_config.json
    #  2. local android studio installation
    #  3. ANDROID_HOME environment variable
    #  4. ANDROID_SDK_ROOT environment variable
    #  5. Android Studio SDK installation
    sdk_roots_all = filter(None, [
        build.tool_config.get("android.sdk"),
        utils.value_for_platform(platform_local_sdk_root),
        # Also see: https://developer.android.com/studio/command-line/variables
        os.getenv("ANDROID_HOME"),
        os.getenv("ANDROID_SDK_ROOT"),
        utils.value_for_platform(platform_system_sdk_root),
    ])
    sdk_roots = filter(path.isdir, sdk_roots_all) # remove non-existent paths

    LOG.debug("Looking for Android SDK in: %s" % sdk_roots)

    def search(sdk_root, binary, locations):
        locations = map(lambda l: path.join(sdk_root, l), locations)
        locations = map(glob, locations)                    # glob binary paths
        locations = _flatten(locations)                     # flatten glob results
        location = len(locations) and locations[-1] or None # highest version of each glob result
        return binary, location

    for sdk_root in sdk_roots:
        ret = map(lambda kv: search(sdk_root, kv[0], kv[1]), android_sdk_binaries.iteritems())
        ret = filter(lambda b: b[1] != None, ret)
        if len(android_sdk_binaries) == len(ret):
            return AndroidSdkBinaries(**dict(ret)), sdk_root

    return None, sdk_roots_all



def install(build):
    LOG.info("Install SDK for platform: %s " % sys.platform)

    try:
        android_sdk_root = utils.value_for_platform(platform_local_sdk_root)
    except AndroidSdkError as e:
        LOG.debug(e)
        raise AndroidSdkError("Android SDK installation is not supported for your platform '%s'. You will need to install it manually." % sys.platform)

    if path.isdir(android_sdk_root):
        LOG.info("Remove existing installation: %s" % android_sdk_root)
        shutil.rmtree(android_sdk_root)

    cmdline_tools_path = path.join(android_sdk_root, "cmdline-tools")
    if sys.platform.startswith("win32"):
        sdkmanager_path = path.join(cmdline_tools_path, "tools", "bin", "sdkmanager.bat")
    else:
        sdkmanager_path = path.join(cmdline_tools_path, "tools", "bin", "sdkmanager")

    if not path.isfile(sdkmanager_path):
        LOG.info("Create directory: %s" % android_sdk_root)
        os.makedirs(android_sdk_root)

        LOG.info("Create directory: %s" % cmdline_tools_path)
        os.makedirs(cmdline_tools_path)

        source = utils.value_for_platform(platform_sdkmanager_url)
        destination = path.join(cmdline_tools_path, "commandlinetools.zip")
        LOG.info("Download Android SDK Manager to: %s" % destination)
        lib.download_with_progress_bar("Downloading Android SDK", source, destination)

        LOG.info("Extract Android SDK Manager to: %s" % cmdline_tools_path)
        with utils.BetterZipFile(destination) as zip:
            zip.extractall(cmdline_tools_path)

        LOG.info("Delete: %s" % destination)
        os.remove(destination)

    # setup environment
    env = deepcopy(os.environ)
    LOG.info("Set: ANDROID_SDK_ROOT = %s" % android_sdk_root)
    env["ANDROID_SDK_ROOT"] = android_sdk_root
    java_binary, java_home = locate_java(build)
    if java_home:
        LOG.info("Set: JAVA_HOME = %s" % java_home)
        env["JAVA_HOME"] = java_home

    # run sdkmanager
    cmd = [ sdkmanager_path, "--install" ] + android_sdk_packages
    process = lib.PopenWithoutNewConsole(cmd,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT,
                                         env=env,
                                         cwd=cmdline_tools_path)
    stdout = utils.Unbuffered(sys.stdout)
    _map_file(process.stdout, lambda c: stdout.write(c))

    LOG.info("Remove sdk installer: %s" % cmdline_tools_path)
    shutil.rmtree(cmdline_tools_path)

    return locate_sdk(build)


def install_emulator_image(build):
    sdk, searched = locate_sdk(build)
    LOG.info("Using Android SDK: %s" % searched)

    packages = [ android_emulator_image ]
    packages += android_emulator_packages
    packages += utils.value_for_platform(platform_emulator_packages)

    # setup environment
    env = deepcopy(os.environ)
    java_binary, java_home = locate_java(build)
    if java_home:
        LOG.info("Set: JAVA_HOME = %s" % java_home)
        env["JAVA_HOME"] = java_home

    # run sdkmanager
    cmd = [ sdk.sdkmanager, "--install" ] + packages
    process = lib.PopenWithoutNewConsole(cmd,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT)
    stdout = utils.Unbuffered(sys.stdout)
    _map_file(process.stdout, lambda c: stdout.write(c))


# - helpers -------------------------------------------------------------------

def _map_file(f, fn):
    """read file one character at a time and map a function over it"""
    while True:
        c = f.read(1)
        if not c:
            break
        fn(c)


def _flatten(l):
    return [item for sublist in l for item in sublist]
