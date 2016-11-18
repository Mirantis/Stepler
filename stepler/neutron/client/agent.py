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

from stepler.neutron.client import base


class AgentManager(base.BaseNeutronManager):
    """Agent (neutron) manager."""

    NAME = 'agent'

    def list_agents(self, name=None):
        """Get neutron agents.

        Args:
            name (str|None): agent name, ex: neutron-l3-agent

        Returns:
            list: list of agents data (dict - binary, host, alive etc.)
        """
        kwargs = {}
        if name:
            kwargs['binary'] = name
        return self._rest_client.list_agents(**kwargs)['agents']
