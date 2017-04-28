"""
--------------------
Host aggregate tests
--------------------
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


@pytest.mark.usefixtures('admin_only')
class TestAdminOnly(object):
    """Tests for admin only."""

    @pytest.mark.idempotent_id('8afb843e-1c38-4d21-b977-b45704cb74ad')
    def test_create_delete_host_aggregate(self, host_aggregates_steps_ui):
        """**Scenario:** Admin can create and delete host aggregate.

        **Steps:**

        #. Create host aggregate using UI
        #. Delete host aggregate using UI
        """
        host_aggregate_name = host_aggregates_steps_ui.create_host_aggregate()
        host_aggregates_steps_ui.delete_host_aggregate(host_aggregate_name)
