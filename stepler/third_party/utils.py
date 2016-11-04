"""
-----
Utils
-----
"""

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import email.utils
import inspect
import logging
import os
import random
import tempfile
import uuid

import requests
import six

from stepler import config

if six.PY3:
    basestring = str

LOGGER = logging.getLogger(__name__)

__all__ = [
    'generate_ids',
    'generate_files',
    'get_file_path',
    'get_volume_migrate_host',
    'get_unwrapped_func',
    'is_iterable',
]


def generate_mac_addresses(count=1):
    """Generate unique mac addresses.

     Arguments:
         - count: count of uniq  mac addresses, default is 1.

    Returns:
        - generator of uniq mac addresses.
    """
    for _ in range(count):
        mac = [0x00, 0x24, 0x81,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        mac_address = ':'.join(map(lambda x: "%02x" % x, mac))
        yield mac_address


def generate_ids(prefix=None, postfix=None, count=1, length=None):
    """Generate unique identificators, based on UUID.

    Arguments:
        prefix (string|None): prefix of unique ids.
        postfix (string|None): postfix of unique ids.
        count (int|1): count of unique ids.
        length (int|None): length of unique ids.

    Returns:
        generator: unique ids.
    """
    for _ in range(count):
        uid = str(uuid.uuid4())
        if prefix:
            # mix constant stepler prefix to separate tested objects
            uid = '{}-{}-{}'.format(config.STEPLER_PREFIX, prefix, uid)
        if postfix:
            uid = '{}-{}'.format(uid, postfix)
        if length:
            uid = (uid * (length / len(uid) + 1))[:length]
        yield uid


def generate_files(prefix=None, postfix=None, folder=None, count=1, size=1024):
    """Generate files with unique names.

    Arguments:
        prefix (string|None): prefix of unique ids.
        postfix (string|None): postfix of unique ids.
        folder (string|None): folder to create unique files.
        count (int|1): count of unique ids.
        size (int|1024): size of unique files.

    Returns:
        generator: files with unique names.
    """
    folder = folder or tempfile.mkdtemp()
    if not os.path.isdir(folder):
        os.makedirs(folder)

    for uid in generate_ids(prefix, postfix, count):
        file_path = os.path.join(folder, uid)

        with open(file_path, 'wb') as f:
            f.write(os.urandom(size))

        yield file_path


def generate_ips(ip_start=1, ip_end=254, count=1):
    """Generates random IP v4 addresses.
        Like: 173.217.169.131, 207.105.178.224, 193.121.141.217

    Arguments:
        ip_start (int): Start range of the generated sequence
        ip_end (int): End range of the generated sequence
        count (int): count of unique ids.

    Returns:
        generator: Random IP addresses
    """
    for _ in range(count):
        yield ".".join(
            [str(random.randint(ip_start, ip_end)) for _ in range(4)])


# TODO(schipiga): copied from mos-integration-tests, need refactor.
def get_file_path(url, name=None):
    """Download file by URL to local cached storage.

    Arguments:
        url (string): URL of file location.
        name (string|None): file name.

    Returns:
        string: file path of downloaded file.
    """
    def _get_file_name(url):
        keepcharacters = (' ', '.', '_', '-')
        filename = url.rsplit('/')[-1]
        return "".join(c for c in filename
                       if c.isalnum() or c in keepcharacters).rstrip()

    if os.path.isfile(url):
        return url

    if not os.path.exists(config.TEST_IMAGE_PATH):
        try:
            os.makedirs(config.TEST_IMAGE_PATH)
        except Exception as e:
            LOGGER.warning("Can't make dir for files: {}".format(e))
            return None

    if not name:
        name = _get_file_name(url)

    file_path = os.path.join(config.TEST_IMAGE_PATH, name)
    headers = {}
    if os.path.exists(file_path):
        file_date = os.path.getmtime(file_path)
        headers['If-Modified-Since'] = email.utils.formatdate(file_date,
                                                              usegmt=True)

    response = requests.get(url, stream=True, headers=headers)

    if response.status_code == 304:
        LOGGER.info("Image file is up to date")
    elif response.status_code == 200:
        LOGGER.info("Start downloading image")
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(65536):
                f.write(chunk)
        LOGGER.info("Image downloaded")
    else:
        LOGGER.warning("Can't get fresh image. HTTP status code is "
                       "{0.status_code}".format(response))

    response.close()
    return file_path


def get_unwrapped_func(func):
    """Get original function under decorator.

    Decorator hides original function inside itself. But in some cases it's
    important to get access to original function, for ex: for documentation.

    Args:
        func (function): function that can be potentially a decorator which
            hides original function

    Returns:
        function: unwrapped function or the same function
    """
    if not inspect.isfunction(func) and not inspect.ismethod(func):
        return func

    if func.__name__ != func.func_code.co_name:
        for cell in func.func_closure:
            obj = cell.cell_contents
            if inspect.isfunction(obj):
                if func.__name__ == obj.func_code.co_name:
                    return obj
                else:
                    return get_unwrapped_func(obj)
    return func


def is_iterable(obj):
    """Define whether object is iterable or no (skip strings).

    Args:
        obj (object): obj to define whether it's iterable or no

    Returns:
        bool: True or False
    """
    if isinstance(obj, basestring):
        return False

    try:
        iter(obj)
        return True

    except TypeError:
        return False


def slugify(string):
    """Replace non-alphanumeric symbols to underscore in string.

    Args:
        string (str): string to replace

    Returns:
        str: replace string
    """
    return ''.join(s if s.isalnum() else '_' for s in string).strip('_')


def get_volume_migrate_host(nodes, host):
    """Get cinder host to migrate volume.

    Arguments:
        nodes (FuelNodes): cinder nodes
        host (string): initial volume host

    Returns:
        string: host to volume migrate
        None: if no host found
    """
    for node in nodes:
        if not host.startswith(node.fqdn):
            return node.fqdn + config.VOLUME_HOST_POSTFIX