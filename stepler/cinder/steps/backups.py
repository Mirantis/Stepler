"""
------------
Backup steps
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
from hamcrest import assert_that, calling, equal_to, raises  # noqa

from stepler import base
from stepler import config
from stepler.third_party.matchers import expect_that
from stepler.third_party import steps_checker
from stepler.third_party import waiter

__all__ = ['BackupSteps']


class BackupSteps(base.BaseSteps):
    """Backup steps."""

    @steps_checker.step
    def create_backup(self,
                      volume,
                      name=None,
                      container=None,
                      description=None,
                      snapshot_id=None,
                      check=True):
        """Step to create volume backup.

        Args:
            volume (object): cinder volume
            name (str): name of created backup
            container (str): name of the backup service container
            description (str): description
            snapshot_id (str): id of snapshot created from volume
            check (bool): flag whether to check step or not

        Returns:
            object: volume backup

        Raises:
            TimeoutExpired: if backup is not available after timeout
            AssertionError: if backup attributes are not the same as ones
                entered during creation
        """
        backup = self._client.create(volume.id,
                                     name=name,
                                     container=container,
                                     description=description,
                                     snapshot_id=snapshot_id)

        if check:
            self.check_backup_status(backup,
                                     config.STATUS_AVAILABLE,
                                     timeout=config.BACKUP_AVAILABLE_TIMEOUT)
            assert_that(backup.volume_id, equal_to(volume.id))
            if name:
                assert_that(backup.name, equal_to(name))
            if description:
                assert_that(backup.description, equal_to(description))
            if container:
                assert_that(backup.container, equal_to(container))
            if snapshot_id:
                assert_that(backup.snapshot_id, equal_to(snapshot_id))

        return backup

    @steps_checker.step
    def check_backup_status(self, backup, status, timeout=0):
        """Check step volume backup status.

        Args:
            backup (object): volume backup to check status
            status (str): backup status name to check
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was failed after timeout
        """

        def predicate():
            backup.get()
            return expect_that(backup.status.lower(), equal_to(status.lower()))

        waiter.wait(predicate, timeout_seconds=timeout)

    @steps_checker.step
    def check_backup_not_created_with_long_container_name(self, volume,
                                                          container):
        """Step to check that backup is not created with overlimit container
            name length.

        Args:
            volume (obj): cinder volume
            container (str): container name

        Raises:
            AssertionError: if no BadRequest occurs or exception message is
                unexpected
        """
        exception_message = "Backup container has more than 255 characters"

        assert_that(
            calling(self.create_backup).with_args(
                volume, container=container, check=False),
            raises(exceptions.BadRequest, exception_message))

    @steps_checker.step
    def delete_backup(self, backup, check=True):
        """Step to delete volume backup.

        Args:
            backup (object): volume backup
            check (bool): flag whether to check step or not
        """
        self._client.delete(backup)

        if check:
            self.check_backup_presence(backup,
                                       must_present=False,
                                       timeout=config.BACKUP_DELETE_TIMEOUT)

    @steps_checker.step
    def check_backup_presence(self, backup, must_present=True, timeout=0):
        """Check step volume backup presence status.

        Args:
            backup (object): volume backup to check presence status
            must_present (bool): flag whether volume should present or not
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutExpired: if check was failed after timeout
        """

        def predicate():
            try:
                self._client.get(backup.id)
                is_present = True
            except exceptions.NotFound:
                is_present = False
            return expect_that(is_present, equal_to(must_present))

        waiter.wait(predicate, timeout_seconds=timeout)