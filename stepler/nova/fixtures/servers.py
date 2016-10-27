"""
---------------
Server fixtures
---------------
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

import logging

from hamcrest import assert_that, is_not  # noqa
import pytest

from stepler import config
from stepler.nova.steps import ServerSteps
from stepler.third_party.context import context
from stepler.third_party.utils import generate_ids

__all__ = [
    'create_server',
    'create_server_context',
    'create_servers',
    'create_servers_context',
    'get_server_steps',
    'get_ssh_proxy_cmd',
    'server',
    'server_steps',
    'servers_cleanup'
]

LOGGER = logging.getLogger(__name__)
# servers which should be missed, when unexpected servers will be removed
SKIPPED_SERVERS = []


@pytest.yield_fixture
def servers_cleanup():
    """Callable function fixture to clear unexpected servers.

    It provides cleanup before and after test. Cleanup before test is callable
    with injecton of server steps. Should be called before returning of
    instantiated server steps.
    """
    _server_steps = [None]

    def _servers_cleanup(server_steps):
        assert_that(server_steps, is_not(None))
        _server_steps[0] = server_steps  # inject server steps for finalizer
        # check=False because in best case no servers will be present
        servers = server_steps.get_servers(name_prefix=config.STEPLER_PREFIX,
                                           check=False)
        if SKIPPED_SERVERS:
            server_names = [server.name for server in SKIPPED_SERVERS]
            LOGGER.debug(
                "SKIPPED_SERVERS contains servers {!r}. They will not be "
                "removed in cleanup procedure.".format(server_names))

        servers = [server for server in servers
                   if server not in SKIPPED_SERVERS]
        if servers:
            server_steps.delete_servers(servers)

    yield _servers_cleanup

    _servers_cleanup(_server_steps[0])


@pytest.fixture(scope='session')
def get_server_steps(request, get_nova_client):
    """Callable session fixture to get server steps.

    Args:
        get_nova_client (function): function to get nova client.

    Returns:
        function: function to get server steps.
    """
    def _get_server_steps():
        return ServerSteps(get_nova_client().servers)

    return _get_server_steps


@pytest.fixture
def server_steps(get_server_steps, servers_cleanup):
    """Function fixture to get nova steps.

    Args:
        get_server_steps (function): function to get server steps
        servers_cleanup (function): function to make servers cleanup right
            after server steps initialization

    Returns:
        ServerSteps: instantiated server steps.
    """
    _server_steps = get_server_steps()
    servers_cleanup(_server_steps)
    return _server_steps


@pytest.yield_fixture
def create_servers(server_steps):
    """Fixture to create servers with options.

    Can be called several times during test.
    """
    names = []

    def _create_servers(server_names, *args, **kwgs):
        server_names = list(server_names)
        names.extend(server_names)
        _servers = server_steps.create_servers(server_names, *args, **kwgs)
        return _servers

    yield _create_servers

    if names:
        servers = [s for s in server_steps.get_servers(check=False)
                   if s.name in names]
        server_steps.delete_servers(servers)


@pytest.fixture
def create_server(create_servers):
    """Fixture to create server with options.

    Can be called several times during test.
    """
    def _create_server(server_name, *args, **kwgs):
        return create_servers([server_name], *args, **kwgs)[0]

    return _create_server


@pytest.fixture
def create_servers_context(server_steps):
    """Function fixture to create servers inside context.

    It guarantees servers deletion after context exit.
    It should be used when ``servers`` must be deleted inside a test, and their
    deletion can't be delegated to fixture finalization. Can be called several
    times during a test.

    Example:
        .. code:: python

           def test_something(create_servers_context):
               for i in sequence:  # sequence can't be calculated outside test
                   with create_servers_context(*args, **kwgs) as servers:
                       [server.do_something() for server in servers]

    Args:
        server_steps (stepler.nova.steps.ServerSteps): instantiated steps
            object to manipulate with ``server`` resource.

    Returns:
        function: function to use as context manager to create servers
    """
    @context
    def _create_servers_context(server_names, *args, **kwgs):
        servers = server_steps.create_servers(server_names, *args, **kwgs)
        yield servers
        server_steps.delete_servers(servers)

    return _create_servers_context


@pytest.fixture
def create_server_context(create_servers_context):
    """Function fixture to create server inside context.

    It guarantees server deletion after context exit.
    It should be used when ``server`` must be deleted inside a test, and its
    deletion can't be delegated to fixture finalization. Can be called several
    times during a test.

    Example:
        .. code:: python

           def test_something(create_server_context):
               for i in sequence:  # sequence can't be calculated outside test
                   with create_server_context(*args, **kwgs) as server:
                       server.do_something()

    Args:
        create_servers_context (function): context manager to create servers

    Returns:
        function: function to use as context manager to create server
    """
    @context
    def _create_server_context(server_name, *args, **kwgs):
        with create_servers_context([server_name], *args, **kwgs) as servers:
            yield servers[0]

    return _create_server_context


@pytest.fixture
def server(create_server, cirros_image, flavor, internal_network):
    """Function fixture to create server with default options before test.

    Args:
        create_server (function): function to create a nova server
        cirros_image (object): cirros image from glance
        flavor (object): nova flavor
        internal_network (object): neutron internal network

    Returns:
        object: nova server
    """
    return create_server(next(generate_ids('server')),
                         image=cirros_image,
                         flavor=flavor,
                         networks=[internal_network])


# TODO(schipiga): this fixture is rudiment of MOS. Will be changed in future.
@pytest.fixture
def get_ssh_proxy_cmd(admin_ssh_key_path,
                      ip_by_host,
                      network_steps,
                      server_steps):
    """Callable function fixture to get ssh proxy data of server.

    Args:
        admin_ssh_key_path (str): path to admin ssh key
        ip_by_host (function): function to get IP by host
        network_steps (NetworkSteps): instantiated network steps
        server_steps (ServerSteps): instantiated server steps

    Returns:
        function: function to get ssh proxy command
    """
    def _get_ssh_proxy_cmd(server, ip=None):
        # proxy command is actual for fixed IP only
        server_ips = server_steps.get_ips(server, 'fixed')
        ip_info = server_ips[ip] if ip else server_ips.values()[0]
        server_ip = ip_info['ip']
        server_mac = ip_info['mac']
        net_id = network_steps.get_network_id_by_mac(server_mac)
        dhcp_netns = "qdhcp-{}".format(net_id)
        dhcp_host = network_steps.get_dhcp_host_by_network(net_id)
        dhcp_server_ip = ip_by_host(dhcp_host)
        proxy_cmd = 'ssh -i {} root@{} ip netns exec {} netcat {} 22'.format(
            admin_ssh_key_path, dhcp_server_ip, dhcp_netns, server_ip)

        return proxy_cmd

    return _get_ssh_proxy_cmd
