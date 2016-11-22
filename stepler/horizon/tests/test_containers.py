"""
---------------
Container tests
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

import pytest
from stepler.third_party import utils


@pytest.mark.usefixtures('any_one')
class TestAnyOne(object):
    """Tests for any one."""

    @pytest.mark.idempotent_id('e2804b4e-743e-4632-9c63-34066491a418')
    def test_create_public_container(self, create_container):
        """Verify that one can create public container."""
        container_name = next(utils.generate_ids('container'))
        create_container(container_name, public=True)

    @pytest.mark.idempotent_id('fde52ec8-1e68-4c9d-86d3-6dbc5d915c85')
    def test_available_public_container_url(self, create_container,
                                            containers_steps, horizon):
        """Verify that public container url is available."""
        container_name = next(utils.generate_ids('container'))
        create_container(container_name, public=True)

        with containers_steps.get_container(container_name):
            container_info = \
                containers_steps.get_container_info(container_name)

            folder_name = next(utils.generate_ids('folder'))
            containers_steps.create_folder(folder_name)

            containers_steps.check_folder_avaiable_by_public_url(
                folder_name, container_info['public_url'])

            containers_steps.delete_folder(folder_name)

    @pytest.mark.idempotent_id('27f9647e-a7be-454b-95c5-fe1aa84d665d')
    def test_upload_file_to_container(self, container, containers_steps):
        """Verify that one can upload file to container."""
        with containers_steps.get_container(container.name):
            file_path = next(utils.generate_files())

            file_name = containers_steps.upload_file(file_path)
            containers_steps.delete_file(file_name)

    @pytest.mark.idempotent_id('762249c5-ae19-4480-9295-b51501c0c817')
    def test_upload_file_to_folder(self, container, containers_steps):
        """Verify that one can upload file to folder."""
        with containers_steps.get_container(container.name):
            folder_name = next(utils.generate_ids('folder'))
            containers_steps.create_folder(folder_name)

            with containers_steps.get_folder(folder_name):
                file_path = next(utils.generate_files())
                file_name = containers_steps.upload_file(file_path)
                containers_steps.delete_file(file_name)

            containers_steps.delete_folder(folder_name)
