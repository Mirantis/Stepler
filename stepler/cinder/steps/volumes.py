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
from hamcrest import (assert_that, calling, empty, equal_to, has_entries,
                      has_properties, has_property, is_in, is_not, raises)  # noqa

from stepler import base
from stepler import config
from stepler.third_party.matchers import expect_that
from stepler.third_party import steps_checker
from stepler.third_party import utils
from stepler.third_party import waiter

__all__ = ['VolumeSteps']


class VolumeSteps(base.BaseSteps):
    """Volume steps."""

    @steps_checker.step
    def check_volume_not_created_with_long_name(self, name):
        """Step to check volume is not created with long name.

        Args:
            name (str): name for volume. Expected long name in argument

        Raises:
            AssertionError: if check triggered an error
        """
        exception_message = "Name has more than 255 characters"

        assert_that(
            calling(self.create_volumes).with_args(
                names=[name], check=False),
            raises(exceptions.BadRequest, exception_message))

    @steps_checker.step
    def check_volume_not_created_with_non_exist_volume_type(self, image):
        """Step to check volume is not created with non-existed volume type.

        Args:
            image (obj): image for volume creation

        Raises:
            AssertionError: if check triggered an error
        """
        type_name = next(utils.generate_ids('volume_type'))
        exception_message = ("Volume type with name {0} could not be found"
                             .format(type_name))

        assert_that(
            calling(self.create_volumes).with_args(
                names=[None], volume_type=type_name, image=image, check=False),
            raises(exceptions.NotFound, exception_message))

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

        Raises:
            TimeoutExpired|AssertionError: if check was falsed
        """
        image_id = None if image is None else image.id
        volumes = []
        for name in names:
            volume = self._client.volumes.create(size,
                                                 name=name,
                                                 imageRef=image_id,
                                                 volume_type=volume_type,
                                                 description=description,
                                                 snapshot_id=snapshot_id)
            volumes.append(volume)

        if check:
            for volume in volumes:
                self.check_volume_status(
                    volume,
                    config.STATUS_AVAILABLE,
                    transit_statuses=(config.STATUS_CREATING,
                                      config.STATUS_DOWNLOADING,
                                      config.STATUS_UPLOADING),
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

        return volumes

    @steps_checker.step
    def delete_volumes(self, volumes, check=True):
        """Step to delete volumes.

        Args:
            volumes (list): cinder volumes
            check (bool): flag whether to check step or not
        """
        for volume in volumes:
            self._client.volumes.delete(volume.id)

        if check:
            for volume in volumes:
                self.check_volume_presence(
                    volume,
                    must_present=False,
                    timeout=config.VOLUME_DELETE_TIMEOUT)

    @steps_checker.step
    def check_volume_presence(self, volume, must_present=True, timeout=0):
        """Check step volume presence status.

        Args:
            volume (object): cinder volume to check presence status
            present (bool): flag whether volume should present or not
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was falsed after timeout
        """
        def _check_volume_presence():
            try:
                self._client.volumes.get(volume.id)
                is_present = True
            except exceptions.NotFound:
                is_present = False
            return expect_that(is_present, equal_to(must_present))

        waiter.wait(_check_volume_presence, timeout_seconds=timeout)

    @steps_checker.step
    def check_volume_status(self, volume, status, transit_statuses=(),
                            timeout=0):
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
            return expect_that(volume.status.lower(),
                               is_not(is_in(transit_statuses)))

        waiter.wait(predicate, timeout_seconds=timeout)
        assert_that(volume.status.lower(), equal_to(status.lower()))

    @steps_checker.step
    def get_volumes(self, name_prefix=None, check=True):
        """Step to retrieve volumes.

        Args:
            check (bool): flag whether to check step or not

        Returns:
            list: volume list

        Raises:
            AssertionError: if check was falsed
        """
        volumes = self._client.volumes.list()

        if name_prefix:
            volumes = [volume for volume in volumes
                       if (volume.name or '').startswith(name_prefix)]

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
    def get_servers_attached_to_volume(self, volume):
        """Step to retrieve server_ids attached to volume.

        Args:
            volume (object): cinder volume

        Returns:
            list: attached servers' ids
        """
        volume.get()
        return [a['server_id'] for a in volume.attachments]

    @steps_checker.step
    def check_volume_type(self, volume, volume_type, timeout=0):
        """Step to check volume size.

        Args:
            volume (object): cinder volume
            volume_type (obj): expected volume type
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was falsed after timeout
        """
        def predicate():
            volume.get()
            return expect_that(volume.volume_type, equal_to(volume_type.name))

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
            attached_ids = self.get_servers_attached_to_volume(volume)
            return expect_that(set(attached_ids), equal_to(set(server_ids)))

        waiter.wait(predicate, timeout_seconds=timeout)

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
    def check_volume_not_created_with_incorrect_size(self, size):
        """Step to check negative volume creation with negative/zero size.

        Args:
            size (int): volume size

        Raises:
            AssertionError: if check was triggered to an error
        """
        error_message = 'must be an integer.+greater than (?:0|zero)'
        assert_that(
            calling(self.create_volumes).with_args(
                names=[None], size=size, check=False),
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

    @steps_checker.step
    def set_volume_bootable(self, volume, bootable, check=True):
        """Step to set volume bootable.

        Args:
            volume (object): cinder volume
            bootable (bool): flag whether to set or unset volume bootable
            check (bool): flag whether to check step or not

        Raises:
            AssertionError: if check was falsed
        """
        if bootable:
            bootable = 'true'
        else:
            bootable = 'false'
        self._client.volumes.set_bootable(volume, bootable)

        if check:
            volume.get()
            assert_that(volume, has_property('bootable', bootable))

    @steps_checker.step
    def change_volume_type(self, volume, volume_type, policy, check=True):
        """Step to retype volume.

        Args:
            volume (object): cinder volume
            volume_type (object): cinder volume type
            policy (str): policy for migration during the retype
            check (bool): flag whether to check step or not

        Raises:
            TimeoutExpired: if check was falsed after timeout
        """
        self._client.volumes.retype(volume, volume_type.name, policy)

        if check:
            self.check_volume_type(volume, volume_type,
                                   timeout=config.VOLUME_RETYPE_TIMEOUT)
