import os
import validictory_module
import json

def json_schema(manifest, file, schema, **kw):
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "module", file))
    schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "schema", "module_"+schema+"_schema.json"))

    with open(file_path, "rb") as file_file:
        file_json = json.load(file_file)

    with open(schema_path, "rb") as schema_file:
        schema_json = json.load(schema_file)

    validictory_module.validate(file_json, schema_json)


def valid_bundle(manifest, file, **kw):
    bundle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "module", file))

    if not bundle_path.endswith(".bundle"):
        raise Exception("Folder '%s' is not a valid bundle, bundle names always end '.bundle'" % (file))


def valid_framework(manifest, file, **kw):
    bundle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "module", file))

    if not bundle_path.endswith(".framework"):
        raise Exception("Folder '%s' is not a valid framework, framework names always end '.framework'" % (file))
