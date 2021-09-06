"Tasks that might be run on the customers's machine"

from time import gmtime
from calendar import timegm

# where the customer code exists inside the apps
locations_normal = {
    'android': 'development/android/assets/src',
    'android_bundle': 'development/android_bundle/base/assets/src',
    'ios': 'development/ios/*/assets/src',
    'ios-native': 'development/ios-native/ForgeInspector/assets/src',
    'osx': 'development/osx/Forge.app/Contents/Resources/assets/src',
    'web': 'development/web/src',
    'reload': 'development/reload/src',
}

locations_debug = {
    'ios': 'ios/app/ForgeInspector/assets/src',
    'ios-native': 'ios/native/ForgeInspector/assets/src',
    'android': 'android/ForgeInspector/assets/src',
    'osx': 'development/osx/Forge.app/Contents/Resources/assets/src',
    'web': 'development/web/src',
    'reload': 'development/reload/src',
}


def validate_user_source(src='src'):
    '''Check for any issues with the user source, i.e. no where to include all.js'''
    return [
        {'do': {'check_index_html': (src,)}}
    ]

def copy_user_source_to_tempdir(ignore_patterns=None, tempdir=None):
    return [
        {'do': {'copy_files': {'from': 'src', 'to': tempdir, 'ignore_patterns': ignore_patterns}}},
    ]

def delete_tempdir(tempdir=None):
    return [
        {'do': {'remove_files': tempdir}},
    ]

def run_hook(hook=None, dir=None):
    return [
        {'do': {'run_hook': {'hook': hook, 'dir': dir}}},
    ]

def copy_user_source_to_template(ignore_patterns=None, src='src', debug=False):
    if not debug:
        locations = locations_normal
    else:
        locations = locations_debug

    return [
        {'when': {'platform_is': 'android'}, 'do': {'copy_files': { 'from': src, 'to': locations["android"], 'ignore_patterns': ignore_patterns }}},
        {'when': {'platform_is': 'android'}, 'do': {'copy_files': { 'from': src, 'to': locations["android_bundle"], 'ignore_patterns': ignore_patterns }}},
        {'when': {'platform_is': 'ios'}, 'do': {'copy_files': { 'from': src, 'to': locations["ios"], 'ignore_patterns': ignore_patterns }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'copy_files': { 'from': src, 'to': locations["ios-native"], 'ignore_patterns': ignore_patterns }}},
        {'when': {'platform_is': 'osx'}, 'do': {'copy_files': { 'from': src, 'to': locations["osx"], 'ignore_patterns': ignore_patterns }}},
        {'when': {'platform_is': 'web'}, 'do': {'copy_files': { 'from': src, 'to': locations["web"], 'ignore_patterns': ignore_patterns }}},
        {'do': {'copy_files': { 'from': src, 'to': locations["reload"], 'ignore_patterns': ignore_patterns }}},
    ]

def include_platform_in_html(debug=False):
    if not debug:
        locations = locations_normal
    else:
        locations = locations_debug

    return [
        {'when': {'platform_is': 'android'}, 'do': {'find_and_replace_in_dir': {
            "root_dir": locations["android"],
            "find": "<head>",
            "replace": "<head><script src='%{back_to_parent}%forge/app_config.js'></script><script src='%{back_to_parent}%forge/all.js'></script>"
        }}},
        {'when': {'platform_is': 'android'}, 'do': {'find_and_replace_in_dir': {
            "root_dir": locations["android_bundle"],
            "find": "<head>",
            "replace": "<head><script src='%{back_to_parent}%forge/app_config.js'></script><script src='%{back_to_parent}%forge/all.js'></script>"
        }}},
        {'when': {'platform_is': 'ios'}, 'do': {'find_and_replace_in_dir': {
            "root_dir": locations["ios"],
            "find": "<head>",
            "replace": "<head><script src='%{back_to_parent}%forge/app_config.js'></script><script src='%{back_to_parent}%forge/all.js'></script>"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'find_and_replace_in_dir': {
            "root_dir": locations["ios-native"],
            "find": "<head>",
            "replace": "<head><script src='%{back_to_parent}%forge/app_config.js'></script><script src='%{back_to_parent}%forge/all.js'></script>"
        }}},
        {'when': {'platform_is': 'osx'}, 'do': {'find_and_replace_in_dir': {
            "root_dir": locations["osx"],
            "find": "<head>",
            "replace": "<head><script src='%{back_to_parent}%forge/app_config.js'></script><script src='%{back_to_parent}%forge/all.js'></script>"
        }}},
        {'when': {'platform_is': 'web'}, 'do': {'find_and_replace_in_dir': {
            "root_dir": locations["web"],
            "find": "<head>",
            "replace": "<head><script src='%{back_to_parent}%_forge/app_config.js'></script><script src='%{back_to_parent}%_forge/all.js'></script>"
        }}},
        {'do': {'find_and_replace_in_dir': {
            "root_dir": locations["reload"],
            "find": "<head>",
            "replace": "<head><script src='%{back_to_parent}%forge/app_config.js'></script><script src='%{back_to_parent}%forge/all.js'></script>"
        }}},
        {'do': {'find_and_replace_in_dir': {
            "root_dir": locations["reload"],
            "find": "<head>",
            "replace": """<head>
                            <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, minimum-scale=1.0, maximum-scale=1.0">
                            <script>
                            function window$forge$_receive(result) {
                                    try {
                                            window.forge._receive(JSON.parse(result));
                                    } catch (e) {
                                            forge.logging.error("window$forge$_receive -> " + e);
                                    }
                            }
                    </script>"""
        }}},
    ]

def include_name(build):
    json_safe_name = build.config["name"].replace('"', '\\"')
    xml_safe_name = build.config["name"].replace('"', '\\"').replace("'", "\\'")

    return [
        {'when': {'platform_is': 'ios'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios/*/Info.plist',
            "key": "CFBundleName",
            "value": "${name}"
        }}},
        {'when': {'platform_is': 'ios'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios/*/Info.plist',
            "key": "CFBundleDisplayName",
            "value": "${name}"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios-native/dist/*.app/Info.plist',
            "key": "CFBundleName",
            "value": "${name}"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios-native/dist/*.app/Info.plist',
            "key": "CFBundleDisplayName",
            "value": "${name}"
        }}},
        {'when': {'platform_is': 'osx'}, 'do': {'set_in_biplist': {
            "filename": 'development/osx/Forge.app/Contents/Info.plist',
            "key": "CFBundleName",
            "value": "${name}"
        }}},
        {'when': {'platform_is': 'osx'}, 'do': {'set_in_biplist': {
            "filename": 'development/osx/Forge.app/Contents/Info.plist',
            "key": "CFBundleDisplayName",
            "value": "${name}"
        }}},
    ]

def include_requirements():
    return [
        {'when': {'platform_is': 'ios', 'config_property_exists': 'core.ios.minimum_version'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios/*/Info.plist',
            "key": "MinimumOSVersion",
            "value": "${core.ios.minimum_version}"
        }}},
        {'when': {'platform_is': 'ios-native', 'config_property_exists': 'core.ios.minimum_version'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios-native/dist/*.app/Info.plist',
            "key": "MinimumOSVersion",
            "value": "${core.ios.minimum_version}"
        }}},
    ]

def include_uuid():
    return [
        {'do': {'populate_package_names': ()}},
        {'when': {'platform_is': 'ios'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios/*/Info.plist',
            "key": "CFBundleIdentifier", "value": "${core.ios.package_name}"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios-native/dist/*.app/Info.plist',
            "key": "CFBundleIdentifier", "value": "${core.ios.package_name}"
        }}},
        {'when': {'platform_is': 'osx'}, 'do': {'set_in_biplist': {
            "filename": 'development/osx/Forge.app/Contents/Info.plist',
            "key": "CFBundleIdentifier",
            "value": "${core.osx.package_name}"
        }}},
    ]

def include_author():
    return [
        {'when': {'platform_is': 'osx'}, 'do': {'set_in_biplist': {
            "filename": 'development/osx/Forge.app/Contents/Info.plist',
            "key": "NSHumanReadableCopyright",
            "value": "${author}"
        }}},
    ]

def include_description():
    return [
    ]

def include_version(build):
    build_number = str(int(timegm(gmtime())))
    target = iter(build.enabled_platforms).next()
    if "build_number" in build.config and target in build.config["build_number"]:
        build_number = str(build.config["build_number"][target])

    return [
        {'when': {'platform_is': 'ios'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios/*/Info.plist',
            "key": "CFBundleVersion", "value": build_number
        }}},
        {'when': {'platform_is': 'ios'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios/*/Info.plist',
            "key": "CFBundleShortVersionString", "value": "${version}"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios-native/dist/*.app/Info.plist',
            "key": "CFBundleVersion", "value": build_number
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'set_in_biplist': {
            "filename": 'development/ios-native/dist/*.app/Info.plist',
            "key": "CFBundleShortVersionString", "value": "${version}"
        }}},
        {'when': {'platform_is': 'osx'}, 'do': {'set_in_biplist': {
            "filename": 'development/osx/Forge.app/Contents/Info.plist',
            "key": "CFBundleVersion",
            "value": build_number
        }}},
        {'when': {'platform_is': 'osx'}, 'do': {'set_in_biplist': {
            "filename": 'development/osx/Forge.app/Contents/Info.plist',
            "key": "CFBundleShortVersionString",
            "value": "${version}"
        }}},
        {'do': {'set_in_config': {
            "key": "version_code",
            "value": build_number
        }}},
    ]

def include_reload():
    return [
        {'do': {'populate_trigger_domain': ()}},
        {'do': {'set_in_config': {
            "key": "trigger_domain",
            "value": "${trigger_domain}"
        }}},
        {'do': {'set_in_config': {
            "key": "config_hash",
            "value": "${config_hash}"
        }}},
        {'when': {'platform_is': 'android'}, 'do': {'generate_sha1_manifest': {
            "input_folder": "development/android/assets/src",
            "output_file": "development/android/assets/hash_to_file.json"
        }}},
        {'when': {'platform_is': 'android'}, 'do': {'generate_sha1_manifest': {
            "input_folder": "development/android_bundle/base/assets/src",
            "output_file": "development/android_bundle/base/assets/hash_to_file.json"
        }}},

        {'when': {'platform_is': 'ios'}, 'do': {'generate_sha1_manifest': {
            "input_folder": "development/ios/device-ios.app/assets/src",
            "output_file": "development/ios/device-ios.app/assets/hash_to_file.json"
        }}},
        {'when': {'platform_is': 'ios'}, 'do': {'generate_sha1_manifest': {
            "input_folder": "development/ios/simulator-ios.app/assets/src",
            "output_file": "development/ios/simulator-ios.app/assets/hash_to_file.json"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'generate_sha1_manifest': {
            "input_folder": "development/ios-native/dist/device-ios.app/assets/src",
            "output_file": "development/ios-native/dist/device-ios.app/assets/hash_to_file.json"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'generate_sha1_manifest': {
            "input_folder": "development/ios-native/dist/simulator-ios.app/assets/src",
            "output_file": "development/ios-native/dist/simulator-ios.app/assets/hash_to_file.json"
        }}},
        {'when': {'platform_is': 'osx'}, 'do': {'generate_sha1_manifest': {
            "input_folder": "development/osx/Forge.app/Contents/Resources/assets/src",
            "output_file": "development/osx/Forge.app/Contents/Resources/assets/hash_to_file.json"
        }}},
    ]

def include_config(debug=False):
    if debug:
        return [
            {'when': {'platform_is': 'android'}, 'do': {'write_config': {
                "filename": 'android/ForgeInspector/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'android'}, 'do': {'write_config': {
                "filename": 'android/ForgeInspector/assets/forge/app_config.js',
                "mapping_file": 'android/ForgeInspector/assets/module_mapping.json',
                "content": "window.forge = {}; window.forge.config = ${config}; window.forge.module_mapping = ${module_mapping}; window.forge.config.development = false;"
            }}},

            {'when': {'platform_is': 'ios'}, 'do': {'write_config': {
                "filename": 'ios/app/ForgeInspector/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'ios'}, 'do': {'write_config': {
                "filename": 'ios/app/ForgeInspector/assets/forge/app_config.js',
                "mapping_file": 'ios/app/ForgeInspector/assets/module_mapping.json',
                "content": "window.forge = {}; window.forge.config = ${config};"
            }}},
            {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
                "filename": 'ios/native/ForgeInspector/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
                "filename": 'ios/native/ForgeInspector/assets/forge/app_config.js',
                "mapping_file": 'ios/native/ForgeInspector/assets/module_mapping.json',
                "content": "window.forge = {}; window.forge.config = ${config};"
            }}},
        ]
    else:
        return [
            {'when': {'platform_is': 'android'}, 'do': {'write_config': {
                "filename": 'development/android/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'android'}, 'do': {'write_config': {
                "filename": 'development/android/assets/forge/app_config.js',
                "mapping_file": 'development/android/assets/module_mapping.json',
                "content": "window.forge = {}; window.forge.config = ${config}; window.forge.module_mapping = ${module_mapping}; window.forge.config.development = false;"
            }}},
            {'when': {'platform_is': 'android'}, 'do': {'write_config': {
                "filename": 'development/android_bundle/base/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'android'}, 'do': {'write_config': {
                "filename": 'development/android_bundle/base/assets/forge/app_config.js',
                "mapping_file": 'development/android/assets/module_mapping.json',
                "content": "window.forge = {}; window.forge.config = ${config}; window.forge.module_mapping = ${module_mapping}; window.forge.config.development = false;"
            }}},

            {'when': {'platform_is': 'ios'}, 'do': {'write_config': {
                "filename": 'development/ios/device-ios.app/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'ios'}, 'do': {'write_config': {
                "filename": 'development/ios/simulator-ios.app/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'ios'}, 'do': {'write_config': {
                "filename": 'development/ios/device-ios.app/assets/forge/app_config.js',
                "mapping_file": 'development/ios/device-ios.app/assets/module_mapping.json',
                "content": "window.forge = {}; window.forge.config = ${config}; window.forge.module_mapping = ${module_mapping}; window.forge.config.development = false;"
            }}},
            {'when': {'platform_is': 'ios'}, 'do': {'write_config': {
                "filename": 'development/ios/simulator-ios.app/assets/forge/app_config.js',
                "mapping_file": 'development/ios/simulator-ios.app/assets/module_mapping.json',
                "content": "window.forge = {}; window.forge.config = ${config}; window.forge.module_mapping = ${module_mapping}; window.forge.config.development = false;"
            }}},

            {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
                "filename": 'development/ios-native/ForgeInspector/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
                "filename": 'development/ios-native/ForgeInspector/assets/forge/app_config.js',
                "mapping_file": 'development/ios-native/ForgeInspector/assets/module_mapping.json',
                "content": "window.forge = {}; window.forge.config = ${config}; window.forge.module_mapping = ${module_mapping}; window.forge.config.development = false;"
            }}},

            {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
                "filename": 'development/ios-native/dist/device-ios.app/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
                "filename": 'development/ios-native/dist/simulator-ios.app/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
                "filename": 'development/ios-native/dist/device-ios.app/assets/forge/app_config.js',
                "mapping_file": 'development/ios-native/dist/device-ios.app/assets/module_mapping.json',
                "content": "window.forge = {}; window.forge.config = ${config}; window.forge.module_mapping = ${module_mapping}; window.forge.config.development = false;"
            }}},
            {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
                "filename": 'development/ios-native/dist/simulator-ios.app/assets/forge/app_config.js',
                "mapping_file": 'development/ios-native/dist/simulator-ios.app/assets/module_mapping.json',
                "content": "window.forge = {}; window.forge.config = ${config}; window.forge.module_mapping = ${module_mapping}; window.forge.config.development = false;"
            }}},

            {'when': {'platform_is': 'osx'}, 'do': {'write_config': {
                "filename": 'development/osx/Forge.app/Contents/Resources/assets/app_config.json',
                "content": "${config}"
            }}},
            {'when': {'platform_is': 'osx'}, 'do': {'write_config': {
                "filename": 'development/osx/Forge.app/Contents/Resources/assets/forge/app_config.js',
                "content": "window.forge = {}; window.forge.config = ${config};"
            }}},
            {'when': {'platform_is': 'web'}, 'do': {'write_config': {
                "filename": 'development/web/forge/app_config.js',
                "content": "window.forge = {}; window.forge.config = ${config};"
            }}},
        ]

def compile_ios_native_app():
    from os import path
    return [
        {'when': {'platform_is': 'ios-native'}, 'do': { 'xcode_build': (path.abspath(path.join('development', 'ios-native'))) }},
        {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
            "filename": 'development/ios-native/dist/device-ios.app/assets/app_config.json',
            "content": "${config}"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
            "filename": 'development/ios-native/dist/device-ios.app/assets/forge/app_config.js',
            "mapping_file": 'development/ios-native/dist/device-ios.app/assets/module_mapping.json',
            "content": "window.forge = {}; window.forge.config = ${config}; window.forge.module_mapping = ${module_mapping}; window.forge.config.development = false;"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
            "filename": 'development/ios-native/dist/simulator-ios.app/assets/app_config.json',
            "content": "${config}"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'write_config': {
            "filename": 'development/ios-native/dist/simulator-ios.app/assets/forge/app_config.js',
            "mapping_file": 'development/ios-native/dist/simulator-ios.app/assets/module_mapping.json',
            "content": "window.forge = {}; window.forge.config = ${config}; window.forge.module_mapping = ${module_mapping}; window.forge.config.development = false;"
        }}},
    ]

def run_module_build_steps(build):
    return [
        {'when': {'platform_is': 'android'}, 'do': {
            'run_module_build_steps': {
                'steps_path': 'development/android/build_steps',
                'src_path': 'development/android/assets/src',
                'project_path': 'development/android'
            }
        }},

        {'when': {'platform_is': 'android'}, 'do': {
            'run_module_build_steps': {
                'steps_path': 'development/android/build_steps',
                'src_path': 'development/android_bundle/base/assets/src',
                'project_path': 'development/android_bundle/base'
            }
        }},

        {'when': {'platform_is': 'ios'}, 'do': {
            'run_module_build_steps': {
                'steps_path': 'development/ios/build_steps',
                'src_path': 'development/ios/device-ios.app/assets/src',
                'project_path': 'development/ios/device-ios.app'
            }
        }},
        {'when': {'platform_is': 'ios'}, 'do': {
            'run_module_build_steps': {
                'steps_path': 'development/ios/build_steps',
                'src_path': 'development/ios/simulator-ios.app/assets/src',
                'project_path': 'development/ios/simulator-ios.app'
            }
        }},
        {'when': {'platform_is': 'ios-native'}, 'do': {
            'run_module_build_steps': {
                'steps_path': 'development/ios-native/dist/build_steps',
                'src_path': 'development/ios-native/dist/device-ios.app/assets/src',
                'project_path': 'development/ios-native/dist/device-ios.app'
            }
        }},
        {'when': {'platform_is': 'ios-native'}, 'do': {
            'run_module_build_steps': {
                'steps_path': 'development/ios-native/dist/build_steps',
                'src_path': 'development/ios-native/dist/simulator-ios.app/assets/src',
                'project_path': 'development/ios-native/dist/simulator-ios.app'
            }
        }},
        {'when': {'platform_is': 'osx'}, 'do': {
            'run_module_build_steps': {
                'steps_path': 'development/osx/build_steps',
                'src_path': 'development/osx/Forge.app/Contents/Resources/assets/src',
                'project_path': 'development/osx/Forge.app'
            }
        }}
        # Delete build steps folder?
    ]

def resolve_urls():
    return [
        {'do': {'resolve_urls': (
            'modules.activations.config.activations.[].scripts.[]',
            'modules.activations.config.activations.[].styles.[]',
            'modules.launchimage.config.android',
            'modules.launchimage.config.android-landscape',
            'modules.button.config.default_icon',
            'modules.button.config.default_popup',
            'modules.button.config.default_icons.*'
        )}},
    ]

def run_android_phase(build_type_dir, sdk, device, interactive, purge=False):
    return [
        {'when': {'platform_is': 'android'}, 'do': {'run_android': (build_type_dir, sdk, device, interactive, purge)}},
    ]

def run_ios_phase(device):
    return [
        {'when': {'platform_is': 'ios'}, 'do': {'run_ios': (device,)}},
    ]

def run_ios_native_phase(device):
    return [
        {'when': {'platform_is': 'ios-native'}, 'do': {'run_ios': (device,)}},
    ]

def run_osx_phase():
    return [
        {'when': {'platform_is': 'osx'}, 'do': {'run_osx': ()}},
    ]


def run_web_phase():
    return [
        {'when': {'platform_is': 'web'}, 'do': {'run_web': ()}},
    ]

def package(build_type_dir):
    return [
        {'when': {'platform_is': 'android'}, 'do': {'package_android': ()}},
        {'when': {'platform_is': 'android'}, 'do': {'bundle_android': ()}},
        {'when': {'platform_is': 'ios'}, 'do': {'package_ios': ()}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'package_ios_native': ()}},
        {'when': {'platform_is': 'osx'}, 'do': {'package_osx': ()}},
        {'when': {'platform_is': 'web'}, 'do': {'package_web': ()}},
    ]

def serve(build_type_dir):
    return [
        {'when': {'platform_is': 'android'}, 'do': {'serve_android': ()}},
        {'when': {'platform_is': 'ios'}, 'do': {'serve_ios': ()}},
        {'when': {'platform_is': 'osx'}, 'do': {'serve_osx': ()}},
        {'when': {'platform_is': 'web'}, 'do': {'serve_web': ()}},
    ]

def make_installers():
    return [
    ]

def check_javascript():
    return [
            {'do': {'lint_javascript': ()}},
    ]

def check_local_config_schema():
    return [
            {'do': {'check_local_config_schema': ()}},
    ]

def clean_phase():
    return [
        {'when': {'platform_is': 'android'}, 'do': {'clean_android': ()}},
        {'when': {'platform_is': 'web'}, 'do': {'clean_web': ()}},
    ]


def inject_local_assets():
    """only ever run from forge-generate"""
    return [
        {'when': {'platform_is': 'ios'}, 'do': {'inject_local_assets': ()}},
        {'when': {'platform_is': 'android'}, 'do': {'inject_local_assets': ()}},
    ]


def set_is_development(is_development = False):
    to_str = lambda b: "true" if b else "false"
    return [
        {'when': {'platform_is': 'ios'}, 'do': {'find_and_replace': {
            "in": ("development/ios/*/assets/forge/app_config.js",),
            "find": "window.forge.config.development = %s;" % to_str(not is_development),
            "replace": "window.forge.config.development = %s;" % to_str(is_development)
        }}},
        {'when': {'platform_is': 'android'}, 'do': {'find_and_replace': {
            "in": ("development/android/assets/forge/app_config.js",),
            "find": "window.forge.config.development = %s;" % to_str(not is_development),
            "replace": "window.forge.config.development = %s;" % to_str(is_development)
        }}},
    ]
