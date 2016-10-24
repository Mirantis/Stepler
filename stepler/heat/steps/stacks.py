"""
----------------
Heat stack steps
----------------
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

from hamcrest import assert_that, equal_to, is_not, empty  # noqa
import waiting

from stepler import base
from stepler import config
from stepler.third_party import steps_checker

__all__ = ['StackSteps']


class StackSteps(base.BaseSteps):
    """Heat stack steps."""

    @steps_checker.step
    def create(self, name, template, parameters=None, files=None, check=True):
        """Step to create stack.

        Args:
            name (str): name of stack
            template (str): yaml template content for create stack from
            parameters (dict|None): parameters for template
            files (dict|None): in case if template uses file as reference
                e.g: "type: volume_with_attachment.yaml"
            check (bool): flag whether check step or not

        Returns:
            object: heat stack
        """
        parameters = parameters or {}
        files = files or {}
        response = self._client.create(
            stack_name=name,
            template=template,
            files=files,
            parameters=parameters)

        stack = self._client.get(response['stack']['id'])
        if check:
            self.check_status(
                stack,
                config.HEAT_COMPLETE_STATUS,
                transit_statuses=[config.HEAT_IN_PROGRESS_STATUS],
                timeout=config.STACK_CREATION_TIMEOUT)

        return stack

    @steps_checker.step
    def check_status(self, stack, status, transit_statuses=(), timeout=0):
        """Verify step to check stack status.

        Args:
            stack (obj): heat stack to check its status
            status (str): expected stack status
            transit_statuses (iterable): allowed transit statuses
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was falsed after timeout
        """

        def predicate():
            stack.get()
            return stack.status.lower() not in transit_statuses

        waiting.wait(predicate, timeout_seconds=timeout)
        assert_that(stack.status.lower(), equal_to(status.lower()))

    @steps_checker.step
    def get_stacks(self, check=True):
        """Step to retrieve stacks from heat.

        Args:
            check (bool): flag whether to check step or not
        Returns:
            list: stacks list
        """
        stacks = list(self._client.list())

        if check:
            assert_that(stacks, is_not(empty()))

        return stacks

    @steps_checker.step
    def delete(self, stack, check=True):
        """Step to delete stack.

        Args:
            stack (obj): stack to delete
            check (bool): flag whether to check step or not
        Rasies:
            Time
        """
        stack.delete()

        if check:
            self.check_presence(
                stack, present=False, timeout=config.STACK_DELETING_TIMEOUT)

    @steps_checker.step
    def check_presence(self, stack, present=True, timeout=0):
        """Check-step to check heat stack presence.

        Args:
            stack (obj): heat stack
            present (bool): flag to check is stack present or absent
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was falsed after timeout
        """

        def predicate():
            try:
                next(self._client.list(id=stack.id))
                return present
            except StopIteration:
                return not present

        waiting.wait(predicate, timeout_seconds=timeout)
