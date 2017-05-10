"""
-----------------
Floating IP tests
-----------------
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


@pytest.mark.usefixtures('any_one')
class TestAnyOne(object):
    """Tests for anyone."""

    @pytest.mark.idempotent_id('95546c8c-775a-4527-b92b-83cf56db999d',
                               any_one='admin')
    @pytest.mark.idempotent_id('57d7c23a-463e-49b7-843f-09ded9686fb9',
                               any_one='user')
    def test_floating_ip_associate(self, horizon_server, floating_ip,
                                   floating_ips_steps_ui):
        """**Scenario:** Verify that user can associate floating IP.

        **Setup:**

        #. Create floating IP using API
        #. Create server using API

        **Steps:**

        #. Associate floating IP to server using UI

        **Teardown:**

        #. Delete floating IP using API
        #. Delete server using API
        """
        floating_ips_steps_ui.associate_floating_ip(floating_ip.ip,
                                                    horizon_server.name)
