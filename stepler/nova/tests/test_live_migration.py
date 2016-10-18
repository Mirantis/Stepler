"""
-------------------------
Nova live migration tests
-------------------------
"""
#    Copyright 2016 Mirantis, Inc.
#
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

from stepler import config
from stepler.third_party.utils import generate_ids

USERDATA_DONE_MARKER = next(generate_ids('userdata-done'))

INSTALL_WORKLOAD_USERDATA = """#!/bin/bash -v
apt-get install -yq stress cpulimit sysstat iperf
echo {}""".format(USERDATA_DONE_MARKER)


def test_network_connectivity_to_vm_during_live_migration(
        keypair, flavor, security_group, nova_floating_ip, cirros_image,
        network, subnet, router, add_router_interfaces, create_volume,
        create_server, server_steps):
    """**Scenario:** Verify network connectivity to the VM during live
    migration.

    **Setup:**

        #. Upload cirros image
        #. Create network
        #. Create subnet
        #. Create router
        #. Set router default gateway to public network
        #. Create security group with allow ping rule
        #. Create flavor

    **Steps:**

        #. Add router interface to created network
        #. Boot server from cirros image
        #. Assign floating ip to server
        #. Start ping to server floating ip
        #. Migrate server to another hypervisor
        #. Stop ping
        #. Check that ping loss is not more than 20

    **Teardown:**

        #. Delete server
        #. Delete flavor
        #. Delete security group
        #. Delete router
        #. Delete subnet
        #. Delete network
        #. Delete cirros image
    """
    add_router_interfaces(router, [subnet])
    server_name = next(generate_ids('server'))
    server = create_server(
        server_name,
        image=cirros_image,
        keypair=keypair,
        flavor=flavor,
        networks=[network],
        security_groups=[security_group])
    server_steps.attach_floating_ip(server, nova_floating_ip)
    with server_steps.check_ping_loss_context(
            nova_floating_ip.ip, max_loss=20):
        server_steps.live_migrate(server, block_migration=True)


def test_migration_with_memory_workload(
        keypair, flavor, security_group, nova_floating_ip, ubuntu_image,
        network, subnet, router, add_router_interfaces, create_volume,
        create_server, server_steps):
    """**Scenario:** LM of instance under memory workload.

    **Setup:**

        #. Upload ubuntu image
        #. Create network
        #. Create subnet
        #. Create router
        #. Set router default gateway to public network
        #. Create security group with allow ping rule
        #. Create flavor

    **Steps:**

        #. Add router interface to created network
        #. Create volume from ubuntu image
        #. Boot server from volume
        #. Assign floating ip to server
        #. Start memory workload on server
        #. Migrate server to another hypervisor
        #. Check that ping to server's floating ip is successful

    **Teardown:**

        #. Delete server
        #. Delete flavor
        #. Delete volume
        #. Delete security group
        #. Delete router
        #. Delete subnet
        #. Delete network
        #. Delete ubuntu image
    """
    add_router_interfaces(router, [subnet])
    volume = create_volume(
        next(generate_ids('volume')), size=20, image=ubuntu_image)
    block_device_mapping = {'vda': volume.id}

    server_name = next(generate_ids('server'))
    server = create_server(
        server_name,
        image=None,
        flavor=flavor,
        keypair=keypair,
        networks=[network],
        security_groups=[security_group],
        block_device_mapping=block_device_mapping,
        userdata=INSTALL_WORKLOAD_USERDATA,
        username='ubuntu')
    server_steps.check_server_log_contains_record(
        server,
        USERDATA_DONE_MARKER,
        timeout=config.USERDATA_EXECUTING_TIMEOUT)
    server_steps.attach_floating_ip(server, nova_floating_ip)

    with server_steps.get_server_ssh(server,
                                     nova_floating_ip.ip) as server_ssh:
        server_steps.generate_server_memory_workload(server_ssh)

    server_steps.live_migrate(server, block_migration=True)
    server_steps.check_ping_to_server_floating(
        server, timeout=config.PING_CALL_TIMEOUT)
