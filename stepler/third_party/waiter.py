"""
------
Waiter
------
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

import time

from stepler import config


def wait(predicate, timeout=0, polling_time=config.POLLING_TIME, rate=1,
         skipped_exceptions=()):
    """Wait that predicate execution returns non-falsy result.

    Notes:
        - It processes **error message of predicate result** if predicate
          returns tuple: ``(False, "Error message")``. This message will be
          attached to raised exception.

        - It makes early exit from waiting cycle if it sees, that polling time
          is higher than the time to the end of timeout, because it's obvious
          that next polling will not occur.

        - It provides to increase polling time by multiplying it to ``rate``
          in each waiting cycle.

        - It includes real timeout to error message, but not function defined.

        - It hides own error traceback in output.

    Args:
        predicate (function): predicate to wait execution result
        timeout (int): seconds to wait result
        polling_time (float): polling time between predicate executions
        rate (int): coefficient to multiply polling time
        skipped_exceptions (tuple): predicate exceptions which will be omitted
            during waiting.

    Returns:
        object: result of predicate execution

    Raises:
        AssertionError: if predicate execution is false after timeout
    """
    __tracebackhide__ = True

    start = time.time()
    limit = start + timeout
    first = True

    while time.time() < limit or first:
        first = False

        try:
            result = predicate()

        except skipped_exceptions as e:
            message = str(e)

        else:
            if isinstance(result, tuple):
                result, message = result

            if result:
                break

        if polling_time > limit - time.time():
            break

        time.sleep(polling_time)
        polling_time *= rate

    if result:
        return result

    else:
        error = '{} returned false with timeout {:.3f} seconds.'.format(
            predicate.__name__, time.time() - start)

        if message:
            error += ' ' + message

        raise AssertionError(error)
