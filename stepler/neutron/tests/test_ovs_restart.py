"""
-------------------------
Neutron OVS restart tests
-------------------------
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

from stepler import config

pytestmark = pytest.mark.requires("computes_count_gte(2)")


@pytest.mark.idempotent_id('ee080cc2-b658-42cf-ac0b-f5eab906fcf5')
def test_restart_with_pcs_disable_enable(
        neutron_2_servers_different_networks,
        nova_floating_ip,
        server_steps,
        os_faults_steps):
    """**Scenario:** Restart OVS-agents with pcs disable/enable on controllers.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network_1 with subnet_1 and router
    #. Create server_1
    #. Create floating ip
    #. Create network_2 with subnet_2
    #. Add network_2 interface to router
    #. Create server_2 on another compute and connect it to network_2

    **Steps:**

    #. Attach floating IP to server_1
    #. Check ping from server_1 to server_2
    #. Restart ovs-agents with pcs enable/disable on controllers
    #. Check ping from server_1 to server_2

    **Teardown:**

    #. Delete servers
    #. Delete networks, subnets, router
    #. Delete floating IP
    #. Delete security group
    #. Delete cirros image
    #. Delete flavor
    """
    server_1, server_2 = neutron_2_servers_different_networks.servers

    server_steps.attach_floating_ip(server_1, nova_floating_ip)
    server_2_fixed_ip = next(iter(server_steps.get_ips(server_2,
                                                       config.FIXED_IP)))

    with server_steps.get_server_ssh(server_1) as server_ssh:
        server_steps.check_ping_for_ip(
            server_2_fixed_ip, server_ssh,
            timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)

    os_faults_steps.restart_services([config.NEUTRON_OVS_SERVICE])

    with server_steps.get_server_ssh(server_1) as server_ssh:
        server_steps.check_ping_for_ip(
            server_2_fixed_ip, server_ssh,
            timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)


@pytest.mark.idempotent_id('310c630d-38f0-402b-9423-ffb14fb766b2')
def test_restart_with_pcs_ban_clear(
        neutron_2_servers_different_networks,
        nova_floating_ip,
        server_steps,
        os_faults_steps):
    """**Scenario:** Restart OVS-agents with pcs ban/clear on controllers.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network_1 with subnet_1 and router
    #. Create server_1
    #. Create floating ip
    #. Create network_2 with subnet_2
    #. Add network_2 interface to router
    #. Create server_2 on another compute and connect it to network_2

    **Steps:**

    #. Attach floating IP to server_1
    #. Check ping from server_1 to server_2
    #. Restart ovs-agents with pcs ban/clear on controllers
    #. Check ping from server_1 to server_2

    **Teardown:**

    #. Delete servers
    #. Delete networks, subnets, router
    #. Delete floating IP
    #. Delete security group
    #. Delete cirros image
    #. Delete flavor
    """
    server_1, server_2 = neutron_2_servers_different_networks.servers

    server_steps.attach_floating_ip(server_1, nova_floating_ip)
    server_2_fixed_ip = next(iter(server_steps.get_ips(server_2,
                                                       config.FIXED_IP)))

    with server_steps.get_server_ssh(server_1) as server_ssh:
        server_steps.check_ping_for_ip(
            server_2_fixed_ip, server_ssh,
            timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)

    nodes = os_faults_steps.get_nodes(
        service_names=[config.NEUTRON_OVS_SERVICE])
    os_faults_steps.terminate_service(config.NEUTRON_OVS_SERVICE, nodes=nodes)

    os_faults_steps.start_service(config.NEUTRON_OVS_SERVICE, nodes=nodes)

    with server_steps.get_server_ssh(server_1) as server_ssh:
        server_steps.check_ping_for_ip(
            server_2_fixed_ip, server_ssh,
            timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)


@pytest.mark.idempotent_id('ab973d26-55e0-478c-b5fd-35a3ea47e583')
def test_restart_many_times(
        neutron_2_servers_different_networks,
        nova_floating_ip,
        server_steps,
        os_faults_steps,
        agent_steps):
    """**Scenario:** Restart OVS-agents many times.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network_1 with subnet_1 and router
    #. Create server_1
    #. Create floating ip
    #. Create network_2 with subnet_2
    #. Add network_2 interface to router
    #. Create server_2 on another compute and connect it to network_2

    **Steps:**

    #. Attach floating IP to server_1
    #. Start ping from server_1 to server_2
    #. Restart ovs-agents
    #. Check that ping loss is not more than 2
    #. Repeat last 3 steps 40 times

    **Teardown:**

    #. Delete servers
    #. Delete networks, subnets, router
    #. Delete floating IP
    #. Delete security group
    #. Delete cirros image
    #. Delete flavor
    """
    server_1, server_2 = neutron_2_servers_different_networks.servers

    server_steps.attach_floating_ip(server_1, nova_floating_ip)
    server_2_fixed_ip = next(
        iter(server_steps.get_ips(server_2, config.FIXED_IP)))

    ovs_agents = agent_steps.get_agents(binary=config.NEUTRON_OVS_SERVICE)
    with server_steps.get_server_ssh(server_1) as server_ssh:
        for _ in range(40):
            with server_steps.check_ping_loss_context(
                    server_2_fixed_ip,
                    max_loss=config.NEUTRON_OVS_RESTART_MAX_PING_LOSS,
                    server_ssh=server_ssh):
                os_faults_steps.restart_services([config.NEUTRON_OVS_SERVICE])
                agent_steps.check_alive(
                    ovs_agents,
                    must_alive=True,
                    timeout=config.NEUTRON_AGENT_ALIVE_TIMEOUT)


@pytest.mark.idempotent_id('6188b10f-c8f1-4d00-9c97-d163503592a5')
def test_restart_with_broadcast_traffic(
        neutron_2_servers_same_network,
        nova_floating_ip,
        server_steps,
        os_faults_steps,
        agent_steps):
    """**Scenario:** Restart OVS-agents with broadcast traffic on background.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and router
    #. Create server_1
    #. Create floating ip
    #. Create server_2 on another compute and connect it to network

    **Steps:**

    #. Attach floating IP to server_1
    #. Start arping from server_1 to server_2
    #. Restart ovs-agents
    #. Check that ping loss is not more than 50

    **Teardown:**

    #. Delete servers
    #. Delete network, subnet, router
    #. Delete floating IP
    #. Delete security group
    #. Delete cirros image
    #. Delete flavor
    """
    server_1, server_2 = neutron_2_servers_same_network.servers

    server_steps.attach_floating_ip(server_1, nova_floating_ip)
    server_2_fixed_ip = next(
        iter(server_steps.get_ips(server_2, config.FIXED_IP)))

    ovs_agents = agent_steps.get_agents(binary=config.NEUTRON_OVS_SERVICE)
    with server_steps.get_server_ssh(server_1) as server_ssh:
        with server_steps.check_arping_loss_context(
                server_ssh,
                ip=server_2_fixed_ip,
                max_loss=config.NEUTRON_OVS_RESTART_MAX_ARPING_LOSS):
            os_faults_steps.restart_services([config.NEUTRON_OVS_SERVICE])
            agent_steps.check_alive(
                ovs_agents,
                timeout=config.NEUTRON_AGENT_ALIVE_TIMEOUT)


@pytest.mark.idempotent_id('f3935941-4262-41b3-bedb-d9777e63895f')
def test_restart_with_iperf_traffic(
        neutron_2_servers_iperf_different_networks,
        nova_floating_ip,
        server_steps,
        os_faults_steps,
        agent_steps):
    """**Scenario:** Restart OVS-agents with broadcast traffic on background.

    **Setup:**

    #. Create ubuntu image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and router
    #. Create network_2 with subnet_2
    #. Create server_1
    #. Create server_2 on another compute and connect it to network
    #. Create floating ip

    **Steps:**

    #. Attach floating IP to server_1
    #. Start iperf traffic from server_1 to server_2, wait it done
    #. Check that iperf loss is 0
    #. Start iperf traffic from server_1 to server_2
    #. Restart ovs-agents
    #. Check that iperf loss is not more than 10%

    **Teardown:**

    #. Delete servers
    #. Delete network, subnet, router
    #. Delete floating IP
    #. Delete security group
    #. Delete ubuntu image
    #. Delete flavor
    """
    server_1, server_2 = neutron_2_servers_iperf_different_networks.servers

    server_steps.attach_floating_ip(server_1, nova_floating_ip)
    server_2_fixed_ip = next(
        iter(server_steps.get_ips(server_2, config.FIXED_IP)))

    ovs_agents = agent_steps.get_agents(binary=config.NEUTRON_OVS_SERVICE)
    with server_steps.get_server_ssh(server_1) as server_ssh:
        with server_steps.check_iperf_loss_context(
                server_ssh,
                ip=server_2_fixed_ip,
                port=config.IPERF_UDP_PORT,
                max_loss=0):
            pass
        with server_steps.check_iperf_loss_context(
                server_ssh,
                ip=server_2_fixed_ip,
                port=config.IPERF_UDP_PORT,
                max_loss=config.NEUTRON_OVS_RESTART_MAX_IPERF_LOSS):
            os_faults_steps.restart_services([config.NEUTRON_OVS_SERVICE])
            agent_steps.check_alive(
                ovs_agents,
                timeout=config.NEUTRON_AGENT_ALIVE_TIMEOUT)
