"""
-------------
User fixtures
-------------
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
from stepler.keystone import steps
from stepler.third_party import utils

__all__ = [
    'admin',
    'create_user',
    'get_user_steps',
    'user_steps',
    'user',
    'current_user',
    'new_user_with_project',
]


@pytest.fixture(scope="session")
def get_user_steps(get_keystone_client):
    """Callable session fixture to get users steps.

    Args:
        get_keystone_client (function): function to get keystone client.

    Returns:
        function: function to get users steps.
    """
    def _get_steps(**credentials):
        return steps.UserSteps(get_keystone_client(**credentials).users)

    return _get_steps


@pytest.fixture
def user_steps(get_user_steps):
    """Function fixture to get user steps.

    Args:
        get_user_steps (function): function to get user steps

    Returns:
        stepler.keystone.steps.UserSteps: instantiated user steps
    """
    return get_user_steps()


@pytest.fixture
def admin(user_steps):
    """Function fixture to get admin.

    Args:
        user_steps (object): instantiated user steps

    Returns:
        object: user 'admin'
    """
    return user_steps.get_user(name='admin')


@pytest.yield_fixture
def create_user(user_steps):
    """Session callable fixture to create user with options.

    Can be called several times during a test.
    After the test it destroys all created users.

    Examples of using this fixture in test:
        create_user('user1', 'qwerty!')
        create_user(user_name='user2', password='user2', domain='ldap2')

    Args:
        user_steps (object): instantiated user steps

    Yields:
        function: function to create user with options

    """
    users = []

    def _create_user(*args, **kwgs):
        user = user_steps.create_user(*args, **kwgs)
        users.append(user)
        return user

    yield _create_user

    for user in users:
        user_steps.delete_user(user)


@pytest.fixture
def user(create_user):
    """Function fixture to create user with default options before test.

    Args:
        create_user (function): function to create user with options

    Returns:
        object: user
    """
    user_name = next(utils.generate_ids('user'))
    password = next(utils.generate_ids('password'))
    return create_user(user_name, password)


@pytest.fixture
def new_user_with_project(request, create_user_with_project):
    """Fixture to create new project with new '_member_' user.

    Args:
        request (obj): pytest SubRequest instance
        create_user_with_project (function): function to create
            project resources

    Yields:
        dict: dict with username, password and project_name
    """
    creds_alias, = utils.generate_ids()
    with_role = getattr(request, 'param', {}).get('with_role')

    if with_role:
        role_type = None
    else:
        role_type = config.ROLE_MEMBER

    with create_user_with_project(creds_alias,
                                  role_type=role_type) as resource:
        yield {'username': resource.user.name,
               'password': resource.password,
               'project_name': resource.project.name}


@pytest.fixture
def current_user(session, user_steps):
    """Fixture to get current user.

    Args:
        session (obj): keystone session
        user_steps (obj): instantiated user steps

    Returns:
        obj: current user
    """
    return user_steps.get_user_by_id(session.get_user_id())
