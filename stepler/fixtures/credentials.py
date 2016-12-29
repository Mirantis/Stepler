"""
--------------------
Credentials fixtures
--------------------
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
import pytest

from stepler import config
from stepler.third_party import context

__all__ = [
    'credentials',
]


class CredentialsManager(object):

    default = attrdict.AttrDict({
        'username': config.USERNAME,
        'password': config.PASSWORD,
        'project_name': config.PROJECT_NAME,
        'user_domain_name': config.USER_DOMAIN_NAME,
        'project_domain_name': config.PROJECT_DOMAIN_NAME,
    })

    def __init__(self, **creds_dict):
        self._current_alias = 'default'
        self._creds = {}
        for alias, creds in creds_dict.items():
            self.add(alias, creds)

    def __getattr__(self, name):
        current = self._creds.get(self.current_alias) or self.default
        return current.get(name, self.default[name])

    def add(self, alias, creds):
        assert alias not in self._creds and alias != 'default'
        self._creds[alias] = creds

    def get(self, alias):
        if alias in self._creds or alias == 'default':
            return self._creds[alias]
        return None

    def remove(self, alias):
        assert alias != self._current_alias and alias != 'default'
        del self._creds[alias]

    def set_current(self, alias):
        assert alias in self._creds or alias == 'default'
        if alias != self._current_alias:
            self._current_alias = alias

    @context.context
    def change(self, alias):
        initial_alias = self.current_alias
        self.set_current(alias)
        yield
        self.set_current(initial_alias)

    @property
    def current_alias(self):
        assert self._current_alias
        return self._current_alias


@pytest.fixture(scope='session')
def credentials():
    """Function fixture to create CredentialsManager instance.

    Returns:
        object: CredentialsManager instance
    """
    return CredentialsManager()
