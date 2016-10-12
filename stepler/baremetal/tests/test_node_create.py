"""
-----------------
Ironic node tests
-----------------
"""

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


def test_node_create(ironic_node_steps):
    """**Scenario:** Verify that ironic node can be created and deleted.

    **Steps:**

    #. Create ironic node
    #. Delete ironic node
    """
    node = ironic_node_steps.create_ironic_node()
    ironic_node_steps.delete_ironic_node(node)
