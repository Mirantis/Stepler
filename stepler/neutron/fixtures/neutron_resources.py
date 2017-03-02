"""
----------------------
Neutron tests fixtures
----------------------
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

import functools

import attrdict
from neutronclient.common import exceptions
import pytest

from stepler import config
from stepler.third_party import utils

__all__ = [
    'neutron_2_networks',
    'neutron_2_servers_different_networks',
    'neutron_2_servers_different_subnets',
    'neutron_2_servers_diff_nets_with_floating',
    'neutron_2_servers_same_network',
    'neutron_2_servers_iperf_different_networks',
    'neutron_conntrack_2_projects_resources',
    'neutron_2_servers_2_nets_diff_projects',
    'neutron_2_nets_diff_projects',
    'neutron_2_servers_2_projects_with_shared_net',
    'create_max_networks_with_instances',
]


@pytest.fixture
def neutron_2_networks(
        request,
        net_subnet_router,
        public_network,
        create_network,
        create_subnet,
        create_router,
        add_router_interfaces,
        router_steps):
    """Function fixture to prepare environment with 2 networks.

    This fixture creates router(s), 2 networks and 2 subnets and connects
    networks to router(s). By default, both networks will be connected to
    single router.

    All created resources are to be deleted after test.

    Can be parametrized with 'different_routers' to create 2 routers and
    connect each of networks to different router.

    Example:
        @pytest.mark.parametrize('neutron_2_networks',
                                 ['different_routers'],
                                 indirect=True)
        def test_foo(neutron_2_networks):
            # Will be created 2 routers, each of them will be linked with one
            # of the subnets.

    Args:
        request (obj): py.test SubRequest
        net_subnet_router (tuple): network, subnet, router
        public_network (dict): neutron public network
        create_network (function): function to create network
        create_subnet (function): function to create subnet
        create_router (function): function to create router
        add_router_interfaces (function): function to add subnet interface to
            router
        router_steps (obj): instantiated router steps

    Returns:
        attrdict.AttrDict: created resources
    """
    network, subnet, router = net_subnet_router
    network_2 = create_network(next(utils.generate_ids()))

    subnet_2 = create_subnet(
        subnet_name=next(utils.generate_ids()),
        network=network_2,
        cidr='192.168.2.0/24')
    routers = [router]
    if getattr(request, 'param', None) == 'different_routers':
        router_2 = create_router(next(utils.generate_ids()))
        router_steps.set_gateway(router_2, public_network)
        routers.append(router_2)
        add_router_interfaces(router_2, [subnet_2])
    else:
        add_router_interfaces(router, [subnet_2])

    return attrdict.AttrDict(
        networks=[network, network_2],
        subnets=[subnet, subnet_2],
        routers=routers)


@pytest.fixture
def neutron_2_servers_different_networks(
        request,
        cirros_image,
        flavor,
        security_group,
        sorted_hypervisors,
        neutron_2_networks,
        hypervisor_steps,
        server_steps):
    """Function fixture to prepare environment with 2 servers.

    This fixture creates router, 2 networks and 2 subnets, connects networks
    to router, boot nova server on each network on different computes.

    All created resources are to be deleted after test.

    Can be parametrized with 'same_host'.

    Example:
        @pytest.mark.parametrize('neutron_2_servers_different_networks',
                                 ['same_host'],
                                 indirect=True)
        def test_foo(neutron_2_servers_different_networks):
            # Instances will be created on the same compute

    Args:
        request (obj): py.test SubRequest
        cirros_image (obj): cirros image
        flavor (obj): nova flavor
        security_group (obj): nova security group
        sorted_hypervisors (list): available hypervisors
        neutron_2_networks (obj): neutron networks, subnets, router(s)
            resources AttrDict instance
        hypervisor_steps (obj): instantiated nova hypervisor steps
        server_steps (obj): instantiated nova server steps

    Returns:
        attrdict.AttrDict: created resources
    """

    hypervisors = sorted_hypervisors[:2]
    if getattr(request, 'param', None) == 'same_host':
        hypervisors[1] = hypervisors[0]

    servers = []

    for hypervisor, network in zip(hypervisors, neutron_2_networks.networks):
        server = server_steps.create_servers(
            image=cirros_image,
            flavor=flavor,
            networks=[network],
            availability_zone='nova:{}'.format(hypervisor.service['host']),
            security_groups=[security_group],
            username=config.CIRROS_USERNAME,
            password=config.CIRROS_PASSWORD,
            check=False)[0]
        servers.append(server)

    for server in servers:

        server_steps.check_server_status(
            server,
            expected_statuses=[config.STATUS_ACTIVE],
            transit_statuses=[config.STATUS_BUILD],
            timeout=config.SERVER_ACTIVE_TIMEOUT)

    return attrdict.AttrDict(
        servers=servers,
        networks=neutron_2_networks.networks,
        routers=neutron_2_networks.routers)


@pytest.fixture
def neutron_2_servers_diff_nets_with_floating(
        neutron_2_servers_different_networks,
        create_floating_ip,
        server_steps):
    """Function fixture to prepare environment with 2 servers.

    This fixture creates resources using neutron_2_servers_different_networks
    fixture, creates and attaches floating ips for all servers.

    All created resources are to be deleted after test.

    Args:
        neutron_2_servers_different_networks (AttrDict): neutron networks,
            subnets, router(s) and servers resources AttrDict instance
        create_floating_ip (function): function to create floating IP
        server_steps (obj): instantiated nova server steps

    Returns:
        attrdict.AttrDict: created resources
    """
    resources = attrdict.AttrDict(neutron_2_servers_different_networks.copy())

    floating_ips = []
    for server in resources.servers:
        floating_ip = create_floating_ip()
        server_steps.attach_floating_ip(server, floating_ip)
        floating_ips.append(floating_ip)

    resources.floating_ips = floating_ips

    return resources


@pytest.fixture
def neutron_2_servers_same_network(
        request,
        cirros_image,
        flavor,
        security_group,
        net_subnet_router,
        server,
        hypervisor_steps,
        server_steps):
    """Function fixture to prepare environment with 2 servers.

    This fixture creates router, network and subnet, connects network
    to router, boot 2 nova servers on different computes.

    All created resources are to be deleted after test.

    Can be parametrized with 'same_host'.

    Example:
        @pytest.mark.parametrize('neutron_2_servers_same_network',
                                 ['same_host'],
                                 indirect=True)
        def test_foo(neutron_2_servers_same_network):
            # Instances will be created on the same compute

    Args:
        request (obj): py.test SubRequest
        cirros_image (obj): cirros image
        flavor (obj): nova flavor
        security_group (obj): nova security group
        net_subnet_router (tuple): network, subnet, router
        server (obj): nova server
        hypervisor_steps (obj): instantiated nova hypervisor steps
        server_steps (obj): instantiated nova server steps

    Returns:
        attrdict.AttrDict: created resources
    """

    if getattr(request, 'param', None) == 'same_host':
        server_2_hypervisor = getattr(server, config.SERVER_ATTR_HOST)
    else:
        server_2_hypervisor = hypervisor_steps.get_another_hypervisor([server])
        server_2_hypervisor = server_2_hypervisor.service['host']

    network, subnet, router = net_subnet_router

    server_2 = server_steps.create_servers(
        image=cirros_image,
        flavor=flavor,
        networks=[network],
        availability_zone='nova:{}'.format(server_2_hypervisor),
        security_groups=[security_group],
        username=config.CIRROS_USERNAME,
        password=config.CIRROS_PASSWORD)[0]

    return attrdict.AttrDict(
        servers=(server, server_2),
        network=network,
        router=router)


@pytest.fixture
def neutron_2_servers_iperf_different_networks(
        ubuntu_image,
        flavor,
        keypair,
        security_group,
        neutron_2_networks,
        hypervisor_steps,
        neutron_security_group_rule_steps,
        server_steps):
    """Function fixture to prepare environment with 2 ubuntu servers.

    This fixture creates router, 2 networks and 2 subnets, connects networks
    to router, boots nova server with ubuntu on each network on different
    computes, installs iperf to both servers, starts TCP and UDP iperf servers.

    All created resources are to be deleted after test.

    Args:
        ubuntu_image (obj): ubuntu image
        flavor (obj): nova flavor
        keypair (obj): nova server keypair
        security_group (obj): nova security group
        neutron_2_networks (obj): neutron networks, subnets, router(s)
            resources AttrDict instance
        hypervisor_steps (obj): instantiated nova hypervisor steps
        neutron_security_group_rule_steps (obj): instantiated neutron security
            group rules steps
        server_steps (obj): instantiated nova server steps

    Returns:
        attrdict.AttrDict: created resources
    """

    network_1, network_2 = neutron_2_networks.networks
    router = neutron_2_networks.routers[0]

    rules = [
        {
            # iprf tcp
            'direction': config.INGRESS,
            'protocol': 'tcp',
            'port_range_min': config.IPERF_TCP_PORT,
            'port_range_max': config.IPERF_TCP_PORT,
            'remote_ip_prefix': '0.0.0.0/0',
        },
        {
            # iperf udp
            'direction': config.INGRESS,
            'protocol': 'udp',
            'port_range_min': config.IPERF_UDP_PORT,
            'port_range_max': config.IPERF_UDP_PORT,
            'remote_ip_prefix': '0.0.0.0/0',
        }
    ]
    neutron_security_group_rule_steps.add_rules_to_group(security_group['id'],
                                                         rules)

    hypervisors = hypervisor_steps.get_hypervisors()[:2]
    servers = []

    for hypervisor, network in zip(hypervisors, [network_1, network_2]):
        server = server_steps.create_servers(
            image=ubuntu_image,
            flavor=flavor,
            keypair=keypair,
            networks=[network],
            userdata=config.START_IPERF_USERDATA,
            availability_zone='nova:{}'.format(hypervisor.service['host']),
            security_groups=[security_group],
            username=config.UBUNTU_USERNAME,
            check=False)[0]
        servers.append(server)

    for server in servers:

        server_steps.check_server_status(
            server,
            expected_statuses=[config.STATUS_ACTIVE],
            transit_statuses=[config.STATUS_BUILD],
            timeout=config.SERVER_ACTIVE_TIMEOUT)

        server_steps.check_server_log_contains_record(
            server,
            config.USERDATA_DONE_MARKER,
            timeout=config.USERDATA_EXECUTING_TIMEOUT)

    return attrdict.AttrDict(
        servers=servers,
        networks=(network_1, network_2),
        router=router)


@pytest.fixture
def neutron_conntrack_2_projects_resources(
        request,
        neutron_2_nets_diff_projects,
        conntrack_cirros_image,
        public_flavor,
        sorted_hypervisors,
        hypervisor_steps,
        port_steps,
        create_floating_ip,
        get_neutron_security_group_steps,
        get_neutron_security_group_rule_steps,
        get_server_steps):
    """Function fixture to prepare environment for conntrack tests.

    This fixture:

        * creates 2 projects;
        * creates net, subnet, router in each project;
        * creates security groups in each project;
        * add ping + ssh rules for 1'st project's security group;
        * add ssh rules for 2'nd project security group;
        * creates 2 servers in 1'st project;
        * creates 2 servers in 2'nd project with same fixed ip as for 1'st
            project;
        * add floating ips for one of servers in each project.

    All created resources are to be deleted after test.

    Args:
        request (obj): py.test SubRequest
        neutron_2_nets_diff_projects (AttrDict): neutron networks, subnets,
            router(s) resources AttrDict instance
        conntrack_cirros_image (obj): glance image for conntrack tests
        public_flavor (obj): nova flavor with is_public=True attribute
        sorted_hypervisors (list): sorted hypervisors
        hypervisor_steps (obj): instantiated nova hypervisor steps
        port_steps (obj): instantiated port steps
        create_floating_ip (function): function to create floating ip
        get_neutron_security_group_steps (function): function to get security
            group steps
        get_neutron_security_group_rule_steps (function): function to get
            security group rule steps
        get_server_steps (function): function to get server steps

    Returns:
        attrdict.AttrDict: created resources
    """
    base_name, = utils.generate_ids()

    server_count = hypervisor_steps.get_hypervisor_capacity(
        sorted_hypervisors[0], public_flavor)
    if server_count < 4:
        pytest.skip('Requires at least 4 servers with {flavor} to boot on '
                    'single compute'.format(flavor=public_flavor))

    hostname = sorted_hypervisors[0].service['host']
    hypervisor_hostname = sorted_hypervisors[0].hypervisor_hostname

    resources = []
    fixed_ip_1, fixed_ip_2 = config.LOCAL_IPS[20:22]

    for i in range(2):
        project_resources = attrdict.AttrDict()
        name = "{}_{}".format(base_name, i)
        servers = []
        credentials = neutron_2_nets_diff_projects.resources[i].credentials
        network, router = neutron_2_nets_diff_projects.resources[i].net_router
        project_id = neutron_2_nets_diff_projects.resources[i].project_id

        security_group_steps = get_neutron_security_group_steps(**credentials)
        security_group_rule_steps = get_neutron_security_group_rule_steps(
            **credentials)
        security_group_name = "{}_{}".format(base_name, i)
        security_group = security_group_steps.create(security_group_name)
        request.addfinalizer(
            functools.partial(security_group_steps.delete,
                              security_group))
        if i == 0:
            security_group_rule_steps.add_rules_to_group(
                security_group['id'], config.SECURITY_GROUP_SSH_PING_RULES)
        else:
            security_group_rule_steps.add_rules_to_group(
                security_group['id'], config.SECURITY_GROUP_SSH_RULES)

        server_steps = get_server_steps(**credentials)
        project_resources.server_steps = server_steps

        server1 = server_steps.create_servers(
            server_names=[name + "_1"],
            image=conntrack_cirros_image,
            flavor=public_flavor,
            availability_zone='nova:{}'.format(hostname),
            nics=[{
                'net-id': network['id'],
                'v4-fixed-ip': fixed_ip_1
            }],
            security_groups=[security_group],
            username=config.CIRROS_USERNAME,
            password=config.CIRROS_PASSWORD)[0]
        request.addfinalizer(
            functools.partial(server_steps.delete_servers, [server1]))
        servers.append(server1)

        server1_port = port_steps.get_port(
            device_owner=config.PORT_DEVICE_OWNER_SERVER, device_id=server1.id)
        create_floating_ip(port=server1_port, project_id=project_id)

        server2 = server_steps.create_servers(
            server_names=[name + "_2"],
            image=conntrack_cirros_image,
            flavor=public_flavor,
            availability_zone='nova:{}'.format(hostname),
            nics=[{
                'net-id': network['id'],
                'v4-fixed-ip': fixed_ip_2
            }],
            security_groups=[security_group],
            username=config.CIRROS_USERNAME,
            password=config.CIRROS_PASSWORD)[0]
        request.addfinalizer(
            functools.partial(server_steps.delete_servers, [server2]))
        servers.append(server2)
        project_resources.servers = servers
        resources.append(project_resources)
    return attrdict.AttrDict(resources=resources, hostname=hypervisor_hostname)


@pytest.fixture
def create_max_networks_with_instances(cirros_image,
                                       flavor,
                                       security_group,
                                       sorted_hypervisors,
                                       create_network,
                                       create_subnet,
                                       add_router_interfaces,
                                       current_project,
                                       neutron_quota_steps,
                                       hypervisor_steps,
                                       server_steps):
    """Callable fixture to create max networks, boot and delete servers.

    This fixture returns fuction to create max count of networks,
    subnet for each network, connect networks to router, boot
    nova server with cirros on each network and then delete
    created servers.

    Args:
        cirros_image (obj): cirros image
        flavor (obj): nova flavor
        security_group (obj): nova security group
        sorted_hypervisors (list): nova hypervisors list
        create_network (function): function to create network
        create_subnet (function): function to create subnet with options
        add_router_interfaces (function): function to add router interfaces to
            subnets
        current_project (obj): current project
        neutron_quota_steps (obj): instantiated neutron quota steps
        hypervisor_steps (obj): instantiated nova hypervisor steps
        server_steps (obj): instantiated nova server steps

    Returns:
        function: function to create max count of networks
    """
    def _create_max_networks_with_instances(router):
        max_instances = 0
        for hypervisor in sorted_hypervisors:
            max_instances += hypervisor_steps.get_hypervisor_capacity(
                hypervisor, flavor, check=False)

        net_list = []
        servers = []
        neutron_quotas = neutron_quota_steps.get(current_project)
        max_networks_count = neutron_quotas['network']
        try:
            # only about 34 nets can be created for one tenant during
            # implementation so we need to create either
            # max_networks_count of networks or until we get
            # ServiceUnavailable or OverQuotaClient errors as we don't know
            # the exact max possible count of networks to be created
            for i in range(1, max_networks_count + 1):
                network = create_network(next(utils.generate_ids()))
                # TODO(agromov): fix it if we can create more than 255 subnets
                subnet = create_subnet(next(utils.generate_ids()),
                                       network,
                                       cidr="192.168.{0}.0/24".format(i))
                add_router_interfaces(router, [subnet])
                net_list.append(network)

                if len(servers) >= max_instances:
                    server_steps.delete_servers(servers)
                    servers = []

                server = server_steps.create_servers(
                    image=cirros_image,
                    flavor=flavor,
                    networks=[network],
                    security_groups=[security_group])[0]
                servers.append(server)
        except (exceptions.ServiceUnavailable, exceptions.OverQuotaClient):
            pass

        server_steps.delete_servers(servers)

        return net_list

    return _create_max_networks_with_instances


@pytest.fixture
def neutron_2_servers_2_nets_diff_projects(
        request,
        neutron_2_nets_diff_projects,
        sorted_hypervisors,
        cirros_image,
        public_flavor,
        get_neutron_security_group_steps,
        get_neutron_security_group_rule_steps,
        get_server_steps,
        get_floating_ip_steps,
        port_steps):
    """Function fixture to prepare environment for different projects tests.

    This fixture:

        * creates 2 projects;
        * creates net, subnet, router in each project;
        * creates security groups in each project;
        * add ping + ssh rules for each security group;
        * create server in each project;
        * add floating ips for servers in each project.

    All created resources are to be deleted after test.

    Args:
        request (obj): py.test SubRequest
        neutron_2_nets_diff_projects (AttrDict): neutron networks, subnets,
            router(s) resources AttrDict instance
        sorted_hypervisors (list): sorted hypervisors
        cirros_image (obj): glance image
        public_flavor (obj): nova flavor with is_public=True attribute
        get_neutron_security_group_steps (function): function to get security
            group steps
        get_neutron_security_group_rule_steps (function): function to get
            security group rules steps
        get_server_steps (function): function to get server steps
        get_floating_ip_steps (function): function to get floating ip steps
        port_steps (obj): instantiated port steps

    Returns:
        attrdict.AttrDict: created resources
    """
    base_name, = utils.generate_ids()
    resources = []
    hostname = sorted_hypervisors[0].service['host']

    for i in range(2):
        project_resources = attrdict.AttrDict()
        credentials = neutron_2_nets_diff_projects.resources[i].credentials
        network, router = neutron_2_nets_diff_projects.resources[i].net_router

        # Create security group with ssh and ping rules
        security_group_steps = get_neutron_security_group_steps(**credentials)
        security_group_rule_steps = get_neutron_security_group_rule_steps(
            **credentials)
        security_group_name = "{}_{}".format(base_name, i)
        security_group = security_group_steps.create(security_group_name)
        request.addfinalizer(
            functools.partial(security_group_steps.delete,
                              security_group))
        security_group_rule_steps.add_rules_to_group(
            security_group['id'], config.SECURITY_GROUP_SSH_PING_RULES)

        # Create servers
        server_steps = get_server_steps(**credentials)
        project_resources.server_steps = server_steps
        server = server_steps.create_servers(
            image=cirros_image,
            flavor=public_flavor,
            availability_zone='nova:{}'.format(hostname),
            nics=[{'net-id': network['id']}],
            security_groups=[security_group],
            username=config.CIRROS_USERNAME,
            password=config.CIRROS_PASSWORD)[0]
        request.addfinalizer(
            functools.partial(server_steps.delete_servers, [server]))

        # Attach floating ips to servers
        floating_ip_steps = get_floating_ip_steps(**credentials)
        floating_ip = floating_ip_steps.create()
        request.addfinalizer(functools.partial(
            floating_ip_steps.delete, floating_ip))
        server_steps.attach_floating_ip(server, floating_ip)

        project_resources.server = server
        resources.append(project_resources)

    return attrdict.AttrDict(resources=resources)


@pytest.fixture
def neutron_2_nets_diff_projects(role_steps,
                                 create_project,
                                 create_user,
                                 create_network,
                                 create_subnet,
                                 create_router,
                                 router_steps,
                                 add_router_interfaces,
                                 public_network):
    """Function fixture to prepare environment for different projects tests.

    This fixture:

        * creates 2 projects;
        * creates net, subnet, router in each project;

    All created resources are to be deleted after test.

    Args:
        role_steps (obj): instantiated role steps
        create_project (function): function to create project
        create_user (function): function to create user
        create_network (function): function to create network
        create_subnet (function): function to create subnet
        create_router (function): function to create router
        router_steps (obj): instantiated router steps
        add_router_interfaces (function): function to add subnet interface to
            router
        public_network (dict): neutron public network

    Returns:
        attrdict.AttrDict: created resources
    """
    base_name, = utils.generate_ids()
    resources = []
    admin_role = role_steps.get_role(name=config.ROLE_ADMIN)

    for i in range(2):
        project_resources = attrdict.AttrDict()
        name = "{}_{}".format(base_name, i)
        # Create project
        project = create_project(name)
        user = create_user(user_name=name, password=name)
        role_steps.grant_role(admin_role, user, project=project)
        credentials = dict(
            username=name, password=name, project_name=name)

        # Create network with subnet and router
        network = create_network(name, project_id=project.id)
        subnet = create_subnet(
            name,
            network=network,
            project_id=project.id,
            cidr=config.LOCAL_CIDR)
        router = create_router(name, project_id=project.id)
        router_steps.set_gateway(router, public_network)
        add_router_interfaces(router, [subnet])
        project_resources.credentials = credentials
        project_resources.net_router = [network, router]
        project_resources.project_id = project.id
        resources.append(project_resources)

    return attrdict.AttrDict(resources=resources)


@pytest.fixture
def neutron_2_servers_2_projects_with_shared_net(
        request,
        public_network,
        conntrack_cirros_image,
        public_flavor,
        create_project,
        create_user,
        create_network,
        create_subnet,
        create_router,
        add_router_interfaces,
        port_steps,
        role_steps,
        router_steps,
        get_server_steps,
        get_neutron_security_group_steps,
        get_neutron_security_group_rule_steps,
        get_floating_ip_steps):
    """Function fixture to prepare environment for different projects tests.

    This fixture:

        * creates 2 projects: admin and non-admin
        * creates security groups in each project;
        * add ping + ssh rules for each security group;
        * creates shared net with subnet and router in admin project;
        * create server in each project;
        * add floating ips for servers in each project.

    All created resources are to be deleted after test.

    Args:
        request (obj): py.test SubRequest
        public_network (dict): neutron public network
        conntrack_cirros_image (obj): glance image with public visibility
        public_flavor (obj): nova flavor with is_public=True attribute
        create_project (function): function to create project
        create_user (function): function to create user
        create_network (function): function to create network
        create_subnet (function): function to create subnet
        create_router (function): function to create router
        add_router_interfaces (function): function to add subnet interface to
            router
        port_steps (obj): instantiated port steps
        role_steps (obj): instantiated role steps
        router_steps (obj): instantiated router steps
        get_server_steps (function): function to get server steps
        get_neutron_security_group_steps (function): function to get security
            group steps
        get_neutron_security_group_rule_steps (function): function to get
            security group rules steps
        get_floating_ip_steps (function): function to get floating ip steps

    Returns:
        attrdict.AttrDict: created resources
    """
    base_name, = utils.generate_ids()
    resources = []
    final_resources = []
    admin_role = role_steps.get_role(name=config.ROLE_ADMIN)
    member_role = role_steps.get_role(name=config.ROLE_MEMBER)

    for i in range(2):
        project_resources = attrdict.AttrDict()
        name = "{}_{}".format(base_name, i)
        # Create projects
        project = create_project(name)
        user = create_user(user_name=name, password=name)
        if i == 0:
            role_steps.grant_role(admin_role, user, project=project)
        else:
            role_steps.grant_role(member_role, user, project=project)
        credentials = dict(
            username=name, password=name, project_name=name)
        # Create security groups with rule
        security_group_steps = get_neutron_security_group_steps(**credentials)
        security_group_rule_steps = get_neutron_security_group_rule_steps(
            **credentials)
        security_group_name = "{}_{}".format(base_name, i)
        security_group = security_group_steps.create(security_group_name)
        request.addfinalizer(functools.partial(
            security_group_steps.delete, security_group))
        security_group_rule_steps.add_rules_to_group(
            security_group['id'], config.SECURITY_GROUP_SSH_PING_RULES)

        project_resources.credentials = credentials
        project_resources.project_id = project.id
        project_resources.security_group = security_group
        resources.append(project_resources)

    # Create shared network in 1st project
    project_id = resources[0].project_id
    network = create_network(base_name, project_id=project_id, shared=True)
    subnet = create_subnet(base_name, network=network, project_id=project_id,
                           cidr=config.LOCAL_CIDR)
    router = create_router(base_name, project_id=project_id)
    router_steps.set_gateway(router, public_network)
    add_router_interfaces(router, [subnet])

    for i in range(2):
        project_resources = attrdict.AttrDict()
        # Create servers
        server_steps = get_server_steps(**resources[i].credentials)
        server = server_steps.create_servers(
            image=conntrack_cirros_image,
            flavor=public_flavor,
            availability_zone='nova',
            nics=[{'net-id': network['id']}],
            security_groups=[resources[i].security_group],
            username=config.CIRROS_USERNAME,
            password=config.CIRROS_PASSWORD)[0]
        request.addfinalizer(
            functools.partial(server_steps.delete_servers, [server]))
        # Add floating ips to servers
        floating_ip_steps = get_floating_ip_steps(**resources[i].credentials)
        floating_ip = floating_ip_steps.create(public_network)
        request.addfinalizer(functools.partial(
            floating_ip_steps.delete, floating_ip))
        server_steps.attach_floating_ip(server, floating_ip)

        project_resources.server = server
        project_resources.server_steps = server_steps
        final_resources.append(project_resources)

    return attrdict.AttrDict(resources=final_resources)


@pytest.fixture
def neutron_2_servers_different_subnets(
        cirros_image,
        flavor,
        security_group,
        net_subnet_router,
        server,
        create_subnet,
        add_router_interfaces,
        server_steps):
    """Function fixture to prepare environment with 2 servers.

    This fixture creates router, network and 2 subnets, connects subnets
    to router, boot 2 nova servers on different subnets and on the same
    compute.

    All created resources are to be deleted after test.

    Args:
        cirros_image (obj): cirros image
        flavor (obj): nova flavor
        security_group (obj): nova security group
        net_subnet_router (tuple): network, subnet, router
        server (obj): nova server
        create_subnet (function): function to create subnet
        add_router_interfaces (function): function to add subnet interface to
            router
        server_steps (obj): instantiated nova server steps

    Returns:
        attrdict.AttrDict: created resources
    """

    network, subnet, router = net_subnet_router
    subnet_2 = create_subnet(
        subnet_name=next(utils.generate_ids()),
        network=network,
        cidr='192.168.2.0/24')
    add_router_interfaces(router, [subnet_2])

    server_2_host = getattr(server, config.SERVER_ATTR_HOST)
    server_2 = server_steps.create_servers(
        image=cirros_image,
        flavor=flavor,
        nics=[{
            'net-id': network['id'],
            'v4-fixed-ip': '192.168.2.10'
        }],
        availability_zone='nova:{}'.format(server_2_host),
        security_groups=[security_group],
        username=config.CIRROS_USERNAME,
        password=config.CIRROS_PASSWORD)[0]

    return attrdict.AttrDict(
        servers=(server, server_2),
        network=network,
        router=router)
