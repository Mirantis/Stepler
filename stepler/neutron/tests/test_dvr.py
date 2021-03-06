"""
-----------------
Neutron DVR tests
-----------------
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

import time

import pytest

from stepler import config
from stepler.third_party import utils

# TODO(aminasyan): mark fails before skipping. doing todo not to lose the mark
# pytestmark = pytest.mark.requires('dvr')


@pytest.mark.requires("computes_count >= 2")
@pytest.mark.idempotent_id(
    '91853195-c456-464c-b0a4-5655acee7769',
    router=dict(distributed=True),
    neutron_2_servers_different_networks='same_host')
@pytest.mark.idempotent_id(
    '8dd82992-136b-4a46-b399-74a12bb16613',
    router=dict(distributed=True),
    neutron_2_servers_different_networks='different_hosts')
@pytest.mark.idempotent_id(
    '808b1d0c-e492-4a26-97b3-758c0baace80',
    router=dict(distributed=False),
    neutron_2_servers_different_networks='different_hosts')
@pytest.mark.parametrize(
    'router, neutron_2_servers_different_networks',
    [(dict(distributed=True), 'same_host'),
     (dict(distributed=True), 'different_hosts'),
     (dict(distributed=False), 'different_hosts')],
    ids=['distributed router, same host',
         'distributed router, different hosts',
         'centralized router, different hosts'],
    indirect=True)
def test_check_east_west_connectivity_between_instances(
        neutron_2_servers_different_networks,
        floating_ip,
        server_steps):
    """**Scenario:** Check east-west connectivity between instances.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network_1 with subnet_1 and DVR
    #. Create server_1
    #. Create network_2 with subnet_2
    #. Add network_2 interface to router
    #. Create server_2 and connect it to network_2

    **Steps:**

    #. Assign floating ip to server_1
    #. Check that ping from server_1 to server_2 is successful

    **Teardown:**

    #. Delete servers
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnets
    #. Delete networks
    """
    server_1, server_2 = neutron_2_servers_different_networks.servers

    server_steps.attach_floating_ip(server_1, floating_ip)
    server_2_ip = server_steps.get_fixed_ip(server_2)
    with server_steps.get_server_ssh(server_1) as server_1_ssh:
        server_steps.check_ping_for_ip(
            server_2_ip,
            server_1_ssh,
            timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)


@pytest.mark.requires("computes_count >= 2")
@pytest.mark.idempotent_id('820fa7c3-4e6d-43e7-9d61-2bbc4a09c699',
                           router=dict(distributed=True))
@pytest.mark.idempotent_id('578d0cf2-8db6-424b-a9a5-7bdfa8bfa37d',
                           router=dict(distributed=False))
@pytest.mark.parametrize('router',
                         [dict(distributed=True), dict(distributed=False)],
                         ids=['distributed', 'centralized'], indirect=True)
def test_check_connectivity_to_north_south_routing(server,
                                                   floating_ip,
                                                   server_steps):
    """**Scenario:** Check connectivity to North-South-Routing.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Assign floating ip to server
    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    server_steps.attach_floating_ip(server, floating_ip)

    with server_steps.get_server_ssh(server) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)


@pytest.mark.idempotent_id(
    'f3848003-ff36-4f87-899d-de6d3a321b65', router=dict(distributed=False))
@pytest.mark.idempotent_id(
    '885ad794-442a-4b11-9683-4cb0e40470ec', router=dict(distributed=True))
@pytest.mark.parametrize(
    'router', [dict(distributed=False), dict(distributed=True)],
    ids=['centralized router', 'distributed router'], indirect=True)
def test_north_south_connectivity_without_floating(
        server,
        get_ssh_proxy_cmd,
        server_steps):
    """**Scenario:** Check connectivity to North-South-Routing.

    This test checks connectivity to North-South-Routing in case of
        centralized of distributed router without floating ip assigning.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    proxy_cmd = get_ssh_proxy_cmd(server)

    with server_steps.get_server_ssh(
            server, proxy_cmd=proxy_cmd) as server_ssh:
        server_steps.check_ping_for_ip(config.GOOGLE_DNS_IP, server_ssh,
                                       timeout=config.PING_CALL_TIMEOUT)


@pytest.mark.idempotent_id('bbc32bc5-d3ed-4e25-a957-04288420dc54')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
def test_north_south_connectivity_after_ban_clear_l3_on_compute(
        server,
        floating_ip,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check North-South connectivity after ban/clear l3 agent.

    This test checks connectivity to North-South-Routing after ban and clear
        L3 agent on compute.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Assign floating ip to server
    #. Check that ping from server to 8.8.8.8 is successful
    #. Terminate L3 service on compute with server
    #. Start L3 service on compute with server
    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    server_steps.attach_floating_ip(server, floating_ip)

    with server_steps.get_server_ssh(server) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)

    compute_host = getattr(server, config.SERVER_ATTR_HOST)
    compute_fqdn = os_faults_steps.get_fqdn_by_host_name(compute_host)
    compute_node = os_faults_steps.get_node(fqdns=[compute_fqdn])
    os_faults_steps.terminate_service(config.NEUTRON_L3_SERVICE, compute_node)
    os_faults_steps.start_service(config.NEUTRON_L3_SERVICE, compute_node)

    with server_steps.get_server_ssh(server) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)


@pytest.mark.idempotent_id('1c803f4b-a47c-44c2-b321-5d53919390cb4')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
# TODO(akholkin): mark fails before skipping. doing todo not to lose the mark
# @pytest.mark.destructive
def test_north_south_connectivity_after_primary_controller_reset(
        net_subnet_router,
        server,
        get_ssh_proxy_cmd,
        agent_steps,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check North-South after reset primary controller.

    This test checks connectivity to North-South-Routing without floating
        after reset of primary controller with SNAT.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Check that ping from server to 8.8.8.8 is successful
    #. Find controller with SNAT for router
    #. Reschedule router if controller with SNAT is not primary controller
    #. Reset primary controller
    #. Wait for another L3 agent becomes ACTIVE
    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    _, _, router = net_subnet_router

    proxy_cmd = get_ssh_proxy_cmd(server)
    with server_steps.get_server_ssh(
            server, proxy_cmd=proxy_cmd) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)

    primary_controller = os_faults_steps.get_nodes_by_cmd(
        config.FUEL_PRIMARY_CONTROLLER_CMD)
    primary_controller_agent = agent_steps.get_agents(
        binary=config.NEUTRON_L3_SERVICE,
        host=primary_controller.hosts[0].fqdn)[0]

    agent_steps.reschedule_router_to_l3_agent(
        primary_controller_agent,
        router,
        timeout=config.AGENT_RESCHEDULING_TIMEOUT)

    os_faults_steps.reset_nodes(primary_controller)

    agent_steps.check_router_rescheduled(
        router=router,
        old_l3_agent=primary_controller_agent,
        timeout=config.AGENT_RESCHEDULING_TIMEOUT)

    proxy_cmd = get_ssh_proxy_cmd(server)
    with server_steps.get_server_ssh(
            server, proxy_cmd=proxy_cmd) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)


@pytest.mark.idempotent_id('32002b62-6d83-4d1b-9881-21eea7d38f56')
@pytest.mark.requires("l3_agent_nodes_with_snat_count >= 2")
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
def test_reschedule_router_from_snat_controller(
        net_subnet_router,
        server,
        floating_ip,
        agent_steps,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check manually reschedule router from SNAT controller.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Assign floating ip to server
    #. Find controller with SNAT for router
    #. Reschedule router to another controller
    #. Wait for another L3 agent becomes ACTIVE
    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    _, _, router = net_subnet_router
    server_steps.attach_floating_ip(server, floating_ip)

    current_agent = agent_steps.get_l3_agents_for_router(router)[0]
    current_agent_node = os_faults_steps.get_nodes_for_agents([current_agent])

    l3_agents_nodes = os_faults_steps.get_nodes(
        service_names=[config.NEUTRON_L3_SERVICE, config.NOVA_API])
    free_agents_nodes = l3_agents_nodes - current_agent_node
    new_agent = agent_steps.get_agents(binary=config.NEUTRON_L3_SERVICE,
                                       host=free_agents_nodes.hosts[0].fqdn)[0]

    agent_steps.remove_router_from_l3_agent(
        current_agent, router, timeout=config.AGENT_RESCHEDULING_TIMEOUT)
    agent_steps.add_router_to_l3_agent(
        new_agent, router, timeout=config.AGENT_RESCHEDULING_TIMEOUT)
    agent_steps.check_router_rescheduled(
        router=router,
        old_l3_agent=current_agent,
        timeout=config.AGENT_RESCHEDULING_TIMEOUT)
    agent_steps.check_alive(agents=[new_agent],
                            timeout=config.NEUTRON_AGENT_ALIVE_TIMEOUT)

    with server_steps.get_server_ssh(server) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)


# TODO(akholkin): mark fails before skipping. doing todo not to lose the mark
# @pytest.mark.destructive
@pytest.mark.idempotent_id('4dda8b1f-bbad-46d5-8dfa-2dbdc7a526b3')
@pytest.mark.requires("l3_agent_nodes_with_snat_count >= 2")
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
def test_shutdown_controller_with_snat(
        net_subnet_router,
        server,
        floating_ip,
        agent_steps,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check reschedule router after shutdown controller.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Assign floating ip to server
    #. Find controller with SNAT for router
    #. Destroy controller
    #. Wait for SNAT reschedule to another controller
    #. Wait for L3 agent becomes ACTIVE
    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    _, _, router = net_subnet_router
    server_steps.attach_floating_ip(server, floating_ip)

    l3_agent = agent_steps.get_l3_agents_for_router(router)[0]
    l3_agent_node = os_faults_steps.get_nodes_for_agents([l3_agent])

    os_faults_steps.poweroff_nodes(l3_agent_node)
    agent_steps.check_router_rescheduled(
        router=router,
        old_l3_agent=l3_agent,
        timeout=config.AGENT_RESCHEDULING_TIMEOUT)
    new_l3_agent = agent_steps.get_l3_agents_for_router(router)[0]
    agent_steps.check_alive(agents=[new_l3_agent],
                            timeout=config.NEUTRON_AGENT_ALIVE_TIMEOUT)

    with server_steps.get_server_ssh(server) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)


# TODO(akholkin): mark fails before skipping. doing todo not to lose the mark
# @pytest.mark.destructive
@pytest.mark.idempotent_id('08192558-e632-410f-bded-9d124dcce52c')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
def test_north_south_connectivity_after_reset_compute(
        server,
        floating_ip,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check North-South connectivity after reset compute.

    This test checks connectivity to North-South-Routing reset of compute
       where vm hosted.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Assign floating ip to server
    #. Check that ping from server to 8.8.8.8 is successful
    #. Destroy compute with server
    #. Start compute with server
    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    server_steps.attach_floating_ip(server, floating_ip)

    with server_steps.get_server_ssh(server) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)

    compute_host = getattr(server, config.SERVER_ATTR_HOST)
    compute_fqdn = os_faults_steps.get_fqdn_by_host_name(compute_host)
    compute_node = os_faults_steps.get_node(fqdns=[compute_fqdn])
    os_faults_steps.reset_nodes(compute_node, native=False)

    with server_steps.get_server_ssh(server) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)


@pytest.mark.idempotent_id('db7e0ff4-d76c-469e-82a1-478c1c0b9a8f')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
@pytest.mark.parametrize('neutron_2_servers_different_networks',
                         ['different_hosts'], indirect=True)
def test_east_west_connectivity_after_ban_clear_l3_on_compute(
        neutron_2_servers_different_networks,
        get_ssh_proxy_cmd,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check east-west connectivity after ban/clear l3 agent.

    This test checks east-west connectivity between instances on different
        computes after ban and clear l3 agent on one of them.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network_1 with subnet_1 and DVR
    #. Create server_1
    #. Create network_2 with subnet_2
    #. Add network_2 interface to router
    #. Create server_2 and connect it to network_2

    **Steps:**

    #. Terminate l3-service on the compute with server_1
    #. Start l3-service on the compute with server_1
    #. Check that ping from server_1 to server_2 by internal ip is successful

    **Teardown:**

    #. Delete servers
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnets
    #. Delete networks
    """
    server_1, server_2 = neutron_2_servers_different_networks.servers

    compute_host = getattr(server_1, config.SERVER_ATTR_HOST)
    compute_fqdn = os_faults_steps.get_fqdn_by_host_name(compute_host)
    compute_node = os_faults_steps.get_node(fqdns=[compute_fqdn])
    os_faults_steps.terminate_service(config.NEUTRON_L3_SERVICE, compute_node)
    os_faults_steps.start_service(config.NEUTRON_L3_SERVICE, compute_node)

    proxy_cmd = get_ssh_proxy_cmd(server_1)
    server_2_ip = server_steps.get_fixed_ip(server_2)
    with server_steps.get_server_ssh(
            server_1, proxy_cmd=proxy_cmd) as server_1_ssh:
        server_steps.check_ping_for_ip(
            server_2_ip,
            server_1_ssh,
            timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)


# TODO(akholkin): mark fails before skipping. doing todo not to lose the mark
# @pytest.mark.destructive
@pytest.mark.requires("computes_count >=2")
@pytest.mark.idempotent_id('c3c5d5ef-00b9-4054-8ac0-3605abfa7d23')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
@pytest.mark.parametrize('neutron_2_servers_different_networks',
                         ['different_hosts'], indirect=True)
def test_east_west_connectivity_after_reset_computes(
        neutron_2_servers_different_networks,
        get_ssh_proxy_cmd,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check east-west connectivity after reset computes.

    This test checks east-west connectivity between instances on different
        hosts after reset of computes.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network_1 with subnet_1 and DVR
    #. Create server_1
    #. Create network_2 with subnet_2
    #. Add network_2 interface to router
    #. Create server_2 and connect it to network_2

    **Steps:**

    #. Check that ping from server_1 to server_2 by internal ip is successful
    #. Destroy computes where servers are hosted
    #. Start computes where servers are hosted
    #. Check that ping from server_2 to server_1 by internal ip is successful

    **Teardown:**

    #. Delete servers
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnets
    #. Delete networks
    """
    server_1, server_2 = neutron_2_servers_different_networks.servers

    proxy_cmd = get_ssh_proxy_cmd(server_1)
    server_2_ip = server_steps.get_fixed_ip(server_2)
    with server_steps.get_server_ssh(
            server_1, proxy_cmd=proxy_cmd) as server_1_ssh:
        server_steps.check_ping_for_ip(
            server_2_ip,
            server_1_ssh,
            timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)

    # Do nothing some time before computes resetting
    time.sleep(60)

    compute_host_1 = getattr(server_1, config.SERVER_ATTR_HOST)
    compute_fqdn_1 = os_faults_steps.get_fqdn_by_host_name(compute_host_1)
    compute_host_2 = getattr(server_2, config.SERVER_ATTR_HOST)
    compute_fqdn_2 = os_faults_steps.get_fqdn_by_host_name(compute_host_2)
    computes = os_faults_steps.get_nodes(fqdns=[compute_fqdn_1,
                                                compute_fqdn_2])
    os_faults_steps.reset_nodes(computes, native=False)

    proxy_cmd = get_ssh_proxy_cmd(server_2)
    server_1_ip = server_steps.get_fixed_ip(server_1)
    with server_steps.get_server_ssh(
            server_2, proxy_cmd=proxy_cmd) as server_2_ssh:
        server_steps.check_ping_for_ip(
            server_1_ip,
            server_2_ssh,
            timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)


# TODO(akholkin): mark fails before skipping. doing todo not to lose the mark
# @pytest.mark.destructive
@pytest.mark.requires("computes_count >=2 and controllers_count >=2")
@pytest.mark.idempotent_id('99f40662-2f62-4b75-bf82-52f3f0180558')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
@pytest.mark.parametrize('neutron_2_servers_different_networks',
                         ['different_hosts'], indirect=True)
def test_east_west_connectivity_after_destroy_controller(
        neutron_2_servers_different_networks,
        get_ssh_proxy_cmd,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check east-west connectivity after destroy controller.

    This test checks east-west connectivity between instances on different
        hosts after destroy of controller.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network_1 with subnet_1 and DVR
    #. Create server_1
    #. Create network_2 with subnet_2
    #. Add network_2 interface to router
    #. Create server_2 and connect it to network_2

    **Steps:**

    #. Check that ping from server_1 to server_2 by internal ip is successful
    #. Destroy any controller
    #. Check that ping from server_2 to server_1 by internal ip is successful

    **Teardown:**

    #. Delete servers
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnets
    #. Delete networks
    """
    server_1, server_2 = neutron_2_servers_different_networks.servers

    proxy_cmd = get_ssh_proxy_cmd(server_1)
    server_2_ip = server_steps.get_fixed_ip(server_2)
    with server_steps.get_server_ssh(
            server_1, proxy_cmd=proxy_cmd) as server_1_ssh:
        server_steps.check_ping_for_ip(
            server_2_ip,
            server_1_ssh,
            timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)

    controller = os_faults_steps.get_node(service_names=[config.NOVA_API])
    os_faults_steps.poweroff_nodes(controller)

    proxy_cmd = get_ssh_proxy_cmd(server_2)
    server_1_ip = server_steps.get_fixed_ip(server_1)
    with server_steps.get_server_ssh(
            server_2, proxy_cmd=proxy_cmd) as server_2_ssh:
        server_steps.check_ping_for_ip(
            server_1_ip,
            server_2_ssh,
            timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)


@pytest.mark.idempotent_id('8aaa9951-57c0-4690-bbab-cd649633bed8')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
def test_associate_floating_ip_after_restart_l3_on_compute(
        cirros_image,
        flavor,
        security_group,
        net_subnet_router,
        server,
        floating_ip,
        create_floating_ip,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check floating ip association after restart l3 agent.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Assign floating ip to server
    #. Check that ping from server to 8.8.8.8 is successful
    #. Restart L3 service on compute with server
    #. Boot server_2 on the compute where the l3-agent has been restarted
    #. Assign floating ip to server_2
    #. Check pings between server and server_2 via floating ip

    **Teardown:**

    #. Delete servers
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    server_steps.attach_floating_ip(server, floating_ip)

    with server_steps.get_server_ssh(server) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)

    compute_host = getattr(server, config.SERVER_ATTR_HOST)
    compute_fqdn = os_faults_steps.get_fqdn_by_host_name(compute_host)
    compute_node = os_faults_steps.get_node(fqdns=[compute_fqdn])

    os_faults_steps.restart_services(names=[config.NEUTRON_L3_SERVICE],
                                     nodes=compute_node)

    network, _, _ = net_subnet_router
    server_2 = server_steps.create_servers(
        image=cirros_image, flavor=flavor, networks=[network],
        security_groups=[security_group],
        availability_zone='nova:{}'.format(compute_host),
        username=config.CIRROS_USERNAME,
        password=config.CIRROS_PASSWORD)[0]

    floating_ip_2 = create_floating_ip()
    server_steps.attach_floating_ip(server_2, floating_ip_2)
    server_steps.check_ping_between_servers_via_floating(
        servers=[server, server_2],
        ip_types=(config.FLOATING_IP,),
        timeout=config.PING_BETWEEN_SERVERS_TIMEOUT)


@pytest.mark.idempotent_id('d2682741-b7f5-4aec-b6d8-2642ca0ec701')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
def test_check_router_namespace_on_compute_node(
        net_subnet_router,
        server,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check router namespace with server and without it.

    This test check router namespace on compute node with server and after
        server deletion.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Check that router namespace is on compute node where server is hosted
    #. Delete server
    #. Check that router namespace is deleted

    **Teardown:**

    #. Delete server (if it was not removed)
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    _, _, router = net_subnet_router
    compute_host = getattr(server, config.SERVER_ATTR_HOST)
    compute_fqdn = os_faults_steps.get_fqdn_by_host_name(compute_host)
    compute_node = os_faults_steps.get_node(fqdns=[compute_fqdn])

    os_faults_steps.check_router_namespace_presence(router, compute_node)

    server_steps.delete_servers([server])
    os_faults_steps.check_router_namespace_presence(
        router,
        compute_node,
        must_present=False,
        timeout=config.ROUTER_NAMESPACE_TIMEOUT)


@pytest.mark.requires("l3_agent_nodes_with_snat_count >= 2")
# TODO(akholkin): mark fails before skipping. doing todo not to lose the mark
# @pytest.mark.destructive
@pytest.mark.idempotent_id('0bfc9465-a29b-47b2-9c59-382fae7e086e', ban_count=1)
@pytest.mark.idempotent_id('48bf701f-7bd9-474c-b19c-1192702be9b0', ban_count=2)
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
@pytest.mark.parametrize('ban_count', [1, 2])
def test_check_ban_l3_agent_on_node_with_snat(
        net_subnet_router,
        server,
        get_ssh_proxy_cmd,
        agent_steps,
        os_faults_steps,
        server_steps,
        ban_count):
    """**Scenario:** Check North-South after ban L3 agent on node with SNAT.

    This test checks North-South connectivity without floating after ban L3
        agent on node with SNAT.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Check that ping from server to 8.8.8.8 is successful
    #. Find node with SNAT for router and ban L3 agent on it
    #. Wait for another L3 agent becomes ACTIVE
    #. Repeat last 2 steps ``ban_count`` times
    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    net, subnet, router = net_subnet_router

    proxy_cmd = get_ssh_proxy_cmd(server)
    with server_steps.get_server_ssh(
            server, proxy_cmd=proxy_cmd) as server_ssh:
        server_steps.check_ping_for_ip(config.GOOGLE_DNS_IP, server_ssh,
                                       timeout=config.PING_CALL_TIMEOUT)

    for _ in range(ban_count):
        agent = agent_steps.get_l3_agents_for_router(router)[0]
        agent_node = os_faults_steps.get_nodes_for_agents([agent])
        os_faults_steps.terminate_service(
            config.NEUTRON_L3_SERVICE, nodes=agent_node)
        agent_steps.check_router_rescheduled(
            router=router,
            old_l3_agent=agent,
            timeout=config.AGENT_RESCHEDULING_TIMEOUT)

    with server_steps.get_server_ssh(
            server, proxy_cmd=proxy_cmd) as server_ssh:
        server_steps.check_ping_for_ip(config.GOOGLE_DNS_IP, server_ssh,
                                       timeout=config.PING_CALL_TIMEOUT)


@pytest.mark.requires("l3_agent_nodes_with_snat_count >= 2")
# TODO(akholkin): mark fails before skipping. doing todo not to lose the mark
# @pytest.mark.destructive
@pytest.mark.idempotent_id('4750b7b5-a4b9-4a15-9131-6f017315ee24',
                           agent_number=0)
@pytest.mark.idempotent_id('1555fc92-0f06-4a64-a44f-78c7725c46b1',
                           agent_number=-1)
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
@pytest.mark.parametrize('agent_number', [0, -1], ids=['first', 'last'])
def test_check_ban_l3_agents_and_clear_one(
        net_subnet_router,
        server,
        get_ssh_proxy_cmd,
        agent_steps,
        os_faults_steps,
        server_steps,
        agent_number):
    """**Scenario:** Check North-South after ban L3 agent on node with SNAT.

    This test checks North-South connectivity without floating after ban all
        L3 agents on nodes with SNAT and clear the first/last one.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Check that ping from server to 8.8.8.8 is successful
    #. Find node with snat for router and ban L3 agent on it
    #. Wait for another L3 agent becomes ACTIVE
    #. Repeat last 2 steps while no L3 agents will be ACTIVE
    #. Clear the first/last banned L3 agent
    #. Wait for L3 agent becomes ACTIVE
    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    banned_agents = []
    net, subnet, router = net_subnet_router

    proxy_cmd = get_ssh_proxy_cmd(server)
    with server_steps.get_server_ssh(
            server, proxy_cmd=proxy_cmd) as server_ssh:
        server_steps.check_ping_for_ip(config.GOOGLE_DNS_IP, server_ssh,
                                       timeout=config.PING_CALL_TIMEOUT)

    l3_agents_count = len(os_faults_steps.get_nodes(
        service_names=[config.NEUTRON_L3_SERVICE, config.NOVA_API]))
    for _ in range(l3_agents_count - 1):
        l3_agent = agent_steps.get_l3_agents_for_router(router)[0]
        nodes_with_l3 = os_faults_steps.get_nodes_for_agents([l3_agent])
        os_faults_steps.terminate_service(config.NEUTRON_L3_SERVICE,
                                          nodes=nodes_with_l3)
        agent_steps.check_alive([l3_agent],
                                must_alive=False,
                                timeout=config.NEUTRON_AGENT_ALIVE_TIMEOUT)
        agent_steps.check_router_rescheduled(
            router=router,
            old_l3_agent=l3_agent,
            timeout=config.AGENT_RESCHEDULING_TIMEOUT)
        banned_agents.append(l3_agent)

    l3_agent = agent_steps.get_l3_agents_for_router(router)[0]
    last_node_with_l3 = os_faults_steps.get_nodes_for_agents([l3_agent])
    os_faults_steps.terminate_service(service_name=config.NEUTRON_L3_SERVICE,
                                      nodes=last_node_with_l3)
    agent_steps.check_alive(agents=[l3_agent],
                            must_alive=False,
                            timeout=config.NEUTRON_AGENT_ALIVE_TIMEOUT)
    banned_agents.append(l3_agent)

    agent_to_clear = banned_agents[agent_number]
    nodes_with_l3 = os_faults_steps.get_nodes_for_agents([agent_to_clear])
    os_faults_steps.start_service(config.NEUTRON_L3_SERVICE, nodes_with_l3)
    agent_steps.check_alive([agent_to_clear],
                            timeout=config.NEUTRON_AGENT_ALIVE_TIMEOUT)

    with server_steps.get_server_ssh(
            server, proxy_cmd=proxy_cmd) as server_ssh:
        server_steps.check_ping_for_ip(config.GOOGLE_DNS_IP, server_ssh,
                                       timeout=config.PING_CALL_TIMEOUT)


@pytest.mark.idempotent_id('149fad6f-a0c9-4434-a7d0-22902399851e')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
def test_update_router_from_distributed_to_centralized(router, router_steps):
    """**Scenario:** Check update router type from distributed to centralized.

    This test checks that it's not possible to update distributed router to
        centralized.

    **Setup:**

    #. Create distributed router

    **Steps:**

    #. Try to update router type to centralized and check that BadRequest with
        correct exception message occurs

    **Teardown:**

    #. Delete router
    """
    router_steps.check_router_type_not_changed_to_centralized(router)


@pytest.mark.idempotent_id('25e2f9f0-5e3d-439a-94d9-14b7bfec6171')
@pytest.mark.parametrize('router', [dict(distributed=False)], indirect=True)
def test_update_router_from_centralized_to_distributed(
        net_subnet_router,
        server,
        floating_ip,
        os_faults_steps,
        router_steps,
        server_steps):
    """**Scenario:** Check update router type from centralized to distributed.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and centralized router.
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Assign floating ip to server
    #. Try to update router type to distributed while router is in active state
        and check that BadRequest with correct exception message occurs
    #. Set admin state for router to down
    #. Update router type to distributed
    #. Set admin state for router to up
    #. Check that namespace for router appeared on compute with server
    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    _, _, router = net_subnet_router
    server_steps.attach_floating_ip(server, floating_ip)

    router_steps.check_type_unchangeable_for_active_router(router)

    router_steps.update_router(router, admin_state_up=False)
    router_steps.update_router(router, distributed=True)
    router_steps.update_router(router, admin_state_up=True)

    compute_host = getattr(server, config.SERVER_ATTR_HOST)
    compute_fqdn = os_faults_steps.get_fqdn_by_host_name(compute_host)
    compute_node = os_faults_steps.get_node(fqdns=[compute_fqdn])

    os_faults_steps.check_router_namespace_presence(
        router, compute_node, timeout=config.ROUTER_NAMESPACE_TIMEOUT)

    with server_steps.get_server_ssh(server) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)


# TODO(akholkin): mark fails before skipping. doing todo not to lose the mark
# @pytest.mark.destructive
@pytest.mark.idempotent_id('4a9012bd-6fbb-43e2-b38c-c7825d03cd80')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
def test_connectivity_after_ban_l3_agent_many_times(
        net_subnet_router,
        server,
        get_ssh_proxy_cmd,
        agent_steps,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check North-South after ban/clear L3 agent on controller.

    This test checks North-South connectivity without floating IP after ban and
        clear L3 agent on controller with SNAT many times.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and centralized router.
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Check that ping from server to 8.8.8.8 is successful
    #. Find node with SNAT for router
    #. Ban all L3 agents on other controller
    #. Ban and clear L3 agent on controller with snat 40 times
    #. Wait for L3 agent becomes ACTIVE
    #. Check that ping from server to 8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    _, _, router = net_subnet_router

    proxy_cmd = get_ssh_proxy_cmd(server)
    with server_steps.get_server_ssh(
            server, proxy_cmd=proxy_cmd) as server_ssh:
        server_steps.check_ping_for_ip(config.GOOGLE_DNS_IP, server_ssh,
                                       timeout=config.PING_CALL_TIMEOUT)

    l3_agent = agent_steps.get_l3_agents_for_router(router)[0]
    current_l3_agent_node = os_faults_steps.get_nodes_for_agents([l3_agent])

    l3_agents_nodes = os_faults_steps.get_nodes(
        service_names=[config.NEUTRON_L3_SERVICE, config.NOVA_API])
    other_l3_agents_nodes = l3_agents_nodes - current_l3_agent_node
    os_faults_steps.terminate_service(service_name=config.NEUTRON_L3_SERVICE,
                                      nodes=other_l3_agents_nodes)

    for _ in range(40):
        os_faults_steps.terminate_service(
            service_name=config.NEUTRON_L3_SERVICE,
            nodes=current_l3_agent_node)
        os_faults_steps.start_service(
            service_name=config.NEUTRON_L3_SERVICE,
            nodes=current_l3_agent_node)

    agent_steps.check_alive(
        agents=[l3_agent], timeout=config.NEUTRON_AGENT_ALIVE_TIMEOUT)
    with server_steps.get_server_ssh(
            server, proxy_cmd=proxy_cmd) as server_ssh:
        server_steps.check_ping_for_ip(config.GOOGLE_DNS_IP, server_ssh,
                                       timeout=config.PING_CALL_TIMEOUT)


@pytest.mark.idempotent_id('802b2be3-70b2-460a-9ef1-1c7a8cb679c8')
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
# TODO(akholkin): mark fails before skipping. doing todo not to lose the mark
# @pytest.mark.destructive
def test_north_south_floating_ip_shut_down_br_ex_on_controllers(
        server,
        floating_ip,
        os_faults_steps,
        server_steps):
    """**Scenario:** Check North-South connectivity after shut-downing br-ex.

    This test checks North-South connectivity with floating IP after
        shut-downing br-ex on all controllers.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router
    #. Create server

    **Steps:**

    #. Assign floating ip to server
    #. Check that ping from server to 8.8.8.8 is successful
    #. Shut down br-ex on all controllers
    #. Connect to server using floating IP and check that ping from server to
        8.8.8.8 is successful

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    server_steps.attach_floating_ip(server, floating_ip)
    server_credentials = server_steps.get_server_credentials(server)

    with server_steps.get_server_ssh(server) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)

    nodes = os_faults_steps.get_nodes(service_names=[config.NOVA_API])
    os_faults_steps.execute_cmd(nodes=nodes, cmd=config.SHUTDOWN_BR_EX_CMD)

    with server_steps.get_server_ssh(
            server,
            ip=floating_ip['floating_ip_address'],
            credentials=server_credentials) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)


@pytest.mark.requires("neutron_debug and computes_count >= 2")
@pytest.mark.parametrize('router', [dict(distributed=True)], indirect=True)
@pytest.mark.idempotent_id('f3ec53bb-63f9-4344-96a5-c9f7030d2519')
def test_check_router_update_notification_for_l3_agents(
        cirros_image,
        flavor,
        security_group,
        net_subnet_router,
        floating_ip,
        server_steps,
        host_steps,
        os_faults_steps):
    """**Scenario:** Check router update notifications for L3 agent.

    This test checks that router update notification appear in log of L3 agent
    after server creation and assigning/deleting floating ip but only in log on
    compute node where server is hosted.

    **Setup:**

    #. Create cirros image
    #. Create flavor
    #. Create security group
    #. Create network with subnet and DVR
    #. Add network interface to router

    **Steps:**

    #. Get current sizes of log files of L3 agent on all computes
    #. Create server
    #. Assign floating ip to server
    #. Delete floating ip from server
    #. Check that 3 notifications have appeared in log of L3 agent on compute
        with server
    #. Check that no notifications have appeared in log of L3 agent on other
        computes

    **Teardown:**

    #. Delete server
    #. Delete cirros image
    #. Delete security group
    #. Delete flavor
    #. Delete router
    #. Delete subnet
    #. Delete network
    """
    nodes = os_faults_steps.get_nodes(
        service_names=[config.NOVA_COMPUTE, config.NEUTRON_L3_SERVICE])
    server_host_fqdn = next(host.fqdn for host in nodes.hosts)

    log_file = config.AGENT_LOGS[config.NEUTRON_L3_SERVICE][1]

    line_count_file_path = os_faults_steps.store_file_line_count(nodes,
                                                                 log_file)

    network = net_subnet_router[0]
    server_host_name = host_steps.get_host(fqdn=server_host_fqdn).host_name
    server = server_steps.create_servers(
        image=cirros_image,
        flavor=flavor,
        networks=[network],
        security_groups=[security_group],
        availability_zone='nova:' + server_host_name,
        username=config.CIRROS_USERNAME)[0]

    server_steps.attach_floating_ip(server, floating_ip)
    server_steps.detach_floating_ip(server, floating_ip)

    server_node = os_faults_steps.get_node(fqdns=[server_host_fqdn])
    os_faults_steps.check_string_in_file(
        server_node, file_name=log_file,
        keyword=config.STR_L3_AGENT_NOTIFICATION,
        start_line_number_file=line_count_file_path,
        expected_count=3)

    os_faults_steps.check_string_in_file(
        nodes - server_node, file_name=log_file,
        keyword=config.STR_L3_AGENT_NOTIFICATION,
        start_line_number_file=line_count_file_path,
        must_present=False)


@pytest.mark.idempotent_id('11703a9c-2620-49c7-b834-0bffbed975d6')
@pytest.mark.parametrize('flavor', [dict(ram=64, disk=1)], indirect=True)
@pytest.mark.parametrize(
    'change_neutron_quota', [dict(
        network=50, router=50, subnet=50, port=200)],
    indirect=True)
@pytest.mark.usefixtures('change_neutron_quota')
def test_instance_connectivity_after_l3_agent_restart(
        cirros_image,
        flavor,
        security_group,
        public_network,
        create_network,
        create_subnet,
        create_router,
        create_floating_ip,
        router_steps,
        server_steps,
        hypervisor_steps,
        host_steps,
        os_faults_steps,
        agent_steps):
    """**Scenario:** Check instances connectivity after restarting l3 agent.

    **Setup:**

    #. Increase neutron quotas
    #. Create cirros image
    #. Create security group

    **Steps:**

    #. Create 10 networks, subnets and routers
    #. Create 10 servers on one compute
    #. For each server, create floating ip and attach it to server
    #. Check that ping from one server to 8.8.8.8 is successful
    #. Restart L3 agent on compute 60 times
    #. Check that ping from all servers to 8.8.8.8 are successful

    **Teardown:**

    #. Delete servers
    #. Delete floating IPs
    #. Delete networks, subnets, routers
    #. Delete security group
    #. Delete cirros image
    #. Restore original neutron quotas
    """
    servers = []
    host_fqdn = hypervisor_steps.get_hypervisors()[0].hypervisor_hostname
    host_name = host_steps.get_host(fqdn=host_fqdn).host_name

    for _ in range(10):

        network = create_network(next(utils.generate_ids()))
        subnet = create_subnet(
            subnet_name=next(utils.generate_ids()),
            network=network,
            cidr=config.LOCAL_CIDR)
        router = create_router(next(utils.generate_ids()), distributed=True)
        router_steps.set_gateway(router, public_network)
        router_steps.add_subnet_interface(router, subnet)

        server = server_steps.create_servers(
            image=cirros_image,
            flavor=flavor,
            networks=[network],
            security_groups=[security_group],
            availability_zone='nova:' + host_name,
            username=config.CIRROS_USERNAME,
            password=config.CIRROS_PASSWORD)[0]

        floating_ip = create_floating_ip()
        server_steps.attach_floating_ip(server, floating_ip)

        servers.append(server)

    with server_steps.get_server_ssh(servers[0]) as server_ssh:
        server_steps.check_ping_for_ip(
            config.GOOGLE_DNS_IP, server_ssh,
            timeout=config.PING_CALL_TIMEOUT)

    node = os_faults_steps.get_node(fqdns=[host_fqdn])
    for _ in range(60):
        os_faults_steps.restart_services(names=[config.NEUTRON_L3_SERVICE],
                                         nodes=node)

    l3_agent = next(
        agent for agent in agent_steps.get_agents(node)
        if agent['binary'] == config.NEUTRON_L3_SERVICE)
    agent_steps.check_alive(
        [l3_agent], timeout=config.NEUTRON_AGENT_ALIVE_TIMEOUT)

    for server in servers:
        with server_steps.get_server_ssh(server) as server_ssh:
            server_steps.check_ping_for_ip(
                config.GOOGLE_DNS_IP, server_ssh,
                timeout=config.PING_CALL_TIMEOUT)


@pytest.mark.idempotent_id('849ce63d-6fe9-44ec-ad4a-d795c3fe0626')
def test_add_router_interface_with_port_id(create_router,
                                           port,
                                           router_steps,
                                           os_faults_steps):
    """**Scenario:** Add router interface with port_id parameter.

    This test checks that there are no error messages in logs when adding
    router interface with port_id parameter.

    **Setup:**

    #. Create network with subnet
    #. Create port

    **Steps:**

    #. Get current sizes of neutron log files on controllers
    #. Create router of distributed type
    #. Add port interface to router
    #. Wait for 30 seconds
    #. Check that message 'Could not retrieve gateway port for subnet'
        did not appear in log files

    **Teardown:**

    #. Delete port interface
    #. Delete port
    #. Delete router
    #. Delete subnet and network
    """
    nodes = os_faults_steps.get_nodes(
        service_names=[config.NEUTRON_SERVER_SERVICE])

    log_file = config.AGENT_LOGS[config.NEUTRON_SERVER_SERVICE][0]

    line_count_file_path = os_faults_steps.store_file_line_count(nodes,
                                                                 log_file)

    router_name = next(utils.generate_ids())
    router = create_router(router_name, distributed=True)
    router_steps.add_port_interface(router, port)

    time.sleep(config.ERROR_GATEWAY_PORT_CHECK_TIME)

    os_faults_steps.check_string_in_file(
        nodes, file_name=log_file,
        keyword=config.STR_ERROR_GATEWAY_PORT,
        start_line_number_file=line_count_file_path,
        must_present=False)
