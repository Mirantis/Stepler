"""
--------------
Keystone tests
--------------
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

from stepler import config
from stepler.third_party import utils


@pytest.mark.idempotent_id('89ef26c6-600a-4f69-afeb-d3b8d9ad1244')
def test_keystone_permission_lose(admin,
                                  project,
                                  admin_role,
                                  project_steps,
                                  role_steps,
                                  user_steps):
    """**Scenario:** Check that admin have access to users and projects in this
    session.

    **Setup:**

    #. Create new project

    **Steps:**

    #. Add admin member with admin role to this project
    #. Remove the admin role for this project
    #. Check that admin is able to get projects and users

    **Teardown:**

    #. Delete project
    """
    role_steps.grant_role(admin_role, user=admin, project=project)
    role_steps.revoke_role(admin_role, user=admin, project=project)
    project_steps.get_projects()
    user_steps.get_users()


@pytest.mark.idempotent_id('76f823ac-5c8b-4617-a4cc-9e30257a679f')
def test_restart_all_services(cirros_image,
                              tiny_flavor,
                              keypair,
                              net_subnet_router,
                              security_group,
                              create_user,
                              user_steps,
                              os_faults_steps,
                              server_steps):
    """**Scenario:** Check that keystone works after restarting services.

    **Setup:**

    #. Create cirros image
    #. Create tiny flavor
    #. Create key pair
    #. Create network with subnet and router

    **Steps:**

    #. Create new user 1
    #. Check that user 1 is present in user list
    #. Restart keystone services
    #. Check that user 1 is present in user list
    #. Create new user 2
    #. Check that user 2 is present in user list
    #. Create VM
    #. Check its status = ACTIVE

    **Teardown:**

    #. Delete VM
    #. Delete network, subnet, router
    #. Delete users 1 and 2
    #. Delete key pair
    #. Delete tiny flavor
    #. Delete cirros image
    """
    user_name = next(utils.generate_ids('user'))
    user1 = create_user(user_name=user_name, password=user_name)

    os_faults_steps.restart_services([config.KEYSTONE])

    user_steps.check_user_presence(user1)
    user_name = next(utils.generate_ids('user'))
    create_user(user_name=user_name, password=user_name)

    network, _, _ = net_subnet_router
    server_steps.create_servers(image=cirros_image,
                                flavor=tiny_flavor,
                                networks=[network],
                                keypair=keypair,
                                security_groups=[security_group])


@pytest.mark.idempotent_id('14ed4331-c05e-4b9a-9723-eac8c6f3f26a')
def test_check_objects_are_revoked(role_steps,
                                   get_project_steps,
                                   create_project,
                                   create_user):
    """**Scenario:** Check that keystone objects are revoked correctly.

    https://bugs.launchpad.net/mos/+bug/1546197
    When you delete a role assignment using a user+role+project pairing,
    unscoped tokens between the user+project are unnecessarily revoked as
    well. In fact, two events are created for each role assignment deletion
    (one that is scoped correctly and one that is scoped too broadly).

    **Setup:**

    #. Create project
    #. Create user

    **Steps:**

    #. Add new project in admin tenant
    #. Login under this user
    #. Get projects
    #. Delete new user from admin tenant
    #. Get projects

    **Teardown:**

    #. Delete user
    #. Delete project
    """
    user_name = next(utils.generate_ids('user'))
    user_password = next(utils.generate_ids('password'))
    project_name = next(utils.generate_ids('project'))

    project = create_project(project_name=project_name, domain='default')
    user = create_user(user_name,
                       user_password,
                       default_project=project)
    admin_role = role_steps.get_role(name='admin')
    role_steps.grant_role(role=admin_role, user=user, project=project)

    user_credentials = {'username': user_name,
                        'password': user_password,
                        'project_name': project_name}

    user_project_steps = get_project_steps(**user_credentials)
    user_project_steps.get_projects()
    role_steps.revoke_role(role=admin_role, user=user, project=project)
    user_project_steps.check_get_projects_requires_authentication()


@pytest.mark.idempotent_id('e52e771c-b8e4-4af5-981f-76b975e5b110')
def test_modify_project_members_update_quotas(admin_role,
                                              create_project,
                                              create_group,
                                              role_steps,
                                              project_steps):
    """**Scenario:** Failed to modify project members and update project quotas.

    https://bugs.launchpad.net/horizon/+bug/1326668

    **Setup:**

    #. Get admin role

    **Steps:**

    #. Create project
    #. Create group
    #. Add new project in admin tenant
    #. Get projects
    #. Delete new project from admin tenant
    #. Get projects

    **Teardown:**

    #. Delete group
    #. Delete project
    """
    project = create_project(next(utils.generate_ids('project')))
    group = create_group(next(utils.generate_ids('group')))

    role_steps.grant_role(role=admin_role, project=project, group=group)
    project_steps.get_projects()
    role_steps.revoke_role(role=admin_role, project=project, group=group)
    project_steps.get_projects()
