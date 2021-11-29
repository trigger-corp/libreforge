from lib import predicate

@predicate
def icon_available(build, platform, size):
        return "modules" in build.config and \
                "icons" in build.config["modules"] and \
                "config" in build.config["modules"]["icons"] and \
                (size in build.config["modules"]["icons"]["config"] or \
                size in build.config["modules"]["icons"]["config"].get(platform, {}))
