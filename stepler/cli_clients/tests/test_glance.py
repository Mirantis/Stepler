"""
----------------
Glance CLI tests
----------------
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

import pytest

from stepler.third_party import utils


@pytest.mark.idempotent_id('b5948a9d-a0a2-40ca-9638-554020dcde80',
                           api_version=1)
@pytest.mark.idempotent_id('928a6294-d172-4c7a-afc1-5e0fa772caf4',
                           api_version=2)
@pytest.mark.parametrize('api_version', [1, 2])
def test_upload_image_without_properties(cli_glance_steps, api_version):
    """**Scenario:** Verify image is not created from file without properties.

    Test checks image from file can't be created without disk-format and
    container-format

    **Steps:**

    #. Run cli command 'glance image-create --file <filename>'
    #. Check that command failed with expected error message
    """
    cli_glance_steps.check_negative_image_create_without_properties(
        filename=next(utils.generate_ids()), api_version=api_version)


<<<<<<< HEAD
@pytest.mark.idempotent_id('54bdc370-45f6-4085-977c-07996fb81943',
                           api_version=1)
@pytest.mark.idempotent_id('30537390-e1ba-47bc-aca0-db94a740f728',
                           api_version=2)
@pytest.mark.parametrize('api_version', [1, 2])
def test_project_in_image_member_list(cirros_image,
                                      project,
                                      cli_glance_steps,
                                      glance_steps,
                                      api_version):
    """**Scenario:** Verify 'glance member-list' command.

    Test checks that 'glance member-list --image_id <id>' shows bound project.

    **Setup:**

    #. Create cirros image
    #. Create non-admin project

    **Steps:**

    #. Bind project to image via API
    #. Check cli command 'glance member-list --image_id <id>' shows bound
        project

    **Teardown:**

    #. Delete project
    #. Delete cirros image
    """
    glance_steps.bind_project(cirros_image, project, check=False)
    cli_glance_steps.check_project_in_image_member_list(
        cirros_image, project, api_version=api_version)


@pytest.mark.idempotent_id('885ce1ec-ad7d-4401-b67d-14b5f2451674',
                           api_version=1)
@pytest.mark.idempotent_id('3adc71e3-2362-4a95-aac6-93a14da65487',
                           api_version=2)
@pytest.mark.parametrize('api_version', [1, 2])
def test_create_image_member(cirros_image,
                             project,
                             cli_glance_steps,
                             glance_steps,
                             api_version):
    """**Scenario:** Verify 'glance member-create' command.

    **Setup:**

    #. Create cirros image
    #. Create non-admin project

    **Steps:**

    #. Run cli command 'glance member-create <image_id> <project_id>'
    #. Check that project is in image member-list via API

    **Teardown:**

    #. Delete project
    #. Delete cirros image
    """
    cli_glance_steps.create_image_member(cirros_image, project,
                                         api_version=api_version)
    glance_steps.check_image_bind_status(cirros_image, project)


@pytest.mark.idempotent_id('41594846-bf76-4132-9d80-3cb679b12516',
                           api_version=1)
@pytest.mark.idempotent_id('e2393652-ae09-42ae-87fd-7b16adeaa6f7',
                           api_version=2)
@pytest.mark.parametrize('api_version', [1, 2])
def test_delete_image_member(cirros_image,
                             project,
                             cli_glance_steps,
                             glance_steps,
                             api_version):
    """**Scenario:** Verify 'glance member-delete' command.

    **Setup:**

    #. Create cirros image
    #. Create non-admin project

    **Steps:**

    #. Bind project to image via API
    #. Run cli command 'glance member-delete <image_id> <project_id>'
    #. Check that project not in image member-list via API

    **Teardown:**

    #. Delete project
    #. Delete cirros image
    """
    glance_steps.bind_project(cirros_image, project)
    cli_glance_steps.delete_image_member(cirros_image, project,
                                         api_version=api_version)
    glance_steps.check_image_bind_status(cirros_image, project, bound=False)
=======
@pytest.mark.idempotent_id('9290e363-0607-45be-be0a-1e832da59b94')
@pytest.mark.usefixtures('images_cleanup')
@pytest.mark.usefixtures('delete_file')
def test_download_glance_image(cirros_image, glance_steps, cirros_image_path,
                               cli_glance_steps):
    """**Scenario:** Validate Glance image (upload/download, compare md5-sum

    of image).

    **Steps:**

    #. download image to disk via wget or generate a payload image
    #. create image
    #. download image
    #. compare md5sum

    **Teardown:**

    #. Delete image
    #. Delete file
    """
    with utils.generate_file_context(size=0) as cirros_image_file:
            cli_glance_steps.download_image(cirros_image, cirros_image_file)
            glance_steps.check_image_hash(cirros_image, cirros_image_path)
>>>>>>> 8475e48... Add CLI test for Validate Glance image with API V2
