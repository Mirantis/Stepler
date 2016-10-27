"""
-----------------------------
Nova basic verification tests
-----------------------------
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

import pytest
import random

from stepler import config
from stepler.third_party.utils import generate_ids


@pytest.mark.idempotent_id('')
def test_boot_instance_from_volume_bigger_than_flavor(
        flavor,
        security_group,
        nova_floating_ip,
        cirros_image,
        network,
        subnet,
        router,
        add_router_interfaces,
        create_volume,
        create_server,
        server_steps):
    """**Scenario:** Boot instance from volume bigger than flavor size.

    This test verify bug #1517671

    **Setup:**

        #. Upload cirros image
        #. Create network
        #. Create subnet
        #. Create router
        #. Create security group with allow ping rule
        #. Create flavor

    **Steps:**

        #. Set router default gateway to public network
        #. Add router interface to created network
        #. Create volume from cirros image with disk size bigger than flavor
        #. Boot server from volume
        #. Assign floating ip to server
        #. Check that ping to server's floating ip is successful

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
    volume_size = flavor.disk + 1
    volume = create_volume(
        next(generate_ids('volume')),
        size=volume_size,
        image=cirros_image)
    block_device_mapping = {'vda': volume.id}

    server_name = next(generate_ids('server'))
    server = create_server(server_name,
                           image=None,
                           flavor=flavor,
                           networks=[network],
                           security_groups=[security_group],
                           block_device_mapping=block_device_mapping)

    server_steps.attach_floating_ip(server, nova_floating_ip)
    server_steps.check_ping_to_server_floating(server, timeout=5 * 60)


@pytest.mark.idempotent_id('9a75e111-c9dc-44e3-88fb-d315ae2deacb')
def test_delete_server_with_precreated_port(
        flavor,
        network,
        port,
        cirros_image,
        create_port,
        port_steps,
        server_steps):
    """**Scenario:** Delete instance with pre-created port.

    This test verify bug #1486727

    **Setup:**

        #. Create flavor
        #. Create network
        #. Create subnet
        #. Upload cirros image
        #. Create port

    **Steps:**

        #. Boot server with created port
        #. Delete server
        #. Check that port is still present

    **Teardown:**

        #. Delete port
        #. Delete cirros image
        #. Delete network
        #. Delete subnet
        #. Delete flavor
    """
    server_name = next(generate_ids('server'))
    server = server_steps.create_server(server_name,
                                        image=cirros_image,
                                        flavor=flavor,
                                        ports=[port])
    server_steps.delete_server(server)
    port_steps.check_presence(port)


@pytest.mark.idempotent_id('d8a8d247-3150-491a-b9e5-2f20cb0f384d')
def test_remove_incorrect_fixed_ip_from_server(
        flavor,
        security_group,
        keypair,
        ubuntu_image,
        # network,
        # subnet,
        # router,
        # add_router_interfaces,
        nova_floating_ip,
        create_server,
        server_steps,
        network_steps):

    # BUG: https://bugs.launchpad.net/nova/+bug/1534186
    # add_router_interfaces(router, [subnet])

    network = network_steps.get_network_by_name(
        config.ADMIN_INTERNAL_NETWORK_NAME)

    server_name = next(generate_ids('server'))
    server = create_server(
        server_name=server_name,
        image=ubuntu_image,
        flavor=flavor,
        networks=[network],
        keypair=keypair,
        security_groups=[security_group],
        username='ubuntu')

    ip_old = server_steps.get_ips(server, 'fixed', verbose=False)[0]
    ip_new = server_steps.attach_fixed_ip(server, network['id'])
    # ips_after_attach = server_steps.get_ips(server, 'fixed', verbose=False)
    print('old_ip=', ip_old, 'new_ip=', ip_new)

    fake_ip = ".".join([str(random.randint(190, 255)) for _ in range(4)])

    # import ipdb; ipdb.set_trace()
    # from IPython import embed; embed()

    server_steps.check_negative_detach_fixed_ip(server, fake_ip)
    server_steps.detach_fixed_ip(server, fake_ip)

    server_steps.attach_floating_ip(server, nova_floating_ip)
    server_steps.get_server_credentials(server)
    server_steps.get_server_ssh(server)
