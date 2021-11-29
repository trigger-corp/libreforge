from os import path
from time import gmtime
from calendar import timegm

def prepare_config():
    return [
        {'do': {'preprocess_config': ()}},
        {'do': {'populate_package_names': ()}},
    ]

def copy_platform_source():
    return [
        {'do': {'addon_source': 'common-v2'}},
        {'do': {'addon_source': 'module/schema'}},

        {'when': {'platform_is': 'ios'}, 'do': {'addon_source': 'ios/ForgeCore'}},
        {'when': {'platform_is': 'ios'}, 'do': {'addon_source': 'ios/app'}},
        {'when': {'platform_is': 'ios'}, 'do': {'addon_source': 'ios/js'}},

        {'when': {'platform_is': 'ios-native'}, 'do': {'addon_source': 'ios/ForgeCore'}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'addon_source': 'ios/native'}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'addon_source': 'ios/js'}},

        {'when': {'platform_is': 'ios-inspector'}, 'do': {'addon_source': 'ios/ForgeCore'}},
        {'when': {'platform_is': 'ios-inspector'}, 'do': {'addon_source': 'ios/inspector'}},
        {'when': {'platform_is': 'ios-inspector'}, 'do': {'addon_source': 'ios/js'}},
        {'when': {'platform_is': 'ios-inspector'}, 'do': {'addon_source': 'test-apps/inspector'}},

        {'when': {'platform_is': 'osx'}, 'do': {'addon_source': 'osx/ForgeCore'}},
        {'when': {'platform_is': 'osx'}, 'do': {'addon_source': 'osx/app'}},
        {'when': {'platform_is': 'osx'}, 'do': {'addon_source': 'osx/js'}},

        {'when': {'platform_is': 'osx-inspector'}, 'do': {'addon_source': 'osx/ForgeCore'}},
        {'when': {'platform_is': 'osx-inspector'}, 'do': {'addon_source': 'osx/ForgeInspector'}},
        {'when': {'platform_is': 'osx-inspector'}, 'do': {'addon_source': 'osx/js'}},
        {'when': {'platform_is': 'osx-inspector'}, 'do': {'addon_source': 'test-apps/inspector'}},

        {'when': {'platform_is': 'android'}, 'do': {'addon_source': 'android/ForgeInspector'}},
        {'when': {'platform_is': 'android'}, 'do': {'addon_source': 'android/ForgeCore'}},
        {'when': {'platform_is': 'android'}, 'do': {'addon_source': 'android/js'}},
        {'when': {'platform_is': 'android'}, 'do': {'addon_source': 'android/build.gradle'}},
        {'when': {'platform_is': 'android'}, 'do': {'addon_source': 'android/settings.gradle'}},
        {'when': {'platform_is': 'android'}, 'do': {'addon_source': 'android/gradle.properties'}},

        {'when': {'platform_is': 'an-inspector'}, 'do': {'addon_source': 'android/ForgeCore'}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'addon_source': 'android/ForgeInspector'}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'addon_source': 'android/ForgeModule'}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'addon_source': 'android/js'}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'addon_source': 'android/build.gradle'}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'addon_source': 'android/settings.gradle'}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'addon_source': 'android/gradle.properties'}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'addon_source': 'android/an-inspector-settings.gradle'}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'addon_source': 'test-apps/inspector'}},

        {'when': {'platform_is': 'web'}, 'do': {'addon_source': 'web'}},
    ]

def provision_platform_assets():
    return [
        {'when': {'platform_is': 'ios'}, 'do': {'provision_assets': 'assets'}},
        {'when': {'platform_is': 'android'}, 'do': {'provision_assets': 'assets'}},
    ]


def override_modules():
    return [
        {'do': {'prepare_module_override': ()}},
    ]

def copy_customer_source():
    return [
        {'do': {'user_source': 'src'}},
    ]

def copy_common_files():
    return [
        {'when': {'platform_is': 'android'}, 'do': {'copy_files': {
            'from': 'common-v2/forge', 'to': 'android/ForgeInspector/assets/forge'
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'copy_files': {
            'from': 'common-v2/forge', 'to': 'android/ForgeInspector/assets/forge'
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'copy_files': {
            'from': 'test-apps/inspector', 'to': 'android/ForgeInspector/assets/src'
        }}},
        {'when': {'platform_is': 'ios'}, 'do': {'copy_files': {
            'from': 'common-v2/forge', 'to': 'ios/app/ForgeInspector/assets/forge'
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'copy_files': {
            'from': 'common-v2/forge', 'to': 'ios/native/ForgeInspector/assets/forge'
        }}},
        {'when': {'platform_is': 'osx'}, 'do': {'copy_files': {
            'from': 'common-v2/forge', 'to': 'osx/app/ForgeInspector/assets/forge'
        }}},
        {'when': {'platform_is': 'ios-inspector'}, 'do': {'copy_files': {
            'from': 'common-v2/forge', 'to': 'ios/inspector/ForgeInspector/assets/forge'
        }}},
        {'when': {'platform_is': 'ios-inspector'}, 'do': {'copy_files': {
            'from': 'test-apps/inspector', 'to': 'ios/inspector/ForgeInspector/assets/src'
        }}},
        {'when': {'platform_is': 'osx-inspector'}, 'do': {'copy_files': {
            'from': 'common-v2/forge', 'to': 'osx/ForgeInspector/ForgeInspector/assets/forge'
        }}},
        {'when': {'platform_is': 'osx-inspector'}, 'do': {'copy_files': {
            'from': 'test-apps/inspector', 'to': 'osx/ForgeInspector/ForgeInspector/assets/src'
        }}},
        {'when': {'platform_is': 'web'}, 'do': {'copy_files': {
            'from': 'common-v2/forge', 'to': 'web/forge'
        }}},
    ]


def pre_create_all_js():
    current_jQuery = 'common-v2/jquery-1.5.2.js'
    return [
        {'when': {'platform_is': 'web'}, 'do': {'add_to_all_js': current_jQuery}},
        {'do': {'add_to_all_js': 'common-v2/api-prefix.js'}},
        {'do': {'add_to_all_js': 'common-v2/config.js'}},
        {'when': {'platform_is': 'web'}, 'do': {'add_to_all_js': 'common-v2/api-jquery.js'}},
        {'do': {'add_to_all_js': 'common-v2/polyfills/misc.js'}},
        {'do': {'add_to_all_js': 'common-v2/polyfills/promise.js'}},
        {'do': {'add_to_all_js': 'common-v2/api.js'}},
    ]

def post_create_all_js():
    return [
        {'do': {'add_to_all_js': 'common-v2/modules/is/common.js'}},
        {'when': {'platform_is': 'android,an-inspector'}, 'do': {'add_to_all_js': 'common-v2/modules/is/android.js'}},
        {'when': {'platform_is': 'ios,ios-native,ios-inspector'}, 'do': {'add_to_all_js': 'common-v2/modules/is/ios.js'}},
        {'when': {'platform_is': 'osx,osx-inspector'}, 'do': {'add_to_all_js': 'common-v2/modules/is/osx.js'}},
        {'do': {'add_to_all_js': 'common-v2/modules/logging/default.js'}},
        {'do': {'add_to_all_js': 'common-v2/modules/httpd/default.js'}},
        {'do': {'add_to_all_js': 'common-v2/modules/internal/default.js'}},
        {'when': {'platform_is': 'android,an-inspector,ios,ios-native,ios-inspector'}, 'do': {'add_to_all_js': 'common-v2/modules/event/mobile.js'}},
        {'do': {'add_to_all_js': 'common-v2/modules/event/common.js'}},
        {'do': {'add_to_all_js': 'common-v2/modules/layout/default.js'}},
        {'do': {'add_to_all_js': 'common-v2/reload.js'}},
        {'do': {'add_to_all_js': 'common-v2/live.js'}},
        {'do': {'add_to_all_js': 'common-v2/tools.js'}},
        {'when': {'platform_is': 'ios'}, 'do': {'add_to_all_js': 'ios/js/api-ios.js'}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'add_to_all_js': 'ios/js/api-ios.js'}},
        {'when': {'platform_is': 'ios-inspector'}, 'do': {'add_to_all_js': 'ios/js/api-ios.js'}},
        {'when': {'platform_is': 'osx'}, 'do': {'add_to_all_js': 'osx/js/api-osx.js'}},
        {'when': {'platform_is': 'osx-inspector'}, 'do': {'add_to_all_js': 'osx/js/api-osx.js'}},
        {'when': {'platform_is': 'android'}, 'do': {'add_to_all_js': 'android/js/api-android.js'}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'add_to_all_js': 'android/js/api-android.js'}},
        {'when': {'platform_is': 'web'}, 'do': {'add_to_all_js': 'web/assets_forge/api-web.js'}},
        {'do': {'add_to_all_js': 'common-v2/api-expose.js'}},
        {'do': {'add_to_all_js': 'common-v2/api-suffix.js'}},
    ]

def remove_assets_forge():
    return [
        {'when': {'platform_is': 'web'}, 'do': {'remove_files': 'web/assets_forge'}},
    ]

def platform_specific_templating(build):
    'Perform any platform specific templating'

    json_safe_name = build.config["name"].replace('"', '\\"')
    xml_safe_name = build.config["name"].replace('"', '\\"').replace("'", "\\'")

    build_number = str(int(timegm(gmtime())))
    target = iter(build.enabled_platforms).next()
    if "build_number" in build.config and target in build.config["build_number"]:
        build_number = str(build.config["build_number"][target])

    return [
        {'when': {'platform_is': 'an-inspector'}, 'do': {'write_config': {
            "filename": 'android/ForgeInspector/assets/app_config.json',
            "content": '{"modules": {"inspector": {"version": "1.0"}}}'
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'write_config': {
            "filename": 'android/ForgeInspector/assets/forge/app_config.js',
            "content": 'window.forge = {}; window.forge.config = {"inspector": {"version": "1.0"}}};'
        }}},

        # Log output on iOS
        # TODO: Been broken for some time
        # {'when': {'platform_is': 'ios'}, 'do': {'find_and_replace': {
        #       "in": ('ios/ForgeCore/ForgeCore/utils/ForgeLog.m',),
        #       "find": "kForgeLogLevel = @\"DEBUG\";", "replace": "kForgeLogLevel = @\"${logging_level}\";"
        # }}},

        {'when': {'platform_is': 'android', 'config_property_exists': 'core.android.minimum_version'}, 'do': {'android_set_min_sdk_version': {
            "gradle_json": 'android/ForgeInspector/gradle.json',
            "value": "${core.android.minimum_version}"
        }}},
        {'when': {'platform_is': 'android', 'config_property_exists': 'core.general.localisations'}, 'do': {'android_set_gradle_json': {
            "gradle_json": 'android/ForgeInspector/gradle.json',
            "key": "resConfigs",
            "value": "[{% for l in core['general']['localisations'] %}'${l}', {% end %}]"
        }}},
        {'when': {'platform_is': 'android'}, 'do': {'set_attribute_value_xml': {
            "file": 'android/ForgeInspector/AndroidManifest.xml',
            "element": "application",
            "attribute": "android:label",
            "value": xml_safe_name
        }}},
        {'when': {'platform_is': 'android'}, 'do': {'set_attribute_value_xml': {
            "file": 'android/ForgeInspector/AndroidManifest.xml',
            "attribute": "android:versionCode",
            "value": build_number
        }}},
        {'when': {'platform_is': 'android'}, 'do': {'set_attribute_value_xml': {
            "file": 'android/ForgeInspector/AndroidManifest.xml',
            "attribute": "android:versionName",
            "value": "${version}"
        }}},
        {'when': {'platform_is': 'android'}, 'do': {'find_and_replace': {
            "in": ('android/ForgeInspector/AndroidManifest.xml',),
            "find": "io.trigger.forge.android.inspector", "replace": "${core.android.package_name}"
        }}},
        {'when': {
            'platform_is': 'android',
            'config_property_exists': 'flags.android_uses_cleartext_traffic'
        },
        'do': {'set_attribute_value_xml': {
            "file": 'android/ForgeInspector/AndroidManifest.xml',
            "element": "application",
            "attribute": "android:usesCleartextTraffic",
            "value": "${flags.android_uses_cleartext_traffic}"
        }}},


        # add app's package namespace to proguard file because gradle now relocates module resources there
        {'when': {'platform_is': 'android'}, 'do': {'find_and_replace': {
            "in": ('android/ForgeInspector/proguard-project.txt',),
            "find": 'io.trigger.forge.android.inspector',
            "replace": '${core.android.package_name}'
        }}},

        # Workaround for https://crosswalk-project.org/jira/browse/XWALK-3547
        #                https://github.com/AppGyver/steroids/issues/495
        #                https://github.com/shprink/ionic-native-transitions/issues/55
        #                https://github.com/driftyco/ionic-plugin-keyboard/issues/96
        {'when': {'platform_is': 'android', 'config_property_exists': 'core.android.windowSoftInputMode'}, 'do': {'set_attribute_value_xml': {
            "file": 'android/ForgeInspector/AndroidManifest.xml',
            "element": "application/activity",
            "attribute": "android:windowSoftInputMode",
            "value": "${core.android.windowSoftInputMode}"
        }}},

        {'when': {'platform_is': 'ios', 'config_property_equals': ('core.ios.device_family', 'iphone')}, 'do': {'find_and_replace': {
            "in": ('ios/app/ForgeInspector.xcodeproj/project.pbxproj',),
            "find": 'TARGETED_DEVICE_FAMILY = "1,2";',
            "replace": 'TARGETED_DEVICE_FAMILY = "1";'
        }}},
        {'when': {'platform_is': 'ios', 'config_property_equals': ('core.ios.device_family', 'ipad')}, 'do': {'find_and_replace': {
            "in": ('ios/app/ForgeInspector.xcodeproj/project.pbxproj',),
            "find": 'TARGETED_DEVICE_FAMILY = "1,2";',
            "replace": 'TARGETED_DEVICE_FAMILY = "2";'
        }}},

        {'when': {'platform_is': 'ios-native', 'config_property_equals': ('core.ios.device_family', 'iphone')}, 'do': {'find_and_replace': {
            "in": ('ios/native/ForgeInspector.xcodeproj/project.pbxproj',),
            "find": 'TARGETED_DEVICE_FAMILY = "1,2";',
            "replace": 'TARGETED_DEVICE_FAMILY = "1";'
        }}},
        {'when': {'platform_is': 'ios-native', 'config_property_equals': ('core.ios.device_family', 'ipad')}, 'do': {'find_and_replace': {
            "in": ('ios/native/ForgeInspector.xcodeproj/project.pbxproj',),
            "find": 'TARGETED_DEVICE_FAMILY = "1,2";',
            "replace": 'TARGETED_DEVICE_FAMILY = "2";'
        }}},

        {'when': {'platform_is': 'ios-inspector'}, 'do': {'write_config': {
            "filename": 'ios/inspector/ForgeInspector/assets/app_config.json',
            "content": '{"modules": {"inspector": {"version": "1.0"}}}'
        }}},
        {'when': {'platform_is': 'ios-inspector'}, 'do': {'write_config': {
            "filename": 'ios/inspector/ForgeInspector/assets/forge/app_config.js',
            "content": 'window.forge = {}; window.forge.config = {"modules": {"inspector": {"version": "1.0"}}};'
        }}},

        {'when': {'platform_is': 'osx-inspector'}, 'do': {'write_config': {
            "filename": 'osx/ForgeInspector/ForgeInspector/assets/app_config.json',
            "content": '{"modules": {"alert": {"version": "1.0"}, "inspector": {"version": "1.0"}}}'
        }}},
        {'when': {'platform_is': 'osx-inspector'}, 'do': {'write_config': {
            "filename": 'osx/ForgeInspector/ForgeInspector/assets/forge/app_config.js',
            "content": 'window.forge = {}; window.forge.config = {"modules": {"alert": {"version": "1.0"}, "inspector": {"version": "1.0"}}};'
        }}},
    ]

def minification():
    return [
        {'when': {'platform_is': 'android', 'is_external': ()}, 'do': {'minify_in_place': 'android/ForgeInspector/assets/forge/all.js'}},
        {'when': {'platform_is': 'an-inspector', 'is_external': ()}, 'do': {'minify_in_place': 'android/ForgeInspector/assets/forge/all.js'}},

        {'when': {'platform_is': 'ios', 'is_external': ()}, 'do': {'minify_in_place': 'ios/app/ForgeInspector/assets/forge/all.js'}},
        {'when': {'platform_is': 'ios-native', 'is_external': ()}, 'do': {'minify_in_place': 'ios/native/ForgeInspector/assets/forge/all.js'}},
        {'when': {'platform_is': 'ios-inspector', 'is_external': ()}, 'do': {'minify_in_place': 'ios/inspector/ForgeInspector/assets/forge/all.js'}},

        {'when': {'platform_is': 'osx', 'is_external': ()}, 'do': {'minify_in_place': 'osx/app/ForgeInspector/assets/forge/all.js'}},
        {'when': {'platform_is': 'osx-inspector', 'is_external': ()}, 'do': {'minify_in_place': 'osx/ForgeInspector/ForgeInspector/assets/forge/all.js'}},

        {'when': {'platform_is': 'web', 'is_external': ()}, 'do': {'minify_in_place': 'web/forge/all.js'}},
    ]


def add_modules():
    'Run any platform specific steps required to include native modules'
    return [
        {'when': {'platform_is': 'android'}, 'do': {'download_and_extract_modules': ()}},
        {'when': {'platform_is': 'ios'}, 'do': {'download_and_extract_modules': ()}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'download_and_extract_modules': ()}},
        {'when': {'platform_is': 'osx'}, 'do': {'download_and_extract_modules': ()}},
        {'do': {'create_module_mapping': ()}},
        {'when': {'platform_is': 'android'}, 'do': {'add_modules_android': ()}},
        {'when': {'platform_is': 'ios'}, 'do': {'add_modules_ios': ()}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'add_modules_ios_native': ()}},
        {'when': {'platform_is': 'osx'}, 'do': {'add_modules_osx': ()}},
        {'do': {'add_to_all_js': 'common-v2/api-flags.js'}},
    ]

def platform_specific_build():
    'Run any platform specific build steps (Gradle for Android, xcode for iOS)'
    return [
        # clean out adaptive icons if not requested
        {'when': {'platform_is': 'android',
                  'config_property_exists': 'modules.icons.config',
                  'not_config_property_exists': 'modules.icons.config.android.adaptive.background-color'
                  }, 'do': {'remove_files': (
                      'android/ForgeInspector/res/mipmap-anydpi-v26/ic_launcher.xml',
                      'android/ForgeInspector/res/mipmap-anydpi-v26/ic_launcher_round.xml',
                      'android/ForgeInspector/res/mipmap-hdpi-v4/ic_launcher_foreground.png',
                      'android/ForgeInspector/res/mipmap-mdpi-v4/ic_launcher_foreground.png',
                      'android/ForgeInspector/res/mipmap-xhdpi-v4/ic_launcher_foreground.png',
                      'android/ForgeInspector/res/mipmap-xxhdpi-v4/ic_launcher_foreground.png',
                      'android/ForgeInspector/res/mipmap-xxxhdpi-v4/ic_launcher_foreground.png',
                      'android/ForgeInspector/res/values/ic_launcher_background.xml',
                  )}},

        {'when': {'platform_is': 'android'}, 'do': {'gradle_build': ('android', 'assembleVanillaAPK')}},
        {'when': {'platform_is': 'android'}, 'do': {'gradle_build': ('android', 'assembleVanillaAAB')}},
        {'when': {'platform_is': 'android'}, 'do': {'android_copy_native_libs': 'android/ForgeInspector'}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'gradle_build': ('android', 'ForgeCore:assembleDebug')}},

        {'when': {'platform_is': 'ios'}, 'do': {'xcode_build': 'ios/app'}},

        {'when': {'platform_is': 'ios-native'}, 'do': {'xcode_core_build': 'ios/ForgeCore'}},

        {'when': {'platform_is': 'osx'}, 'do': {'xcode_osx_build': 'osx/app'}},

        {'when': {'platform_is': 'ios-inspector'}, 'do': {'xcode_core_build': 'ios/ForgeCore'}},

        {'when': {'platform_is': 'osx-inspector'}, 'do': {'xcode_osx_core_build': 'osx/ForgeCore'}},
    ]

def handle_template_output():
    return [
        {'do': {'remove_files': 'common-v2'}},

        {'when': {'platform_is': 'android'}, 'do': {'rename_files': {
            "from": "android/ForgeInspector/apk",
            "to": "development/android"
        }}},
        {'when': {'platform_is': 'android'}, 'do': {'rename_files': {
            "from": "android/ForgeInspector/aab",
            "to": "development/android_bundle"
        }}},
        {'when': {'platform_is': 'android'}, 'do': {'rename_files': {
            "from": "android/ForgeInspector/build_steps",
            "to": "development/android"
        }}},

        {'when': {'platform_is': 'an-inspector'}, 'do': {'make_dir': {
            "dir": "android/ForgeInspector/libs"
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'rename_files': {
            "from": "android/ForgeCore/libs",
            "to": "android/ForgeModule/libs"
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'rename_files': {
            # Backwards compatibility for customers who still need to use Eclipse for building modules
            "from": "android/ForgeCore/build/intermediates/bundles/vanilla/debug/classes.jar",
            "to": "android/ForgeModule/libs/forgecore.jar"
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'rename_files': {
            "from": "android/ForgeCore/build/outputs/aar/ForgeCore-vanilla-debug.aar",
            "to": "android/ForgeModule/libs/ForgeCore-vanilla-debug.aar"
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'rename_files': {
            "from": "android/ForgeModule",
            "to": "development/an-inspector/ForgeModule"
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'rename_files': {
            "from": "android/build.gradle",
            "to": "development/an-inspector/build.gradle"
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'rename_files': {
            "from": "android/an-inspector-settings.gradle",
            "to": "development/an-inspector/settings.gradle"
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'rename_files': {
            "from": "android/gradle.properties",
            "to": "development/an-inspector/gradle.properties"
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'rename_files': {
            "from": "android/ForgeInspector/an-inspector.gradle",
            "to": "android/ForgeInspector/build.gradle"
        }}},
        {'when': {'platform_is': 'an-inspector'}, 'do': {'rename_files': {
            "from": "android/ForgeInspector",
            "to": "development/an-inspector/ForgeInspector"
        }}},

        {'when': {'platform_is': 'ios'}, 'do': {'rename_files': {
            "from": "ios/app/dist",
            "to": "development/ios"
        }}},
        {'when': {'platform_is': 'osx'}, 'do': {'rename_files': {
            "from": "osx/app/dist",
            "to": "development/osx"
        }}},

        {'when': {'platform_is': 'ios-native'}, 'do': {'remove_files': (
            'ios/ForgeCore/dist/ForgeCore.framework/Versions',
        )}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'rename_files': {
            "from": "ios/ForgeCore/dist/ForgeCore.bundle",
            "to": "ios/native/ForgeCore.bundle"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'rename_files': {
            "from": "ios/ForgeCore/dist/ForgeCore.framework",
            "to": "ios/native/ForgeCore.framework"
        }}},
        {'when': {'platform_is': 'ios-native'}, 'do': {'rename_files': {
            "from": "ios/native",
            "to": "development/ios-native"
        }}},

        {'when': {'platform_is': 'ios-inspector'}, 'do': {'remove_files': (
            'ios/ForgeCore/dist/ForgeCore.framework/Versions',
        )}},
        {'when': {'platform_is': 'ios-inspector'}, 'do': {'rename_files': {
            "from": "ios/ForgeCore/dist/ForgeCore.bundle",
            "to": "ios/inspector/ForgeCore.bundle"
        }}},
        {'when': {'platform_is': 'ios-inspector'}, 'do': {'rename_files': {
            "from": "ios/ForgeCore/dist/ForgeCore.framework",
            "to": "ios/inspector/ForgeCore.framework"
        }}},
        {'when': {'platform_is': 'ios-inspector'}, 'do': {'rename_files': {
            "from": "ios/inspector",
            "to": "development/ios-inspector"
        }}},
        {'when': {'platform_is': 'osx-inspector'}, 'do': {'rename_files': {
            "from": "osx/ForgeCore/dist/ForgeCore.framework",
            "to": "osx/ForgeInspector/ForgeCore.framework"
        }}},
        {'when': {'platform_is': 'osx-inspector'}, 'do': {'rename_files': {
            "from": "osx/ForgeInspector",
            "to": "development/osx-inspector"
        }}},
        {'when': {'platform_is': 'web'}, 'do': {'rename_files': {
            "from": "web",
            "to": "development/web"
        }}},
    ]

def copy_lib_files_to_template(source_dir):
    return [
        {'do': {'copy_files': {
            'from': path.join(source_dir, 'generate', 'lib'),
            'to': path.join('.template', 'lib')
        }}},
    ]

def handle_output():
    return [
        {'do': {'move_output': 'development'}},
        {'when': {'do_package': ()}, 'do': {'move_output': 'release'}},
        {'do': {'remember_build_output_location': ()}},
    ]

def handle_debug_output():
    return [
        {'when': {'platform_is': 'android'}, 'do': {'move_debug_output': 'android'}},
        {'when': {'platform_is': 'ios'}, 'do': {'move_debug_output': 'ios'}},
    ]
