#!/usr/bin/env python

from validator import SchemaValidator, ValidationError, SchemaError

__all__ = ['validate', 'SchemaValidator', 'ValidationError', 'SchemaError']
__version__ = '0.8.0'


def validate(data, schema, validator_cls=SchemaValidator, default_location="_data",
             format_validators=None, required_by_default=True, blank_by_default=False):
    '''
    Validates a parsed json document against the provided schema. If an
    error is found a :class:`ValidationError` is raised.

    If there is an issue in the schema a :class:`SchemaError` will be raised.

    :param data:  python data to validate
    :param schema: python dictionary representing the schema (see
        `schema format`_)
    :param validator_cls: optional validator class (default is
        :class:`SchemaValidator`)
    :param format_validators: optional dictionary of custom format validators
    :param required_by_default: defaults to True, set to False to make
        ``required`` schema attribute False by default.
    '''
    v = validator_cls(format_validators, required_by_default, blank_by_default)
    return v.validate(data, schema, default_location)

if __name__ == '__main__':
    import sys
    import json
    if len(sys.argv) == 2:
        if sys.argv[1] == "--help":
            raise SystemExit("%s SCHEMAFILE [INFILE]" % (sys.argv[0],))
        schemafile = open(sys.argv[1], 'rb')
        infile = sys.stdin
    elif len(sys.argv) == 3:
        schemafile = open(sys.argv[1], 'rb')
        infile = open(sys.argv[2], 'rb')
    else:
        raise SystemExit("%s SCHEMAFILE [INFILE]" % (sys.argv[0],))
    try:
        obj = json.load(infile)
        schema = json.load(schemafile)
        validate(obj, schema)
    except ValueError as e:
        raise SystemExit(e)
