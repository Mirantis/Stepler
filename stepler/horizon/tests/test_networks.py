"""
-------------
Network tests
-------------
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

from stepler.horizon.utils import generate_ids


@pytest.mark.usefixtures('any_one')
class TestAnyOne(object):
    """Tests for any user."""

    @pytest.mark.idempotent_id('6e212b0c-503e-4339-a504-4548344291ee')
    def test_subnet_add(self, network, networks_steps):
        """Verify that user can add subnet."""
        subnet_name = next(generate_ids('subnet'))
        networks_steps.add_subnet(network.name, subnet_name)


@pytest.mark.usefixtures('admin_only')
class TestAdminOnly(object):
    """Tests for admin only."""

    @pytest.mark.idempotent_id('ce3c02b9-ecb3-48c9-9ef4-b48172c6c111')
    def test_create_shared_network(self, networks_steps):
        """Verify that admin can create shared network."""
        network_name = next(generate_ids('network'))
        networks_steps.create_network(network_name, shared=True)

        networks_steps.delete_networks([network_name], check=False)
        networks_steps.close_notification('error')
        networks_steps.check_network_present(network_name)
        networks_steps.admin_delete_network(network_name)


@pytest.mark.usefixtures('user_only')
class TestUserOnly(object):
    """Tests for demo only."""

    @pytest.mark.idempotent_id('81869139-da99-4595-9bee-55862112ae1b')
    def test_not_create_shared_network(self, create_network, networks_steps):
        """Verify that demo can not create shared network."""
        network_name = next(generate_ids('network'))
        create_network(network_name, shared=True)
        networks_steps.check_network_share_status(network_name,
                                                  is_shared=False)
