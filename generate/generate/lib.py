from functools import wraps
from os import path
import os
import sys
import json
import hashlib
import urlparse
import stat
import zipfile
import subprocess

from module_dynamic.lib import PopenWithoutNewConsole
import build

def task(function):
    build.Build.tasks[function.func_name] = function

    @wraps(function)
    def wrapper(*args, **kw):
        return function(*args, **kw)
    return wrapper

def predicate(function):
    build.Build.predicates[function.func_name] = function

    @wraps(function)
    def wrapper(*args, **kw):
        return function(*args, **kw)
    return wrapper

def path_to_lib():
    return path.abspath(path.join(
            __file__,
            path.pardir,
            path.pardir,
            'lib',
    ))

def ensure_lib_available(build, file, extract=False):
    # In case of forge-generate check for file
    server_path = path.abspath(path.join(path.split(path.abspath(__file__))[0], '..', '..', 'generate', 'lib', file))
    if path.isfile(server_path):
        return server_path

    lib_dir = path.join(path.dirname(build.source_dir), '.lib')
    hash_path = path.join(path.dirname(build.source_dir), '.template', 'lib', 'hash.json')
    if not path.exists(lib_dir):
        os.makedirs(lib_dir)

    # Hide directory on windows
    if sys.platform == 'win32':
        try:
            PopenWithoutNewConsole(['attrib', '+h', lib_dir]).wait()
        except Exception:
            # don't care if we fail to hide the templates dir
            pass

    hashes = None
    if path.exists(hash_path):
        with open(hash_path, 'r') as hash_file:
            hashes = json.load(hash_file)

    file_path = path.join(lib_dir, file)

    if path.exists(file_path) and file in hashes:
        # Check hash
        with open(file_path, 'rb') as cur_file:
            hash = hashlib.md5(cur_file.read()).hexdigest()
            if hash == hashes[file]:
                # File exists and is correct
                build.log.debug("File: %s, already downloaded and correct." % file)
                return file_path

    # File doesn't exist, or has the wrong hash or has no known hash - download
    build.log.info("Downloading lib file: %s, this will only happen when a new file is available." % file)

    from forge.remote import Remote
    from forge import build_config
    config = build_config.load()
    remote = Remote(config)

    server_details = urlparse.urlparse(remote.server)
    url = "{protocol}://{netloc}/lib-static/{platform_version}/{file}".format(
            protocol=server_details.scheme,
            netloc=server_details.netloc,
            platform_version=build.config['platform_version'],
            file=file
    )
    remote._get_file(url, file_path)

    if extract:
        if sys.platform == 'win32':
            with zipfile.ZipFile(file_path) as zipf:
                zipf.extractall(lib_dir)
        else:
            subprocess.check_call(['unzip', '-o', file_path, '-d', lib_dir])

    # Make file executable.
    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    return file_path

def dig(obj, path, default = None):
    '''Given a dict and a path, return a nested value or default'''
    for node in path:
        if type(obj) == dict and node in obj:
            obj = obj.get(node)
        else:
            return default
    return obj
