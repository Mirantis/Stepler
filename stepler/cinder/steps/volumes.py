"""
------------
Volume steps
------------
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

from cinderclient import exceptions
from hamcrest import (assert_that, calling, empty, equal_to,
                      has_entries, has_properties, is_not, raises)   # noqa
import waiting

from stepler import base
from stepler import config
from stepler.third_party.matchers import expect_that
from stepler.third_party import steps_checker
from stepler.third_party import waiter

__all__ = ['VolumeSteps']


class VolumeSteps(base.BaseSteps):
    """Volume steps."""

    @steps_checker.step
    def create_volume(self,
                      name=None,
                      size=1,
                      image=None,
                      volume_type=None,
                      description=None,
                      snapshot_id=None,
                      check=True):
        """Step to create volume.

        Args:
            name (str): name of created volume
            size (int): size of created volume (in GB)
            image (object): glance image to create volume from
            volume_type (str): type of volume
            description (str): description
            snapshot_id (str): ID of the snapshot
            check (bool): flag whether to check step or not

        Returns:
            object: cinder volume

        Raises:
            TimeoutExpired|AssertionError: if check was falsed
        """
        image_id = None if image is None else image.id
        volume = self._client.volumes.create(size,
                                             name=name,
                                             imageRef=image_id,
                                             volume_type=volume_type,
                                             description=description,
                                             snapshot_id=snapshot_id)
        if check:
            self.check_volume_status(volume,
                                     config.STATUS_AVAILABLE,
                                     timeout=config.VOLUME_AVAILABLE_TIMEOUT)
            if snapshot_id:
                assert_that(volume.snapshot_id, equal_to(snapshot_id))
            if name:
                assert_that(volume.name, equal_to(name))
            if size:
                assert_that(volume.size, equal_to(size))
            if volume_type:
                assert_that(volume.volume_type, equal_to(volume_type))
            if description:
                assert_that(volume.description, equal_to(description))

        return volume

    @steps_checker.step
    def check_negative_volume_not_created(self, name):
        """Step for negative test case of volume creation with invalid name.

        Args:
            name (str): name for volume. Expected invalid name in argument

        Raises:
            AssertionError: if check triggered an error
        """
        exception_message = "Name has more than 255 characters"

        assert_that(
            calling(self.create_volume).with_args(
                name=name, check=False),
            raises(exceptions.BadRequest, exception_message))

    @steps_checker.step
    def create_volumes(self,
                       names,
                       size=1,
                       image=None,
                       volume_type=None,
                       description=None,
                       snapshot_id=None,
                       check=True):
        """Step to create volumes.

        Args:
            names (list): names of created volume
            size (int): size of created volume (in GB)
            image (object): glance image to create volume from
            volume_type (str): type of volume
            description (str): description
            snapshot_id (str): ID of the snapshot
            check (bool): flag whether to check step or not

        Returns:
            list: cinder volumes
        """
        volumes = []
        for name in names:
            volume = self.create_volume(name=name,
                                        size=size,
                                        image=image,
                                        volume_type=volume_type,
                                        description=description,
                                        snapshot_id=snapshot_id,
                                        check=False)
            volumes.append(volume)

        if check:

            for volume in volumes:
                self.check_volume_status(
                    volume,
                    config.STATUS_AVAILABLE,
                    timeout=config.VOLUME_AVAILABLE_TIMEOUT)

        return volumes

    @steps_checker.step
    def detach_volumes(self, volumes, check=True):
        """Step to detach volumes.

        Args:
            volumes (list): cinder volumes
            check (bool): flag whether to check step or not

        Raises:
            AssertionError: if some attachments are present
        """
        for volume in volumes:
            self._client.volumes.detach(volume.id)

        if check:
            for volume in volumes:
                volume.get()
                assert_that(volume.attachments, empty())

    @steps_checker.step
    def delete_volume(self, volume, check=True):
        """Step to delete volume.

        Args:
            volume (object): cinder volume
            check (bool): flag whether to check step or not
        """
        self._client.volumes.delete(volume.id)

        if check:
            self.check_volume_presence(volume,
                                       present=False,
                                       timeout=config.VOLUME_DELETE_TIMEOUT)

    @steps_checker.step
    def delete_volumes(self, volumes, check=True):
        """Step to delete volumes.

        Args:
            volumes (list): cinder volumes
            check (bool): flag whether to check step or not
        """
        for volume in volumes:
            self.delete_volume(volume, check=False)

        if check:
            for volume in volumes:
                self.check_volume_presence(
                    volume,
                    present=False,
                    timeout=config.VOLUME_DELETE_TIMEOUT)

    @steps_checker.step
    def check_volume_presence(self, volume, present=True, timeout=0):
        """Check step volume presence status.

        Args:
            volume (object): cinder volume to check presence status
            present (bool): flag whether volume should present or not
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was falsed after timeout
        """

        def predicate():
            try:
                self._client.volumes.get(volume.id)
                return present
            except exceptions.NotFound:
                return not present

        waiting.wait(predicate, timeout_seconds=timeout)

    @steps_checker.step
    def check_volume_status(self, volume, status, timeout=0):
        """Check step volume status.

        Args:
            volume (object): cinder volume to check status
            status (str): volume status name to check
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was falsed after timeout
        """

        def predicate():
            volume.get()
            return volume.status.lower() == status.lower()

        waiting.wait(predicate, timeout_seconds=timeout)

    @steps_checker.step
    def get_volumes(self, check=True):
        """Step to retrieve volumes.

        Args:
            check (bool): flag whether to check step or not

        Returns:
            list: volume list

        Raises:
            AssertionError: if check was falsed
        """
        volumes = self._client.volumes.list()
        if check:
            assert_that(volumes, is_not(empty()))
        return volumes

    @steps_checker.step
    def check_volume_size(self, volume, size, timeout=0):
        """Step to check volume size.

        Args:
            volume (object): cinder volume
            size (int): expected volume size
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was falsed after timeout
        """
        def predicate():
            volume.get()
            return expect_that(volume.size, equal_to(size))

        waiter.wait(predicate, timeout_seconds=timeout)

    @steps_checker.step
    def check_volume_attachments(self, volume, server_ids=None, timeout=0):
        """Step to check volume attachments.

        Args:
            volume (object): cinder volume
            server_ids (list): list of nova servers ids
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was falsed after timeout
        """
        server_ids = server_ids or []

        def predicate():
            volume.get()
            attached_ids = [a['server_id'] for a in volume.attachments]
            return sorted(server_ids) == sorted(attached_ids)

        waiting.wait(predicate, timeout_seconds=timeout)

    @steps_checker.step
    def check_volume_extend_failed_incorrect_size(self, volume, size):
        """Step to check negative volume extend to incorrect size.

        Args:
            volume (object): cinder volume
            size (int): volume size

        Raises:
            AssertionError: if check was falsed after timeout
        """
        error_message = 'New size for extend must be greater than current size'
        assert_that(
            calling(self.volume_extend).with_args(volume, size, check=False),
            raises(exceptions.BadRequest, error_message))

    @steps_checker.step
    def check_negative_volume_creation_incorrect_size(self, size):
        """Step to check negative volume creation with negative/zero size

        Args:
            size (int): volume size

        Raises:
            AssertionError: if check was triggered to an error
        """
        error_message = 'must be an integer.+greater than (?:0|zero)'
        assert_that(
            calling(self.create_volume).with_args(size=size, check=False),
            raises(exceptions.BadRequest, error_message))

    @steps_checker.step
    def check_volume_extend_failed_size_more_than_limit(self, volume, size):
        """Step to check negative volume extend to size more than limit.

        Args:
            volume (object): cinder volume
            size (int): volume size

        Raises:
            AssertionError: if check was falsed after timeout
        """
        error_message = (
            "VolumeSizeExceedsAvailableQuota: "
            "Requested volume or snapshot exceeds allowed gigabytes quota.")
        assert_that(
            calling(self.volume_extend).with_args(volume, size, check=False),
            raises(exceptions.OverLimit, error_message))

    @steps_checker.step
    def volume_upload_to_image(self, volume, image_name,
                               force=False, container_format='bare',
                               disk_format='raw', check=True):
        """Step to upload volume to image.

        Args:
            volume (str): The :class:`Volume` to upload
            image_name (str): The new image name
            force (bool): Enables or disables upload of a volume that is
            attached to an instance
            container_format (str): Container format type
            disk_format (str): Disk format type
            check (bool): flag whether to check step or not

        Raises:
            AssertionError: if check was triggered to False

        Returns:
            object: image
        """
        response, image = self._client.volumes.upload_to_image(
            volume=volume,
            force=force,
            image_name=image_name,
            container_format=container_format,
            disk_format=disk_format)

        if check:
            assert_that(response.status_code, equal_to(202))
            assert_that(image['os-volume_upload_image'], has_entries({
                'container_format': container_format,
                'disk_format': disk_format,
                'image_name': image_name,
                'id': volume.id,
                'size': volume.size
            }))

        return image

    @steps_checker.step
    def volume_extend(self, volume, size, check=True):
        """Step to extend volume to new size.

        Args:
            volume (object): cinder volume
            size (int): The new volume size
            check (bool): flag whether to check step or not

        Raises:
            TimeoutExpired: if check was falsed after timeout
        """
        self._client.volumes.extend(volume, size)

        if check:
            self.check_volume_size(volume, size,
                                   timeout=config.VOLUME_AVAILABLE_TIMEOUT)

    @steps_checker.step
    def update_volume(self, volume, new_name=None,
                      new_description=None, check=True):
        """Step to update volume.

        Args:
            volume (object): cinder volume
            new_name (str); new name for volume
            new_description (str): new description for volume
            check (bool): flag whether to check step or not

        Raises:
            AssertionError: if check was falsed
        """
        update_data = {}
        if new_name:
            update_data['name'] = new_name
        if new_description:
            update_data['description'] = new_description
        self._client.volumes.update(volume, **update_data)

        if check:
            volume.get()
            assert_that(volume, has_properties(update_data))

    @steps_checker.step
    def check_volume_update_failed(self, volume, new_name=None,
                                   new_description=None):
        """Step to check negative volume update.

        Args:
            volume (object): cinder volume
            new_name (str): new name for volume
            new_description(str): new description for volume

        Raises:
            BadRequest: if check was falsed
        """
        assert_that(
            calling(
                self.update_volume).with_args(volume, new_name=new_name,
                                              new_description=new_description,
                                              check=False),
            raises(exceptions.BadRequest))
