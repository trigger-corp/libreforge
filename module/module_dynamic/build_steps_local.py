import shutil
import os

import pystache
import json
from xml.etree import ElementTree

import build_steps

# Needed to prevent elementtree screwing with namespace names
ElementTree.register_namespace('android', 'http://schemas.android.com/apk/res/android')
ElementTree.register_namespace('tools', 'http://schemas.android.com/tools')


def copy_file_from_src(build_params, filename, dest):
    filename = pystache.render(filename, build_params['app_config'])
    dest = pystache.render(dest, build_params['app_config'])
    if os.path.isfile(os.path.join(build_params['src_path'], filename)):
        if not os.path.exists(os.path.dirname(os.path.join(build_params['project_path'], dest))):
            os.makedirs(os.path.dirname(os.path.join(build_params['project_path'], dest)))
        shutil.copy2(os.path.join(build_params['src_path'], filename), os.path.join(build_params['project_path'], dest))
    elif filename != "":
        raise Exception("Could not find file: %s" % filename)


def copy_file_from_assets(build_params, filename, dest):
    # TODO implement
    return copy_file_from_src(build_params, filename, dest)


def icons_handle_prerendered(build_params):
    if "ios" in build_params['app_config']["modules"]["icons"]["config"] and build_params['app_config']["modules"]["icons"]["config"]["ios"].get("prerendered"):
        build_steps.set_in_biplist(
                build_params,
                filename=os.path.join(build_params['project_path'], "Info.plist"),
                key="UIPrerenderedIcon",
                value=True)
        build_steps.set_in_biplist(
                build_params,
                filename=os.path.join(build_params['project_path'], "Info.plist"),
                key="CFBundleIcons.CFBundlePrimaryIcon.UIPrerenderedIcon",
                value=True)


# - we can no longer mutate AndroidManifest.xml from the client-side as Gradle build encodes it -------
# def add_attributes_to_xml(build_params, file, attributes, to):
#       '''add attributes to elements in an XML file

#       :param file: filename or file object
#       :param attributes: dict containing attributes
#       :param to: sub element tag name or path we will append attributes to
#       '''

#       ns = "{http://schemas.android.com/apk/res/android}"
#       xml = ElementTree.ElementTree()
#       xml.parse(file)
#       if to is None:
#               el = xml.getroot()
#       else:
#               el = xml.find(to, dict((v, k) for k, v in ElementTree._namespace_map.items()))
#               if el is None:
#                       el = xml.getroot()
#                       for node in to.split("/"):
#                               found = el.find(node, dict((v, k) for k, v in ElementTree._namespace_map.items()))
#                               if found is None:
#                                       el = ElementTree.SubElement(el, node)
#                               else:
#                                       el = found
#       for attribute in attributes:
#               if isinstance(attributes[attribute], str) or isinstance(attributes[attribute], unicode):
#                       attributes[attribute] = pystache.render(attributes[attribute], build_params['app_config'])
#               if attribute.replace("android:", ns, 1) in el.attrib:
#                       el.attrib[attribute.replace("android:", ns, 1)] = attributes[attribute]
#               else:
#                       el.attrib[attribute] = attributes[attribute]
#       xml.write(file)


# def android_add_to_application_manifest_attributes(build_params, attributes):
#               add_attributes_to_xml(build_params,
#                       file=os.path.join(build_params['project_path'], 'AndroidManifest.xml'),
#                       attributes=attributes,
#                       to="application")

# def android_add_to_activity_manifest_attributes(build_params, attributes):
#               add_attributes_to_xml(build_params,
#                       file=os.path.join(build_params['project_path'], 'AndroidManifest.xml'),
#                       attributes=attributes,
#                       to="application/activity")
# - we can no longer mutate AndroidManifest.xml from the client-side as Gradle build encodes it -------
