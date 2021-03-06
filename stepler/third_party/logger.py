"""
----------------
Logger for steps
----------------
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

import functools
import logging
import time

import six

LOGGER = logging.getLogger('stepler.func_logger')


def log(func):
    """Decorator to log function with arguments and execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwgs):
        # reject self from log args if it is present
        __tracebackhide__ = True
        log_args = _reject_self_from_args(func, args)

        func_name = getattr(func, '__name__', str(func))
        LOGGER.debug(
            'Function {!r} starts with args {!r} and kwgs {!r}'.format(
                func_name, log_args, kwgs))
        start = time.time()
        try:
            result = func(*args, **kwgs)
        finally:
            LOGGER.debug('Function {!r} ended in {:.4f} sec'.format(
                func_name, time.time() - start))
        return result

    return wrapper


def _reject_self_from_args(func, args):
    if len(args) == 0:
        return args
    try:
        self = six.get_method_self(func)
    except Exception:
        return args
    if args[0] == self:
        return args[1:]
    else:
        return args
