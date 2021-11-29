from lib import predicate

@predicate
def is_external(build):
    return bool(build.external)

@predicate
def do_package(build):
    return getattr(build, "package", False)

@predicate
def config_property_exists(build, property):
    properties = property.split('.')
    at = build.config
    for x in properties:
        if x in at:
            at = at[x]
        else:
            return False
    return True

@predicate
def not_config_property_exists(build, property):
    return not config_property_exists(build, property)

@predicate
def config_property_equals(build, property, value):
    properties = property.split('.')
    at = build.config
    for x in properties:
        if x in at:
            at = at[x]
        else:
            return False
    return at == value

@predicate
def platform_is(build, platform):
    return platform == 'all' or (set(platform.split(',')) & set(build.enabled_platforms))

@predicate
def is_inspector(build, polarity=True):
    target = iter(build.enabled_platforms).next()
    is_inspector = target.endswith("-inspector")
    return is_inspector == polarity
