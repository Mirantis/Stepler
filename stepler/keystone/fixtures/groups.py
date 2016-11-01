"""
--------------
Group fixtures
--------------
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

from stepler.keystone import steps

__all__ = [
    'group_steps',
    'create_group',
]


@pytest.fixture
def group_steps(keystone_client):
    """Function fixture to get group steps.

    Args:
        keystone_client (object): instantiated keystone client

    Returns:
        stepler.keystone.steps.GroupSteps: instantiated group steps
    """
    return steps.GroupSteps(keystone_client.groups)


@pytest.yield_fixture
def create_group(group_steps):
    """Callable function fixture to create single keystone group with options.

    Can be called several times during a test.
    After the test it destroys all created groups.

    Args:
        group_steps (object): instantiated keystone steps

    Returns:
        function: function to create single keystone group with options
    """
    def _create_group(name, **kwargs):
        return group_steps.create_group(name, **kwargs)

    return _create_group
