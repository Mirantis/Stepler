"""
---------------
Glance steps v2
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

from hamcrest import assert_that, empty, is_not, equal_to  # noqa
from waiting import wait

from stepler.third_party import steps_checker

from .base import BaseGlanceSteps

__all__ = [
    'GlanceStepsV2',
]


class GlanceStepsV2(BaseGlanceSteps):
    """Glance steps for v2."""

    @steps_checker.step
    def create_image(self, image_name, image_path, disk_format='qcow2',
                     container_format='bare', check=True):
        """Step to create image.

        Args:
            image_name (str): name of created image
            image_path (str): path to image at local machine
            disk_format (str): format of image disk
            container_format (str): format of image container
            check (bool): flag whether to check step or not

        Returns:
            object: glance image
        """
        images = self.create_images([image_name],
                                    image_path,
                                    disk_format,
                                    container_format,
                                    check)
        return images[0]

    @steps_checker.step
    def create_images(self, image_names, image_path, disk_format='qcow2',
                      container_format='bare', check=True):
        """Step to create images.

        Args:
            image_names (list): names of created images
            image_path (str): path to image at local machine
            disk_format (str): format of image disk
            container_format (str): format of image container
            check (bool): flag whether to check step or not

        Returns:
            list: glance images
        """
        images = []

        for image_name in image_names:
            image = self._client.images.create(
                name=image_name,
                disk_format=disk_format,
                container_format=container_format)
            self._client.images.upload(image.id, open(image_path, 'rb'))
            images.append(image)

        if check:
            for image in images:
                self.check_image_status(image, 'active', timeout=180)

        return images

    @steps_checker.step
    def delete_image(self, image, check=True):
        """Step to delete image.

        Args:
            image (object): glance image
            check (bool): flag whether to check step or not
        """
        self.delete_images([image], check)

    @steps_checker.step
    def delete_images(self, images, check=True):
        """Step to delete images.

        Args:
            image (object): glance image
            check (bool): flag whether to check step or not
        """
        for image in images:
            self._client.images.delete(image.id)

        if check:
            for image in images:
                self.check_image_presence(image, present=False, timeout=180)

    @steps_checker.step
    def bind_project(self, image, project, check=True):
        """Step to bind image to project.

        Args:
            image (object): image to bind to project
            project (object): project to bind to image
            check (bool): flag whether to check binding or not
        """
        self._client.image_members.create(image.id, project.id)
        if check:
            self.check_image_bind_status(image, project)

    @steps_checker.step
    def unbind_project(self, image, project, check=True):
        """Step to unbind image to project.

        Args:
            image (object): image to unbind from project
            project (object): project to unbind from image
            check (bool): flag whether to check unbinding or not
        """
        self._client.image_members.delete(image.id, project.id)
        if check:
            self.check_image_bind_status(image, project, binded=False)

    @steps_checker.step
    def get_images(self, name_prefix=None, check=True, **kwargs):
        """Step to retrieve images from glance.

        Args:
            name_prefix (str): name prefix to filter images
            check (bool): flag whether to check step or not
            **kwargs: like: {'name': 'TestVM', 'status': 'active'}

        Returns:
            list: images list

        Raises:
            AssertionError: if check triggered an error
        """
        images = list(self._client.images.list())

        if name_prefix:
            images = [image for image in images
                      if (image.name or '').startswith(name_prefix)]

        if kwargs:
            matched_images = []
            for image in images:
                for key, value in kwargs.items():
                    if not (key in image and image[key] == value):
                        break
                else:
                    matched_images.append(image)
            images = matched_images

        if check:
            assert_that(images, is_not(empty()))

        return images

    @steps_checker.step
    def get_image(self, check=True, **kwargs):
        """Find one image by provided **kwargs.

        Args:
            check (bool): flag whether to check step or not
            **kwargs: like: {'name': 'TestVM', 'status': 'active'}

        Returns:
            object: glance image

        Raises:
            ValueError: if '**kwargs' were not provided
        """
        if not kwargs:
            raise ValueError("Need to provide search criteria.")

        images = self.get_images(check=check, **kwargs)
        return images[0]

    @steps_checker.step
    def check_image_presence(self, image, present=True, timeout=0):
        """Check step image presence status.

        Args:
            image (object): glance image to check presence status
            presented (bool): flag whether image should present or no
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was failed after timeout
        """
        def predicate():
            try:
                self._client.images.get(image.id)
                return present
            except Exception:
                return not present

        wait(predicate, timeout_seconds=timeout)

    @steps_checker.step
    def check_image_status(self, image, status, timeout=0):
        """Check step image status.

        Args:
            image (object): glance image to check status
            status (str): image status name to check
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was failed after timeout
        """
        def predicate():
            image.update(self._client.images.get(image.id))
            return image.status.lower() == status.lower()

        wait(predicate, timeout_seconds=timeout)

    @steps_checker.step
    def check_image_bind_status(self, image, project, binded=True, timeout=0):
        """Check step image binding status.

        Args:
            image (object): image binded/unbinded with project
            project (object): project binded/unbinded with image
            binded (bool): flag whether project and image should be binded or
                           unbinded
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was failed after timeout
        """
        def predicate():
            members = self._client.image_members.list(image.id)
            member_ids = [member['member_id'] for member in members]

            if binded:
                return project.id in member_ids
            else:
                return project.id not in member_ids

        wait(predicate, timeout_seconds=timeout)

    @steps_checker.step
    def check_image_container_and_disk_format(self,
                                              image_name,
                                              image_container,
                                              disk_format):
        """Check image container format and disk format.

        Args:
            image (object): image binded/unbinded with project
            image_container (str): type of image container
            disk_format (str): type of disk format

        Raises:
            AssertionError: if check was failed
        """
        image = self.get_image(name=image_name)
        assert_that(image['container_format'], equal_to(image_container))
        assert_that(image['disk_format'], equal_to(disk_format))

    @steps_checker.step
    def check_that_image_id_is_changed(self, image_name, image_id):
        """Step to check that after updating heat stack image_id was changed

        Args:
            image_id (str): befor updating
            image_name (str): image name that was replaced

        Raises:
            AssertionError: if check was failed
        """
        image_id_changed = self.get_image(name=image_name)['id']
        assert_that(image_id_changed, is_not(image_id))