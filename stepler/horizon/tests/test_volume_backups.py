"""
-------------------
Volume backup tests
-------------------
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

from stepler.horizon.utils import generate_ids


@pytest.mark.usefixtures('any_one')
class TestAnyOne(object):
    """Tests for any user."""

    @pytest.mark.idempotent_id('7f43197f-ba2c-4962-a07a-43cbf77a779b')
    def test_volume_backups_pagination(self, create_backups, update_settings,
                                       volumes_steps_ui):
        """Verify that volume backups pagination works right and back."""
        backup_names = list(generate_ids('backup', count=3))
        create_backups(backup_names)
        update_settings(items_per_page=1)
        volumes_steps_ui.check_backups_pagination(backup_names)

    @pytest.mark.idempotent_id('dd3abd5c-0900-40a0-be3d-b284eeb6b5da')
    def test_create_volume_backup(self, create_backups):
        """**Scenario:** Create volume backup.

        **Setup:**

        #. Create volume

        **Steps:**

        #. Create backup
        #. Check that backup is created

        **Teardown:**

        #. Delete backup
        #. Delete volume
        """
        backup_name = next(generate_ids('backup'))
        create_backups([backup_name])

    @pytest.mark.idempotent_id('acf12ae6-7b00-4bad-aef4-25ca3e3c3dc0')
    def test_volume_backup_form_max_name_length(self, volume,
                                                volumes_steps_ui):
        """**Scenario:** Create volume backup with name lenght > 255.

        **Setup:**

        #. Create volume

        **Steps:**

        #. Open backup creation form
        #. Check that backup name input can't contains more than 255 symbols

        **Teardown:**

        #. Delete volume
        """
        volumes_steps_ui.check_backup_creation_form_name_field_max_length(
            volume.name, 255)

    @pytest.mark.idempotent_id('42020f62-06d5-49f5-8b78-08d40b518b17')
    def test_create_volume_backup_with_description(self, create_backups):
        """**Scenario:** Create volume backup with description.

        **Setup:**

        #. Create volume

        **Steps:**

        #. Create backup with description
        #. Check that backup is created
        #. Check that backup description is correct

        **Teardown:**

        #. Delete backup
        #. Delete volume
        """
        backup_name = next(generate_ids('backup'))
        backup_description = next(generate_ids('backup', length=30))
        create_backups([backup_name], description=backup_description)

    @pytest.mark.idempotent_id('36a02ea4-ce4d-4f45-b461-954ded1ea171')
    def test_create_volume_backup_with_max_length_description(self,
                                                              create_backups):
        """**Scenario:** Create volume backup with description lenght == max

        **Setup:**

            #. Create volume

        **Steps:**

            #. Create backup with long (255 symbols) description
            #. Check that backup is created
            #. Check that backup description is correct

        **Teardown:**

            #. Delete backup
            #. Delete volume
        """
        backup_name = next(generate_ids('backup'))
        backup_description = next(generate_ids('backup', length=255))
        create_backups([backup_name], description=backup_description)