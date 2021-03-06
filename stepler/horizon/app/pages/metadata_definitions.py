"""
-------------------------
Metadata definitions page
-------------------------
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

from pom import ui
from selenium.webdriver.common.by import By

from stepler.horizon.app import ui as _ui

from .base import PageBase


@ui.register_ui(
    checkbox=_ui.CheckBox(By.CSS_SELECTOR, 'input[type="checkbox"]'),
    dropdown_menu=_ui.DropdownMenu())
class RowNamespace(_ui.Row):
    """Row with namespace in namespaces table."""


class TableNamespaces(_ui.Table):
    """Namespaces table."""

    columns = {'name': 2}
    row_cls = RowNamespace


@ui.register_ui(
    field_namespace_json=ui.TextField(By.NAME, 'direct_input'),
    combobox_namespace_source=_ui.combobox_by_label(
        "Namespace Definition Source"))
class FormImportNamespace(_ui.Form):
    """Form to create namespace."""


class FormConfirmDeleteNamespace(_ui.Form):
    """Form delete metadata confirmation."""

    submit_locator = By.CSS_SELECTOR, '.btn.btn-danger'


@ui.register_ui(
    button_import_namespace=ui.Button(By.ID, 'namespaces__action_import'),
    button_filter_namespaces=ui.Button(By.ID, 'namespaces__action_filter'),
    field_filter_namespaces=ui.TextField(By.NAME, 'namespaces__filter__q'),
    form_import_namespace=FormImportNamespace(By.ID, 'create_metadata_form'),
    form_confirm_delete_namespace=FormConfirmDeleteNamespace(
        By.CSS_SELECTOR,
        'div.modal-content'),
    table_namespaces=TableNamespaces(By.ID, 'namespaces'))
class PageMetadataDefinitions(PageBase):
    """Metadata definitions page."""

    url = "/admin/metadata_defs/"
    navigate_items = 'Admin', 'System', 'Metadata Definitions'
