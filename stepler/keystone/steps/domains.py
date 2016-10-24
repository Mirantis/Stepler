"""
------------
Domain steps
------------
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

from hamcrest import assert_that, is_not, empty, equal_to  # noqa
from waiting import wait

from stepler.base import BaseSteps
from stepler.third_party.steps_checker import step

__all__ = [
    'DomainSteps'
]


class DomainSteps(BaseSteps):
    """Domain steps."""

    @step
    def get_domains(self, check=True):
        """Step to get domains.

        Args:
            check (bool): flag whether to check step or not

        Returns:
            list of objects: list of domains
        """
        domains = list(self._client.list())

        if check:
            assert_that(domains, is_not(empty()))
        return domains

    @step
    def get_domain(self, name, check=True):
        """Step to find domain.

        Args:
            name (str) - domain name

        Raises:
            NotFound: if domain does not exist

        Returns:
            object: domain
        """
        domain = self._client.find(name=name)

        if check:
            assert_that(domain.name, equal_to(name))

        return domain

    @step
    def create_domain(self, domain_name, check=True):
        """Step to create domain.

        Args:
            domain_name (str): domain name
            check (bool): flag whether to check step or not

        Returns:
            object: domain
        """
        domain = self._client.create(domain_name)

        if check:
            self.check_domain_presence(domain)
            assert_that(domain.name, equal_to(domain_name))

        return domain

    @step
    def delete_domain(self, domain, check=True):
        """Step to delete domain.

        Args:
            domain (object): domain
            check (bool): flag whether to check step or not
        """
        self._client.update(domain, enabled=False)
        self._client.delete(domain.id)

        if check:
            self.check_domain_presence(domain, present=False)

    @step
    def check_domain_presence(self, domain, present=True, timeout=0):
        """Step to check domain presence.

        Args:
            domain (object): domain
            present (bool): flag whether domain should present or no
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check is failed after timeout
        """
        def predicate():
            try:
                self._client.get(domain.id)
                return present
            except Exception:
                return not present

        wait(predicate, timeout_seconds=timeout)
