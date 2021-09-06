from xml.etree import ElementTree
import glob
import json
import biplist
import os
import ast
import codecs

import pystache

import utils
from xcode import XcodeProject

# Needed to prevent elementtree screwing with namespace names
ElementTree.register_namespace('android', 'http://schemas.android.com/apk/res/android')
ElementTree.register_namespace('tools', 'http://schemas.android.com/tools')

def add_element_to_xml(build_params, file, element, to=None, unless=None):
    '''add new element to an XML file

    :param file: filename or file object
    :param element: dict containing tag and optionally attributes, text and children
    :param to: sub element tag name or path we will append to
    :param unless: don't add anything if this tag name or path already exists
    '''

    def create_element(tag, attributes={}, text=None, children=[]):
        for attribute in attributes:
            if isinstance(attributes[attribute], str) or isinstance(attributes[attribute], unicode):
                attributes[attribute] = pystache.render(attributes[attribute], build_params['app_config'])
        element = ElementTree.Element(tag, attributes)
        if text is not None:
            if isinstance(text, str) or isinstance(text, unicode):
                text = pystache.render(text, build_params['app_config'])
            element.text = text
        for child in children:
            element.append(create_element(**child))

        return element
    xml = ElementTree.ElementTree()
    xml.parse(file)

    if to is not None:
        el = xml.find(to, dict((v, k) for k, v in ElementTree._namespace_map.items()))
        if el is None:
            raise ValueError("add_element_to_xml could not find: %s" % to)
    else:
        el = xml.getroot()

    existing = xml.find(element["tag"], dict((v, k) for k, v in ElementTree._namespace_map.items()))
    if unless is None and existing is not None and "children" in element:
        # already exists, append
        for child in element["children"]:
            new_el = create_element(**child)
            existing.append(new_el)
        xml.write(file)

    elif unless is None or xml.find(unless, dict((v, k) for k, v in ElementTree._namespace_map.items())) is None:
        new_el = create_element(**element)
        el.append(new_el)
        xml.write(file)


def set_text_for_xml_element(build_params, file, text, to=None):
    '''sets the text for an element to an XML file

    :param file: filename or file object
    :param text: a string containing the text to set
    :param to: sub element tag name or path we will set the text for
    '''

    xml = ElementTree.ElementTree()
    xml.parse(file)
    if to is not None:
        el = xml.find(to, dict((v, k) for k, v in ElementTree._namespace_map.items()))
        if el is None:
            raise ValueError("set_text_for_xml_element could not find: %s" % to)
    else:
        el = xml.getroot()
    el.text = pystache.render(text, build_params['app_config'])
    xml.write(file)


def add_to_json_array(build_params, filename, key, value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = pystache.render(value, build_params['app_config'])

    found_files = glob.glob(filename)
    for found_file in found_files:
        file_json = {}
        with open(found_file, "r") as opened_file:
            file_json = json.load(opened_file)
            # TODO: . separated keys?
            file_json[key].append(value)
        with open(found_file, "w") as opened_file:
            json.dump(file_json, opened_file, indent=2, sort_keys=True)


def android_add_proguard_rule(build_params, rule):
    with open("proguard-project.txt", "a") as proguard_file:
        proguard_file.write("\n")
        proguard_file.write(rule)


def android_add_permission(build_params, permission):
    add_element_to_xml(build_params,
            file='AndroidManifest.xml',
            element={
                    "tag": "uses-permission",
                    "attributes": {"android:name": permission},
            },
            unless="uses-permission/[@android:name='%s']" % permission
    )


def android_add_feature(build_params, feature, required="false"):
    if required == "true":
        unless = "uses-feature/[@android:name='%s']/[@android:required='true']" % feature
    else:
        unless = "uses-feature/[@android:name='%s']" % feature

    add_element_to_xml(build_params,
            file='AndroidManifest.xml',
            element={
                    "tag": "uses-feature",
                    "attributes": {"android:name": feature, "android:required": required},
            },
            unless=unless)


def android_add_to_application_manifest(build_params, element):
    add_element_to_xml(build_params,
            file='AndroidManifest.xml',
            element=element,
            to="application")


def android_add_to_activity_manifest(build_params, element):
    add_element_to_xml(build_params,
            file='AndroidManifest.xml',
            element=element,
            to="application/activity")


def android_add_to_manifest(build_params, element):
    add_element_to_xml(build_params,
            file='AndroidManifest.xml',
            element=element)

def android_add_activity(build_params, activity_name, attributes={}):
    attributes['android:name'] = activity_name
    add_element_to_xml(build_params,
            file='AndroidManifest.xml',
            element={
                    "tag": "activity",
                    "attributes": attributes,
            },
            to="application")


def android_add_service(build_params, service_name, attributes={}):
    attributes['android:name'] = service_name
    add_element_to_xml(build_params,
            file='AndroidManifest.xml',
            element={
                    "tag": "service",
                    "attributes": attributes,
            },
            to="application")


def android_add_receiver(build_params, receiver_name, attributes={}, intent_filters=[]):
    attributes['android:name'] = receiver_name
    add_element_to_xml(build_params,
            file='AndroidManifest.xml',
            element={
                    "tag": "receiver",
                    "attributes": attributes,
            },
            to="application")

    if len(intent_filters) != 0:
        add_element_to_xml(build_params,
                file='AndroidManifest.xml',
                element={
                        "tag": "intent-filter",
                },
                to="application/receiver/[@android:name='%s']" % receiver_name)

        for intent in intent_filters:
            for tag in intent:
                add_element_to_xml(build_params,
                        file='AndroidManifest.xml',
                        element={
                                "tag": tag,
                                "attributes": {"android:name": intent[tag]},
                        },
                        to="application/receiver/[@android:name='%s']/intent-filter" % receiver_name)


def android_add_gradle_dependency(build_params, name, ext=None):
    gradle = {}
    gradle_json = "gradle.json"
    if os.path.exists(gradle_json):
        with open(gradle_json) as f:
            gradle = json.load(f)
    if not "dependencies" in gradle:
        gradle["dependencies"] = []
    if ext is None:
        gradle["dependencies"].append(name)
    else:
        gradle["dependencies"].append({
                "name": name,
                "ext": ext
        })
    with open(gradle_json, "w") as f:
        json.dump(gradle, f, indent=4, sort_keys=True)


def android_add_gradle_plugin(build_params, name, classpath):
    gradle = {}
    gradle_json = "gradle.json"
    if os.path.exists(gradle_json):
        with open(gradle_json) as f:
            gradle = json.load(f)
    if not "gradlePlugins" in gradle:
        gradle["gradlePlugins"] = []
    gradle["gradlePlugins"].append({
        "name": name,
        "classpath": classpath
    })
    with open(gradle_json, "w") as f:
        json.dump(gradle, f, indent=4, sort_keys=True)


def android_add_gradle_exclude_jar(build_params, name, ext=None):
    gradle = {}
    gradle_json = "gradle.json"
    if os.path.exists(gradle_json):
        with open(gradle_json) as f:
            gradle = json.load(f)
    if not "exclude_jars" in gradle:
        gradle["exclude_jars"] = []
    gradle["exclude_jars"].append(name)
    with open(gradle_json, "w") as f:
        json.dump(gradle, f, indent=4, sort_keys=True)


def android_add_gradle_manifest_placeholder(build_params, key, value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = pystache.render(value, build_params['app_config'])
    gradle = {}
    gradle_json = "gradle.json"
    if os.path.exists(gradle_json):
        with open(gradle_json) as f:
            gradle = json.load(f)
    if not "manifestPlaceholders" in gradle:
        gradle["manifestPlaceholders"] = {}
    gradle["manifestPlaceholders"][key] = value
    with open(gradle_json, "w") as f:
        json.dump(gradle, f, indent=4, sort_keys=True)


# TODO use version in customer_tasks.py
def android_set_min_sdk_version(build_params, value):
    gradle = {}
    gradle_json = "gradle.json"
    if os.path.exists(gradle_json):
        with open(gradle_json) as f:
            gradle = json.load(f)
    if not "minSdkVersion" in gradle.keys():
        gradle["minSdkVersion"] = value
    elif "minSdkVersion" in gradle.keys() and int(value) > int(gradle["minSdkVersion"]):
        gradle["minSdkVersion"] = value

    with open(gradle_json, "w") as f:
        json.dump(gradle, f, indent=4, sort_keys=True)


def ios_add_url_handler(build_params, scheme, filename='ForgeInspector/ForgeInspector-Info.plist'):
    if isinstance(scheme, str) or isinstance(scheme, unicode):
        scheme = pystache.render(scheme, build_params['app_config'])

    found_files = glob.glob(filename)
    for found_file in found_files:
        plist = biplist.readPlist(found_file)
        if "CFBundleURLTypes" in plist:
            plist["CFBundleURLTypes"][0]["CFBundleURLSchemes"].append(scheme)
        else:
            plist["CFBundleURLTypes"] = [{"CFBundleURLSchemes": [scheme]}]
        biplist.writePlist(plist, found_file)


def ios_add_url_handlers(build_params, schemes, filename='ForgeInspector/ForgeInspector-Info.plist'):
    if isinstance(schemes, str) or isinstance(schemes, unicode):
        schemes = pystache.render(schemes, build_params['app_config'])
        schemes = ast.literal_eval(schemes) if len(schemes) else []

    for scheme in schemes:
        ios_add_url_handler(build_params, scheme, filename)


def ios_add_background_mode(build_params, mode, filename='ForgeInspector/ForgeInspector-Info.plist'):
    if isinstance(mode, str) or isinstance(mode, unicode):
        mode = pystache.render(mode, build_params['app_config'])

    found_files = glob.glob(filename)
    for found_file in found_files:
        plist = biplist.readPlist(found_file)
        if "UIBackgroundModes" in plist:
            plist["UIBackgroundModes"].append(mode)
        else:
            plist["UIBackgroundModes"] = [mode]
        biplist.writePlist(plist, found_file)

def _plist_merge(x, y):
    if (isinstance(x, list) and isinstance(y, list)):
        return x + y
    elif (isinstance(x, dict) and isinstance(y, dict)):
        z = x.copy()
        z.update(y)
        return z
    else:
        return y


def set_in_biplist(build_params, filename, key, value):
    if isinstance(value, str) or isinstance(value, unicode):
        value = pystache.render(value, build_params['app_config'])
        # TODO Horrible workaround for pystache.render only operating on strings
        if value == "True":
            value = True
        elif value == "False":
            value = False
        elif value == "":
            return

    found_files = glob.glob(filename)
    for found_file in found_files:
        plist = biplist.readPlist(found_file)
        plist = utils.transform(plist,
                                                        key,
                                                        lambda x: _plist_merge(x, value),
                                                        allow_set=True)
        biplist.writePlist(plist, found_file)


def set_in_info_plist(build_params, key, value):
    set_in_biplist(build_params, "ForgeInspector/ForgeInspector-Info.plist", key, value)


def ios_configure_ats(build_params, entries):
    if (isinstance(entries, str) or isinstance(entries, unicode)):
        entries = pystache.render(entries, build_params['app_config'])
        entries = ast.literal_eval(entries) if len(entries) else []

    for entry in entries:
        domain = entry.pop("domain", None)
        set_in_biplist(build_params, "ForgeInspector/ForgeInspector-Info.plist",
                                   "NSAppTransportSecurity.NSExceptionDomains", {domain: entry})


def ios_add_i8n_plist(build_params, lang, key, string):
    if isinstance(string, str) or isinstance(string, unicode):
        string = pystache.render(string, build_params['app_config'])
    filepath = os.path.join("ForgeInspector", "i8n", "%s.lproj" % lang, "InfoPlist.strings")
    if os.path.isfile(filepath):
        with codecs.open(filepath, encoding="utf-8", mode="a") as i8n_strings:
            i8n_strings.write(u'"{key}" = "{string}";\n'.format(key=key, string=string))


def add_ios_system_framework(build_params, framework):
    xcode_project = XcodeProject('ForgeInspector.xcodeproj/project.pbxproj')
    if framework.endswith('.framework'):
        xcode_project.add_framework("System/Library/Frameworks/"+framework, "SDKROOT")
    elif framework.endswith('.dylib'):
        xcode_project.add_framework("usr/lib/"+framework, "SDKROOT")
    else:
        raise Exception("Unsupported iOS framework type for '%s', must end in .framework or .dylib." % framework)
    xcode_project.save()


def add_osx_system_framework(build_params, framework):
    xcode_project = XcodeProject('ForgeInspector.xcodeproj/project.pbxproj')
    if framework.endswith('.framework'):
        xcode_project.add_framework("System/Library/Frameworks/"+framework, "SDKROOT")
    elif framework.endswith('.dylib'):
        xcode_project.add_framework("usr/lib/"+framework, "SDKROOT")
    else:
        raise Exception("Unsupported OSX framework type for '%s', must end in .framework or .dylib." % framework)
    xcode_project.save()


# - in their infinite genius Apple have moved icon assets to a proprietary resource file --------------

def ios_populate_iconset(build_params, filename, icon):
    if isinstance(filename, str) or isinstance(filename, unicode):
        filename = pystache.render(filename, build_params['app_config'])

    # sanitize inputs
    filename = os.path.normcase(filename)
    if filename.startswith("/") or (".." in filename):
        raise Exception("Asset filename '%s' has to be a relative path" % filename)
    icon = os.path.basename(icon)

    from shutil import copy
    source = os.path.join(build_params["assets_path"], filename)
    dest   = os.path.join("ForgeInspector", "Images.xcassets", "AppIcon.appiconset", icon)
    copy(source, dest)


# - ditto for Google services  ------------------------------------------------------------------------

def populate_file_from_assets(build_params, filename, dest):
    if isinstance(filename, str) or isinstance(filename, unicode):
        filename = pystache.render(filename, build_params['app_config'])

    # sanitize inputs
    filename = os.path.normcase(filename)
    if filename.startswith("/") or (".." in filename):
        raise Exception("Asset filename '%s' has to be a relative path" % filename)
    dest = os.path.normcase(dest)
    if dest.startswith("/") or  (".." in dest):
        raise Exception("Asset destination '%s' has to be a relative path" % dest)

    source = os.path.join(build_params["assets_path"], filename)
    if not os.path.exists(source):
        return

    from shutil import copy
    print("Populating file '%s' from asset '%s" % (source, dest))
    copy(source, dest)


# - we can no longer mutate AndroidManifest.xml from the client-side as Gradle build encodes it -------

def add_attributes_to_xml(build_params, file, attributes, to):
    '''add attributes to elements in an XML file

    :param file: filename or file object
    :param attributes: dict containing attributes
    :param to: sub element tag name or path we will append attributes to
    '''
    ns = "{http://schemas.android.com/apk/res/android}"
    xml = ElementTree.ElementTree()
    xml.parse(file)
    if to is None:
        el = xml.getroot()
    else:
        el = xml.find(to, dict((v, k) for k, v in ElementTree._namespace_map.items()))
        if el is None:
            el = xml.getroot()
            for node in to.split("/"):
                found = el.find(node, dict((v, k) for k, v in ElementTree._namespace_map.items()))
                if found is None:
                    el = ElementTree.SubElement(el, node)
                else:
                    el = found
    for attribute in attributes:
        if isinstance(attributes[attribute], str) or isinstance(attributes[attribute], unicode):
            attributes[attribute] = pystache.render(attributes[attribute], build_params['app_config'])
        if attribute.replace("android:", ns, 1) in el.attrib:
            el.attrib[attribute.replace("android:", ns, 1)] = attributes[attribute]
        else:
            el.attrib[attribute] = attributes[attribute]
    xml.write(file)


def android_add_to_application_manifest_attributes(build_params, attributes):
    add_attributes_to_xml(build_params,
                          file='AndroidManifest.xml',
                          attributes=attributes,
                          to="application")


def android_add_to_activity_manifest_attributes(build_params, attributes):
    add_attributes_to_xml(build_params,
                          file='AndroidManifest.xml',
                          attributes=attributes,
                          to="application/activity")


def android_add_url_handler(build_params, scheme, filename='AndroidManifest.xml'):
    if isinstance(scheme, str) or isinstance(scheme, unicode):
        scheme = pystache.render(scheme, build_params['app_config'])

    element = {
        "tag": "intent-filter",
        "children": [
            {
                "tag": "action",
                "attributes": {
                    "android:name": "android.intent.action.VIEW"
                }
            },
            {
                "tag": "category",
                "attributes": {
                    "android:name": "android.intent.category.DEFAULT"
                }
            },
            {
                "tag": "category",
                "attributes": {
                    "android:name": "android.intent.category.BROWSABLE"
                }
            },
            {
                "tag": "data",
                "attributes": {
                    "android:scheme": scheme
                }
            }
        ]
    }
    add_element_to_xml(build_params,
            file=filename,
            element=element,
            to="application/activity")


def android_add_url_handlers(build_params, schemes, filename='AndroidManifest.xml'):
    if isinstance(schemes, str) or isinstance(schemes, unicode):
        schemes = pystache.render(schemes, build_params['app_config'])
        schemes = ast.literal_eval(schemes) if len(schemes) else []

    for scheme in schemes:
        android_add_url_handler(build_params, scheme, filename)

# - we can no longer mutate AndroidManifest.xml from the client-side as Gradle build encodes it -------
