"""
----------
Host steps
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

from hamcrest import (assert_that, is_not, equal_to, empty,
                      greater_than_or_equal_to)  # noqa

from stepler import base
from stepler.third_party import steps_checker

__all__ = [
    'HostSteps'
]


class HostSteps(base.BaseSteps):
    """Host steps."""

    @steps_checker.step
    def get_hosts(self, check=True):
        """Step to get hosts.

        Args:
            check (bool|True): flag whether check step or not

        Returns:
            list: list of hosts objects

        Raises:
            AssertionError: if hosts list is empty
        """
        hosts = list(self._client.list())
        if check:
            assert_that(hosts, is_not(empty()))

        return hosts

    @steps_checker.step
    def get_host(self, name, check=True):
        """Step to get host by name.

        Args:
            name (str): host name
            check (bool|True): flag whether check step or not

        Returns:
            list: list of hosts objects

        Raises:
            AssertionError: if host is not found
        """
        hosts = [host for host in self.get_hosts() if host.host_name == name]

        if check:
            assert_that(len(hosts), equal_to(1))

        return hosts[0]

    @steps_checker.step
    def get_usage_data(self, host, check=True):
        """Step to get cpu/memory/hdd data for host.

        # usage_data is the list of the following elements:
        # elem 0 - 'total' data, 1 - 'used now' data, 2 - 'used max' data
        # next elements - for VMs (one element per project)
        # Every element consists of project, cpu, memory_mb, disk_gb etc.

        Args:
            host (object): host
            check (bool|True): flag whether check step or not

        Raises:
            AssertionError: if usage data has less than 3 elements
        """
        usage_data = self._client.get(host.host_name)

        if check:
            assert_that(len(usage_data), greater_than_or_equal_to(3))
            for data in usage_data:
                for attr in ['project', 'cpu', 'memory_mb', 'disk_gb']:
                    assert_that(hasattr(data, attr))
            assert_that(usage_data[0].project, equal_to('(total)'))
            assert_that(usage_data[1].project, equal_to('(used_now)'))
            assert_that(usage_data[2].project, equal_to('(used_max)'))

        return usage_data

    @steps_checker.step
    def check_host_usage_changing(self, host, usage_data_old,
                                  changed=True, project_id=None):
        """Step to check changes in host usages (cpu/memory/hdd)

        This step gets current usage data and compares them with old data.
        There are two modes of checks: changes are expected or not.
        Depending on it, values must be different or equal. Also, this step
        can check project ID in host usage.

        The following data are checked:
        - cp, memory_mb, disk_gb (for 'used now' and 'used max')
        - number of elements in usage data (number of projects)
        - project ID (only for checked=True)

        Args:
            host (object): host
            usage_data_old (object): usage data got before
            changed (bool|True): indicator that some VMs are added/deleted
            project_id (str|None): project id of VMs created before (optional)

        Raises:
            AssertionError
        """
        usage_data_new = self.get_usage_data(host)

        # only 'used now' (elem 1) and 'used max' (elem 2) data are checked
        for ind in (1, 2):
            for attr in ['cpu', 'memory_mb', 'disk_gb']:
                value_old = getattr(usage_data_old[ind], attr)
                value_new = getattr(usage_data_new[ind], attr)
                if changed:
                    assert_that(value_new, is_not(equal_to(value_old)))
                else:
                    assert_that(value_new, equal_to(value_old))

        value_old = len(usage_data_old)
        value_new = len(usage_data_new)
        if changed:
            assert_that(value_new, is_not(equal_to(value_old)))
        else:
            assert_that(value_new, equal_to(value_old))

        if project_id:
            assert_that(project_id, equal_to(usage_data_new[-1].project))
