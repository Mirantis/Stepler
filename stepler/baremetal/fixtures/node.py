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

from stepler.baremetal.steps import IronicNodeSteps

__all__ = [
    'create_ironic_node',
    'ironic_node',
    'ironic_node_steps',
    'set_ironic_node_maintenance'
]


@pytest.fixture
def ironic_node_steps(ironic_client):
    """Fixture to get ironic node steps."""
    return IronicNodeSteps(ironic_client)


@pytest.yield_fixture
def create_ironic_node(ironic_node_steps):
    """Fixture to create ironic node with options.

    Can be called several times during test.
    """
    nodes = []

    def _create_ironic_node():
        node = ironic_node_steps.create_ironic_node()
        nodes.append(node)
        return node

    yield _create_ironic_node

    for node in nodes:
        ironic_node_steps.delete_node(node)


@pytest.fixture
def ironic_node(create_ironic_node):
    """Fixture to create ironic node with default options before test."""
    return create_ironic_node()


@pytest.fixture
def set_ironic_node_maintenance(ronic_node_steps):
    """Fixture to set node maintenance with default options before test."""
    return ironic_node_steps.set_ironic_node_maintenance()
