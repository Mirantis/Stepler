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
                                       volumes_steps):
        """Verify that volume backups pagination works right and back."""
        backup_names = list(generate_ids('backup', count=3))
        create_backups(backup_names)
        update_settings(items_per_page=1)
        volumes_steps.check_backups_pagination(backup_names)
