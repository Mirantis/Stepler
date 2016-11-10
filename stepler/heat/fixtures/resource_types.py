"""
----------------------------
Heat resource types fixtures
----------------------------
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

from stepler.heat import steps

__all__ = [
    'heat_resource_type_steps',
]


@pytest.fixture
def heat_resource_type_steps(heat_client):
    """Function fixture to get heat resource types steps.

    Args:
        heat_client (object): initialized heat client

    Returns:
        stepler.heat.steps.ResourceTypeSteps: initialized heat resource types
            steps
    """
    return steps.ResourceTypeSteps(heat_client.resource_types)
