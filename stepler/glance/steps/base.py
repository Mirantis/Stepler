"""
-----------------
Glance base steps
-----------------
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

from hamcrest import assert_that, equal_to  # noqa

from stepler import base
from stepler.third_party import steps_checker

__all__ = [
    'BaseGlanceSteps',
]


class BaseGlanceSteps(base.BaseSteps):
    """Glance base steps."""

    @steps_checker.step
    def update_images(self, images, status=None, check=True, **kwargs):
        """Step to update images.

        Args:
            images (object): glance images
            status (str): status of image for assertion
            check (bool): flag whether to check step or not
            **kwargs: like: {'name': 'TestVM'}

        Raises:
            AssertionError: if expected status not equal to actual status
        """
        for image in images:
            self._client.images.update(image.id, **kwargs)

        if check:
            for image in images:
                image.get(image.id)
                if status:
                    assert_that(image.status, equal_to(status))
