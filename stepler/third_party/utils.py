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
import hashlib
import inspect
import logging
from multiprocessing import dummy as mp
import os
import random
import tempfile
import uuid

import attrdict
import requests
import six

from stepler.third_party import context


if six.PY3:
    basestring = str

LOGGER = logging.getLogger(__name__)

__all__ = [
    'AttrDict',
    'generate_ids',
    'generate_files',
    'generate_file_context',
    'generate_ips',
    'get_file_path',
    'get_size',
    'get_unwrapped_func',
    'is_iterable',
    'slugify',
    'background',
    'join_process',
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


def generate_ids(prefix=None, postfix=None, count=1, length=50,
                 use_unicode=False, _stepler_prefix=None):
    """Generate unique identificators, based on UUID.

    Arguments:
        prefix (str|None): prefix of unique ids
        postfix (str|None): postfix of unique ids
        count (int): count of unique ids
        length (int): length of unique ids
        use_unicode (boolean|False): generate str with unicode or not
        _stepler_prefix (str, optional): Resources prefix is used to call
            ``generate_ids`` inside ``stepler.config`` and avoid cross imports
            problem. By default it has value ``stepler.config.STEPLER_PREFIX``.

    Returns:
        generator: unique ids
    """
    # TODO(schipiga): thirdparty module should know nothing about stepler
    # configured values. We hack it for usability.
    # ``If``-statement is used to allow ``generate_ids`` inside
    # ``stepler.config`` and prevent cross imports problem.
    if not _stepler_prefix:
        from stepler import config
        _stepler_prefix = config.STEPLER_PREFIX

    # hash usually should have >= 7 symbols
    min_uid_length = 7

    const_length = len(_stepler_prefix + '-' +
                       (prefix + '-' if prefix else '') +
                       # uid will be here
                       ('-' + postfix if postfix else ''))

    uid_length = length - const_length

    if uid_length < min_uid_length:
        raise ValueError(
            "According to passed prefix and postfix minimal length to "
            "generate unique id must be equal or greater "
            "than {0}.".format(const_length + min_uid_length))

    for _ in range(count):
        # mix constant stepler prefix to separate tested objects
        uid = _stepler_prefix

        if prefix:
            uid += '-' + prefix

        if use_unicode:
            uid += '-' + u"".join(
                six.unichr(random.choice(range(0x0400, 0x045F)))
                for _ in range(uid_length))
        else:
            uid_val = str(uuid.uuid4())
            uid_val = (uid_val * (uid_length / len(uid_val) + 1))[:uid_length]
            uid += '-' + uid_val

        if postfix:
            uid += '-' + postfix

        yield uid


def generate_files(prefix=None, postfix=None, folder=None, count=1, size=1024):
    """Generate files with unique names.

    Arguments:
        prefix (str|None): prefix of unique ids.
        postfix (str|None): postfix of unique ids.
        folder (str|None): folder to create unique files.
        count (int): count of unique ids.
        size (int): size of unique files.

    Returns:
        generator: files with unique names.
    """
    folder = folder or tempfile.mkdtemp()
    if not os.path.isdir(folder):
        os.makedirs(folder)

    for uid in generate_ids(prefix, postfix, count):
        file_path = os.path.join(folder, uid)

        with open(file_path, 'wb') as f:
            f.seek(size - 1)
            f.write('0')

        yield file_path


@context.context
def generate_file_context(prefix=None, postfix=None, folder=None, size=1024):
    """Context manager to generate file with unique name and delete it later.

    Useful for large files.

    Arguments:
        prefix (str|None): prefix of unique id
        postfix (str|None): postfix of unique id
        folder (str|None): folder to create unique file
        size (int): size of unique file (in bytes)

    Yields:
        str: file path.
    """
    file_path = next(generate_files(prefix=prefix, postfix=postfix,
                                    folder=folder, size=size))
    yield file_path

    os.remove(file_path)


def generate_ips(ip_start=1, ip_end=254, count=1):
    """Generate random IP v4 addresses.

    Examples:
        173.217.169.131, 207.105.178.224, 193.121.141.217

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
        url (str): URL of file location.
        name (str|None): file name.

    Returns:
        str: file path of downloaded file.
    """
    # TODO(schipiga): thirdparty module should know nothing about stepler
    # configured values. We hack it for usability.
    from stepler import config

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
        obj (object): obj to define whether it's iterable or not

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


def get_size(value, to):
    """Get size of value with specified type."""
    _map = {'TB': 1024 * 1024 * 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'MB': 1024 * 1024,
            'KB': 1024}

    value = value.upper()
    to = to.upper()

    for k, v in _map.items():
        if value.endswith(k):
            value = int(value.strip(k).strip()) * v
            break
    else:
        value = int(value) * 1024

    for k, v in _map.items():
        if to == k:
            return value / v


class AttrDict(attrdict.AttrDict):
    """Wrapper over attrdict to provide context manager to update fields."""

    _updated_fields = {}

    def __init__(self, *args, **kwgs):
        """Constructor."""
        super(AttrDict, self).__init__(*args, **kwgs)

    def put(self, **kwgs):
        """Put fields to update in buffer."""
        self._updated_fields[id(self)] = kwgs
        return self

    def __enter__(self):
        """Enter to context manager."""
        pass

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Update fields from buffer on exit from context manager."""
        updated_fields = self._updated_fields.pop(id(self))
        self.update(updated_fields)


def get_md5sum(file_path, size=4096):
    """Get md5 hash sum of file.

    Args:
        file_path (str): path to file
        size (int): chunk size to read content

    Returns:
        str: md5 hash sum of file
    """
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def background(f, *args, **kwargs):
    """Run function in separate thread.

    Args:
        f (function): function to call in background
        *args: function args
        **kwargs: function kwargs

    Returns:
        Process: started process instance
    """
    p = mp.Process(target=f, args=args, kwargs=kwargs)
    p.start()
    return p


def join_process(process):
    """Wait until process to be done.

    Args:
        process (Process): process
    """
    process.join()
