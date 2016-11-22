"""
-----------
Agent steps
-----------
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

from hamcrest import (assert_that, is_not, empty, only_contains,
                      has_entry)  # noqa H301

from stepler import base
from stepler.third_party.matchers import expect_that
from stepler.third_party import steps_checker
from stepler.third_party import waiter

__all__ = ["AgentSteps"]


class AgentSteps(base.BaseSteps):
    """Agent steps."""

    @steps_checker.step
    def get_agents(self, check=True, **kwargs):
        """Step to get agents by params in '**kwargs'.

        Args:
            check (bool, optional): flag whether to check step or not
            **kwargs: additional arguments to pass to API

        Returns:
            list: neutron agents

        Raises:
            AssertionError: if list of agents is empty
        """
        agents = list(self._client.find_all(**kwargs))
        if check:
            assert_that(agents, is_not(empty()))
        return agents

    @steps_checker.step
    def check_alive(self, agents, must_alive=True, timeout=0):
        """Verify step to check ``agents`` aliveness status.

        Args:
            agents (list): neutron agents to check status
            must_alive (bool, optional): flag whether all agents should be
                alive or not
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check failed after timeout
        """
        agents_ids = [agent['id'] for agent in agents]

        def _check_agents_alive():
            agents = [
                agent for agent in self.get_agents()
                if agent['id'] in agents_ids
            ]
            return expect_that(agents, only_contains(
                has_entry(alive=must_alive)))

        waiter.wait(_check_agents_alive, timeout_seconds=timeout)
