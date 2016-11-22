"""
----------
Port steps
----------
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

from hamcrest import equal_to

from stepler import base
from stepler.third_party import steps_checker
from stepler.third_party import waiter

__all__ = ["PortSteps"]


class PortSteps(base.BaseSteps):
    """Port steps."""

    @steps_checker.step
    def create(self, network, check=True):
        """Step to create port.

        Args:
            network (dict): network to create port on
            check (bool): flag whether to check step or not

        Returns:
            dict: port
        """
        port = self._client.create(network_id=network['id'])
        if check:
            self.check_presence(port)
        return port

    @steps_checker.step
    def delete(self, port, check=True):
        """Step to create port.

        Args:
            port (dict): port to delete
            check (bool): flag whether to check step or not
        """
        self._client.delete(port['id'])
        if check:
            self.check_presence(port, must_present=False)

    @steps_checker.step
    def check_presence(self, port, must_present=True, timeout=0):
        """Verify step to check port is present.

        Args:
            port (dict): neutron port to check presence status
            must_present (bool): flag whether port must present or not
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check failed after timeout
        """
        def _check_port_presence():
            is_present = bool(self._client.find_all(id=port['id']))
            return waiter.expect_that(is_present, equal_to(must_present))

        waiter.wait(_check_port_presence, timeout_seconds=timeout)
