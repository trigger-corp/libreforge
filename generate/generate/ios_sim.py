import os
import logging
import subprocess
import re
import json

from module_dynamic.utils import which

LOG = logging.getLogger(__name__)

def _run_command(cmd):
    """given shell command, returns communication tuple of stdout and stderr"""
    return subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE).communicate()


def check_xcrun():
    xcrun = which("xcrun")
    if not xcrun:
        raise Exception(__name__, "xcrun not found", "Please check your Xcode installation.")
    return xcrun

def device(devicetype_id=None, devicesdk=None):
    error = "Could not locate simulator for: %s %s" % (devicetype_id, devicesdk)
    resolution = "Please check your Xcode and iOS simulator setup"

    output = _run_command(["xcrun", "simctl", "list", "--json"])
    if output[1] != "":
        raise Exception(__name__, output[1], "")

    simulators = json.loads(output[0])
    if not simulators["runtimes"] or not simulators["devices"] or not simulators["devicetypes"]:
        raise Exception(__name__, error + " (failed to find any simulators at all)", resolution)

    if not devicetype_id:
        return simulators

    # find devicetype
    try:
        devicetype = (item for item in simulators["devicetypes"] if item["identifier"] == devicetype_id).next()
    except:
        raise Exception(__name__, error + " (failed to find devicetype)", resolution)

    # find runtime
    if devicesdk:
        try:
            runtime = (item for item in simulators["runtimes"] if item["name"] == devicesdk).next()
        except:
            runtime = None
    else:
        runtime = simulators["runtimes"][0]
    if not runtime:
        raise Exception(__name__, error + " (failed to find runtime)", resolution)

    # find device
    try:
        device = (item for item in simulators["devices"][runtime["identifier"]] if item["name"] == devicetype["name"]).next()
        device["runtime"] = runtime["name"]
    except:
        raise Exception(__name__, error + " (failed to find device)", resolution)

    return device


def start(device=None):
    if not device:
        raise Exception(__name__, "no device specified", "")

    # boot simulator
    cmd = [ "xcrun", "simctl", "boot", device["udid"] ]
    output = _run_command(cmd)
    if output[1] != "" and not "state: Booted" in output[1]:
           raise Exception(__name__, output[1], "")

    # open simulator app
    output = _run_command(["open", "-a", "Simulator"])
    if output[1] != "":
        raise Exception(__name__, output[1], "")

    LOG.debug("Started simulator with command: %s -> %s" % (cmd, output))



def install(device, bundle):
    output = _run_command(["xcrun", "simctl", "install", device["udid"], bundle])
    if output[1] != "":
        raise Exception(__name__, output[1], "")


def launch(device, package):
    output = _run_command(["xcrun", "simctl", "launch", device["udid"], package])
    if output[1] != "":
        raise Exception(__name__, output[1], "")


def log(device):
    return "{home}/Library/Logs/CoreSimulator/{device}/system.log".format(
            home=os.path.expanduser("~"),
            device=device["udid"]
    )
