"""
------------------------------
Environment dependent fixtures
------------------------------
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

__all__ = [
    'admin_ssh_key_path',
    'auth_url',
    'ip_by_host',
]


@pytest.fixture
def auth_url(env):
    """Fixture to get auth url."""
    return 'http://{0}:5000/v2.0/'.format(env.get_primary_controller_ip())


@pytest.fixture
def admin_ssh_key_path(env):
    """Fixture to admin ssh key.pem path."""
    return env.admin_ssh_keys_paths[0]


@pytest.fixture
def ip_by_host(env):
    """Fixture to get ip by host name."""
    def _ip_by_host(hostname):
        return env.find_node_by_fqdn(hostname).data['ip']

    return _ip_by_host
