"""
----------
Auth tests
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

import pytest


@pytest.mark.idempotent_id('7f35902f-81ca-4a69-a7dc-5b538195c14c',
                           any_one='admin')
@pytest.mark.idempotent_id('ca21eba8-932d-4a8b-b691-fbdc54448c8d',
                           any_one='user')
@pytest.mark.usefixtures('any_one')
def test_login(credentials, auth_steps):
    """**Scenario:** Verify that one can login and logout.

    **Steps:**

    #. Login to horizon
    #. Switch to user project
    #. Logout
    """
    auth_steps.login(credentials.username, credentials.password)
    auth_steps.switch_project(credentials.project_name)
    auth_steps.logout()
