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

from hamcrest import assert_that, is_not, empty  # noqa

from stepler import base
from stepler.third_party import steps_checker

__all__ = ['ResourceSteps']


class ResourceSteps(base.BaseSteps):
    """Heat resource steps"""

    @steps_checker.step
    def get_resources(self, stack, name=None, check=True):
        """Step to get list of resources.

        Args:
            stack (object): heat stack
            name (str): resource name
            check (bool): flag whether check step or not

        Returns:
            list: resource list for stack

        Raises:
            AssertionError: if check was failed
        """
        resources = self._client.list(stack_id=stack.id)

        if name:
            resources = [resource for resource in resources
                         if resource.resource_name == name]

        if check:
            assert_that(resources, is_not(empty()))

        return resources

    @steps_checker.step
    def get_resource(self, stack, name, check=True):
        """Step to get resource.

        Args:
            stack (object): heat stack
            name (str): resource name
            check (bool): flag whether check step or not

        Returns:
            object: stack resource
        """
        return self.get_resources(stack, name, check)[0]

    @steps_checker.step
    def check_that_resource_id_changed(self,
                                       physical_resource_id,
                                       stack,
                                       resource_name):
        """Step to check that after stack updating
        physical_resource_id was changed.

        Args:
            physical_resource_id (str): resource id before updating
            stack (object): heat stack
            resource_name (str): name of the resource

        Raises:
            AssertionError: if physical_resource_id wasn't changed
        """
        physical_resource_id_changed = self.get_resource(stack, resource_name)

        assert_that(physical_resource_id_changed, is_not(physical_resource_id))
