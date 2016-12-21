"""
------------------
Openstack fixtures
------------------
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

import attrdict
from keystoneauth1 import identity
from keystoneauth1 import session as _session
import pytest
from requests.packages import urllib3

from stepler import config
from stepler.third_party import context

__all__ = [
    'get_session',
    'session',
    'os_credentials',
    'uncleanable',
]


@pytest.fixture(scope='session')
def get_session(os_credentials):
    """Callable session fixture to get keystone session.

    Can be called several times during a test to regenerate keystone session.

    Args:
        os_credentials (AttrDict): data structure with credentials to be used

    Returns:
        function: function to get session.

    **Returned function description:**

    Args:
        auth_url (str, optional): Keystone auth URL. By default retrieved
            from config. Can be managed via environment variable `OS_AUTH_URL`.
        username (str, optional): Keystone username. By default retrieved
            from config. Can be managed via environment variable `OS_USERNAME`.
        password (str, optional): Keystone password. By default retrieved
            from config. Can be managed via environment variable `OS_PASSWORD`.
        project_name (str, optional): Keystone project name. By default it's
            retrieved from config. Can be managed via environment variable
            `OS_PROJECT_NAME`.
        user_domain_name (str, optional): Keystone user domain name. For
            keystone **v3** only. By default retrieved from config. Can be
            managed via environment variable `OS_USER_DOMAIN_NAME`.
        project_domain_name (str, optional): Keystone project domain name. For
            keystone **v3** only. By default retrieved via environment
            variable `OS_PROJECT_DOMAIN_NAME`.
        cert(str, tuple, optional): Either a single filename containing both
            the certificate and key or a tuple containing the path to the
            certificate then a path to the key.

    Returns:
        Session: Keystone auth session. According to environment variable
        `OS_AUTH_URL` uses `v3` or `v2.0` API version.

    Raises:
        AssertionError: If environment variable `OS_AUTH_URL` isn't specified.
        ValueError: If keystone API version in config is neither v2.0 no v3.

    See also:
        :func:`session`
    """
    assert config.AUTH_URL, "Environment variable OS_AUTH_URL is not defined"

    def _get_session(auth_url=None,
                     username=None,
                     password=None,
                     project_name=None,
                     user_domain_name=None,
                     project_domain_name=None,
                     cert=None):
        auth_url = auth_url or os_credentials.auth_url
        username = username or os_credentials.username
        password = password or os_credentials.password
        project_name = project_name or os_credentials.project_name
        user_domain_name = (user_domain_name or
                            os_credentials.user_domain_name)
        project_domain_name = (project_domain_name or
                               os_credentials.project_domain_name)

        if config.KEYSTONE_API_VERSION == 3:

            auth = identity.v3.Password(
                auth_url=auth_url,
                username=username,
                user_domain_name=user_domain_name,
                password=password,
                project_name=project_name,
                project_domain_name=project_domain_name)

        elif config.KEYSTONE_API_VERSION == 2:

            auth = identity.v2.Password(
                auth_url=auth_url,
                username=username,
                password=password,
                tenant_name=project_name)

        else:
            raise ValueError("Unexpected keystone API version: {}".format(
                config.KEYSTONE_API_VERSION))

        if cert is None:
            urllib3.disable_warnings()
            return _session.Session(auth=auth, cert=cert, verify=False)
        else:
            return _session.Session(auth=auth, cert=cert)

    return _get_session


@pytest.fixture
def session(get_session):
    """Function fixture to get keystone session with default options.

    Args:
        get_session (function): Function to get keystone session.

    Returns:
        Session: Keystone session.

    See also:
        :func:`get_session`
    """
    return get_session()


@pytest.fixture(scope='session')
def os_credentials():
    """Session fixture to get data structure with current credentials to use.

    These fixture initialises default credentials variables which are
    used in get_session fixture. If new created project should be used
    in tests, credentials should be changed using 'change' context manager.
    After that new sessions should be created for all steps.
    For example if project_steps should be used with new credentials,
    get_project_steps should be used for its recreation.

    Returns:
        AttrDict: contains vars which will be used in get_session
    """
    credentials = attrdict.AttrDict()
    credentials.auth_url = config.AUTH_URL
    credentials.project_name = config.PROJECT_NAME
    credentials.username = config.USERNAME
    credentials.password = config.PASSWORD
    credentials.user_domain_name = config.USER_DOMAIN_NAME
    credentials.project_domain_name = config.PROJECT_DOMAIN_NAME

    @context.context
    def _change_credentials(project_name, username, password):
        old_credentials = None

        if (credentials.project_name != project_name or
                credentials.username != username):
            old_credentials = attrdict.AttrDict(credentials.copy())
            credentials.project_name = project_name
            credentials.username = username
            credentials.password = password

        yield

        if old_credentials is not None:
            credentials.project_name = old_credentials.project_name
            credentials.username = old_credentials.username
            credentials.password = old_credentials.password

    credentials.change = _change_credentials

    return credentials


@pytest.fixture(scope='session')
def uncleanable():
    """Session fixture to get data structure with resources not to cleanup.

    Each test uses cleanup resources mechanism, but some resources should be
    skipped there, because they should be present during several tests. This
    data structure contains such resources.
    """
    data = attrdict.AttrDict()
    data.backup_ids = set()
    data.image_ids = set()
    data.keypair_ids = set()
    data.server_ids = set()
    data.nodes_ids = set()
    data.chassis_ids = set()
    data.snapshot_ids = set()
    data.transfer_ids = set()
    data.volume_ids = set()
    return data
