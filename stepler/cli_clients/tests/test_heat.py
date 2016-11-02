"""
--------------
Heat CLI tests
--------------
"""

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import pytest

from stepler import config
from stepler.third_party import utils


@pytest.mark.idempotent_id('1fb54c78-20f5-459b-9515-3d7caf73ed64')
@pytest.mark.usefixtures('stacks_cleanup')
def test_stack_create_from_file(empty_heat_template_path, cli_heat_steps,
                                stack_steps):
    """**Scenario:** Create stack from template file with CLI.

    **Setup:**

    #. Upload template to node

    **Steps:**

    #. Create stack with template from file
    #. Check that stack is exists

    **Teardown:**

    #. Delete stack
    """
    parameters = {'param': 'string'}
    stack_name = next(utils.generate_ids('stack'))
    stack = cli_heat_steps.create_stack(
        name=stack_name,
        template_file=empty_heat_template_path,
        parameters=parameters)
    stack_steps.check_presence(
        stack['id'], timeout=config.STACK_CREATION_TIMEOUT)
