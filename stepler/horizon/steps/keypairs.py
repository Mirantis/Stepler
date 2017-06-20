"""
--------------
Keypairs steps
--------------
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

from hamcrest import (assert_that, equal_to)  # noqa

from stepler.horizon.steps import base
from stepler.third_party import steps_checker
from stepler.third_party import utils


class KeypairsSteps(base.BaseSteps):
    """Keypairs steps."""

    def _tab_keypairs(self):
        """Open keypairs tab."""
        with self._open(self.app.page_access) as page:
            page.label_keypairs.click()
            return page.tab_keypairs

    @steps_checker.step
    def create_keypair(self, keypair_name=None, check=True):
        """Step to create keypair."""
        keypair_name = keypair_name or next(utils.generate_ids('keypair'))

        tab_keypairs = self._tab_keypairs()
        tab_keypairs.button_create_keypair.click()

        with tab_keypairs.form_create_keypair as form:
            form.field_name.value = keypair_name
            form.submit()

        if check:
            self._tab_keypairs().table_keypairs.row(
                name=keypair_name).wait_for_presence()

        return keypair_name

    @steps_checker.step
    def delete_keypair(self, keypair_name, check=True):
        """Step to delete keypair."""
        tab_keypairs = self._tab_keypairs()

        tab_keypairs.table_keypairs.row(
            name=keypair_name).button_delete_keypair.click()
        tab_keypairs.form_confirm.submit()

        if check:
            self.close_notification('success')
            tab_keypairs.table_keypairs.row(
                name=keypair_name).wait_for_absence()

    @steps_checker.step
    def import_keypair(self, keypair_name, public_key, check=True):
        """Step to import keypair."""
        tab_keypairs = self._tab_keypairs()
        tab_keypairs.button_import_keypair.click()

        with tab_keypairs.form_import_keypair as form:
            form.field_name.value = keypair_name
            form.field_public_key.value = public_key
            form.submit()

        if check:
            self.close_notification('success')
            tab_keypairs.table_keypairs.row(
                name=keypair_name).wait_for_presence()

    @steps_checker.step
    def delete_keypairs(self, keypair_names, check=True):
        """Step to delete keypairs."""
        tab_keypairs = self._tab_keypairs()

        for keypair_name in keypair_names:
            tab_keypairs.table_keypairs.row(
                name=keypair_name).checkbox.select()

        tab_keypairs.button_delete_keypairs.click()
        tab_keypairs.form_confirm.submit()

        if check:
            self.close_notification('success')
            for keypair_name in keypair_names:
                tab_keypairs.table_keypairs.row(
                    name=keypair_name).wait_for_absence()

    @steps_checker.step
    def check_button_import_key_pair_disabled(self):
        """Step to check `import Key Pair` disabled if quota exceeded."""
        tab_keypairs = self._tab_keypairs()
        assert_that(
            tab_keypairs.button_import_keypair.is_enabled, equal_to(False))
