"""
--------------------------
Tests for swift CLI client
--------------------------
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

from stepler.third_party import utils


@pytest.mark.idempotent_id('0f055e9b-1caa-4f86-ab99-c1d51e4978c7')
def test_containers_list_contains_created_container(cli_swift_steps,
                                                    container_steps):
    """**Scenario:** Check container list contains created container.

    **Steps:**

    #. Create container via Swift API
    #. Check that created container is in list using CLI

    **Teardown:**

    #. Delete container
    """
    container_name = next(utils.generate_ids())
    container_steps.create(name=container_name)
    cli_swift_steps.check_containers_list_contains(container_name)
