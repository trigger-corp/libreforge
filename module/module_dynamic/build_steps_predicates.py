import pystache

def config_property_is_true(build_params, config_property):
        if isinstance(config_property, str) or isinstance(config_property, unicode):
                config_property = pystache.render(config_property, build_params['app_config'])

        return config_property == "True"


def is_inspector(build_params, polarity=True):
    is_inspector = "inspector" in build_params.get("app_config", {}).get("modules", {})
    return is_inspector == polarity
