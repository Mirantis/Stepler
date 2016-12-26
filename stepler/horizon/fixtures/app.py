"""
-----------------------------------------------------
Fixtures to run horizon, login, create demo user, etc
-----------------------------------------------------
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

from stepler.horizon.app import Horizon
from stepler.horizon.steps import AuthSteps

from stepler import config

__all__ = [
    'auth_steps',
    'horizon',
    'login'
]


@pytest.yield_fixture
def horizon():
    """Initial fixture to start."""
    app = Horizon(config.OS_DASHBOARD_URL)
    yield app
    app.quit()


@pytest.fixture
def auth_steps(horizon):
    """Get auth steps to login or logout in horizon."""
    return AuthSteps(horizon)


@pytest.yield_fixture
def login(auth_steps):
    """Login to horizon.

    Majority of tests requires user login. Logs out after test.
    """
    assert config.CURRENT_UI_USERNAME
    assert config.CURRENT_UI_PASSWORD
    assert config.CURRENT_UI_PROJECT_NAME

    auth_steps.login(config.CURRENT_UI_USERNAME, config.CURRENT_UI_PASSWORD)
    auth_steps.switch_project(config.CURRENT_UI_PROJECT_NAME)

    yield
    # reload page to be sure that modal form doesn't prevent to logout
    auth_steps.app.current_page.refresh()
    auth_steps.logout()
