# Phases for legacy (module rather than plugin) build process which is still used for:
# web

from os import path

_icon_path_for_customer = {
}

locations = {
}

def create_all_js():
    return [
        {'do': {'add_to_all_js': 'common-v2/legacy/button.js'}},
        {'do': {'add_to_all_js': 'common-v2/legacy/document.js'}},
        {'do': {'add_to_all_js': 'common-v2/legacy/prefs.js'}},
        {'do': {'add_to_all_js': 'common-v2/legacy/tabs.js'}},
        {'do': {'add_to_all_js': 'common-v2/legacy/message.js'}},
        {'do': {'add_to_all_js': 'common-v2/legacy/notification.js'}},
        {'do': {'add_to_all_js': 'common-v2/legacy/file.js'}},
        {'do': {'add_to_all_js': 'common-v2/legacy/request.js'}},
        {'do': {'add_to_all_js': 'common-v2/legacy/geolocation.js'}},
    ]

def platform_specific_templating(build):
    return [
    ]

def customer_phase():
    icon_path = _icon_path_for_customer
    def icon(platform, sub_path):
        return path.join(icon_path[platform], sub_path)

    return [
    ]
