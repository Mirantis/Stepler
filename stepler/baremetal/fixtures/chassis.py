"""
-----------------------
Ironic chassis fixtures
-----------------------
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

import pytest

from stepler.baremetal import steps

__all__ = [
    'create_ironic_chassis',
    'ironic_chassis_steps',
]


@pytest.fixture
def ironic_chassis_steps(ironic_client):
    """Callable session fixture to get ironic steps.

    Args:
        ironic_client (function): function to get ironic client

    Returns:
        function: function to instantiated ironic steps
    """
    return steps.IronicChassisSteps(ironic_client.chassis)


@pytest.yield_fixture
def create_ironic_chassis(ironic_chassis_steps):
    """Callable function fixture to create ironic chassis with options.

    Can be called several times during a test.
    After the test it destroys all created chassis.

    Args:
        ironic_chassis_steps (object): instantiated ironic steps

    Returns:
        function: function to create chassis as batch with options
    """
    _chassis_steps = ironic_chassis_steps

    chassis = _chassis_steps.get_chassis(check=False)
    # chassis_ids_before = {chs.uuid for chs in chassis}

    yield _chassis_steps
    cleanup_chassis()

    # cleanup_chassis(_chassis_steps, chassis_ids_to_delete=chassis_ids_before)


@pytest.fixture(scope='session')
def cleanup_chassis():
    def _cleanup_chassis(_chassis_steps, limit=0):
        deleting_chassis = []

        for chs in _chassis_steps.get_chassis(check=False):
            deleting_chassis.append(chs)

        if len(deleting_chassis) > limit:
            _chassis_steps.delete_ironic_chassis()

    return _cleanup_chassis
