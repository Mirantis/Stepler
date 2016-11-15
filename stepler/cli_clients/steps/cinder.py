"""
-----------------------
Cinder CLI client steps
-----------------------
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

from hamcrest import assert_that, is_  # noqa H301
from six import moves

from stepler.cli_clients.steps import base
from stepler import config
from stepler.third_party import output_parser
from stepler.third_party import steps_checker


class CliCinderSteps(base.BaseCliSteps):
    """CLI cinder client steps."""

    @steps_checker.step
    def create_volume(self, size=1, name=None, image=None, check=True):
        """Step to create volume using CLI.

        Args:
            size(int): size of created volume (in GB)
            name (str): name of created volume
            image (str): glance image name or ID to create volume from
            metadata(str): volume metadata
            check (bool): flag whether to check step or not

        Returns:
            dict: cinder volume
        """
        metadata = '{0}={1}'.format(config.STEPLER_PREFIX,
                                    config.STEPLER_PREFIX)
        cmd = 'cinder create ' + str(size) + ' --metadata ' + metadata
        if image:
            cmd += ' --image ' + image
        if name:
            cmd += ' --name ' + moves.shlex_quote(name)

        exit_code, stdout, stderr = self.execute_command(
            cmd, timeout=config.VOLUME_AVAILABLE_TIMEOUT, check=check)
        volume_table = output_parser.table(stdout)
        volume = {key: value for key, value in volume_table['values']}
        return volume

    @steps_checker.step
    def rename_volume(self, volume, name=None, description=None, check=True):
        """Step to change volume's name or description using CLI.

        Args:
            volume (object): cinder volume to edit
            name (str): new volume name
            description (str): new volume description
            check (bool): flag whether to check step or not
        """
        err_msg = 'One of `name` or `description` should be passed.'
        assert_that(any([name, description]), is_(True), err_msg)

        cmd = 'cinder rename'
        if description is not None:
            cmd += ' --description ' + moves.shlex_quote(description)
        cmd += ' ' + volume.id
        if name:
            cmd += ' ' + name

        self.execute_command(cmd,
                             timeout=config.VOLUME_AVAILABLE_TIMEOUT,
                             check=check)

    @steps_checker.step
    def create_volume_backup(self, volume, name=None, description=None,
                             container=None, check=True):
        """Step to create volume backup using CLI.

        Args:
            volume (object): cinder volume
            name (str): name of backup to create
            description (str): description
            container (str): name of the backup service container
            check (bool): flag whether to check step or not

        Returns:
            dict: cinder volume backup
        """
        cmd = 'cinder backup-create'
        if name:
            cmd += ' --name ' + name
        if description is not None:
            cmd += ' --description ' + moves.shlex_quote(description)
        if container:
            cmd += ' --container ' + container

        cmd += ' ' + volume.id

        exit_code, stdout, stderr = self.execute_command(
            cmd, timeout=config.BACKUP_AVAILABLE_TIMEOUT, check=check)

        backup_table = output_parser.table(stdout)
        backup = {key: value for key, value in backup_table['values']}

        return backup

    @steps_checker.step
    def show_volume_backup(self, backup, check=True):
        """Step to show volume backup using CLI.

        Args:
            backup (object): cinder volume backup object to show
            check (bool): flag whether to check step or not

        Raises:
            AssertionError: if check failed
        """
        cmd = 'cinder backup-show ' + backup.id

        exit_code, stdout, stderr = self.execute_command(
            cmd, timeout=config.BACKUP_SHOW_TIMEOUT, check=check)

        backup_table = output_parser.table(stdout)
        show_result = {key: value for key, value in backup_table['values']}

        if check:
            assert_that(show_result['id'], is_(backup.id))
            if backup.name:
                assert_that(show_result['name'], is_(backup.name))
            if backup.description:
                assert_that(show_result['description'],
                            is_(backup.description))
            if backup.container:
                assert_that(show_result['container'], is_(backup.container))

    @steps_checker.step
    def create_volume_snapshot(self, volume, name=None, description=None,
                               check=True):
        """Step to create volume snapshot using CLI.

        Args:
            volume (object): cinder volume
            name (str): name of snapshot to create
            description (str): snapshot description
            check (bool): flag whether to check step or not

        Returns:
            dict: cinder volume snapshot
        """
        cmd = 'cinder snapshot-create'
        if name:
            cmd += ' --name ' + name
        if description is not None:
            cmd += ' --description ' + moves.shlex_quote(description)

        cmd += ' ' + volume.id

        exit_code, stdout, stderr = self.execute_command(
            cmd, timeout=config.SNAPSHOT_AVAILABLE_TIMEOUT, check=check)

        snapshot_table = output_parser.table(stdout)
        snapshot = {key: value for key, value in snapshot_table['values']}

        return snapshot

    @steps_checker.step
    def show_volume_snapshot(self, snapshot, check=True):
        """Step to show volume snapshot using CLI.

        Args:
            snapshot (object): cinder volume snapshot object to show
            check (bool): flag whether to check step or not

        Raises:
            AssertionError: if check failed
        """
        cmd = 'cinder snapshot-show ' + snapshot.id

        exit_code, stdout, stderr = self.execute_command(
            cmd, timeout=config.SNAPSHOT_SHOW_TIMEOUT, check=check)

        snapshot_table = output_parser.table(stdout)
        show_result = {key: value for key, value in snapshot_table['values']}

        if check:
            assert_that(show_result['id'], is_(snapshot.id))
            if snapshot.name:
                assert_that(show_result['name'], is_(snapshot.name))
            if snapshot.description:
                assert_that(show_result['description'],
                            is_(snapshot.description))

    @steps_checker.step
    def create_volume_transfer(self, volume, name=None, check=True):
        """Step to create volume transfer using CLI.

        Args:
            volume (object): cinder volume
            name (str): name of transfer to create
            check (bool): flag whether to check step or not

        Returns:
            dict: cinder volume transfer
        """
        cmd = 'cinder transfer-create'
        if name:
            cmd += ' --name ' + name

        cmd += ' ' + volume.id

        exit_code, stdout, stderr = self.execute_command(
            cmd, timeout=config.TRANSFER_CREATE_TIMEOUT, check=check)

        transfer_table = output_parser.table(stdout)
        transfer = {key: value for key, value in transfer_table['values']}
        return transfer

    @steps_checker.step
    def show_volume_transfer(self, volume_transfer, check=True):
        """Step to show volume transfer using CLI.

        Args:
            volume_transfer (object): cinder volume transfer object to show
            check (bool): flag whether to check step or not

        Raises:
            AssertionError: if check failed
        """
        cmd = 'cinder transfer-show ' + volume_transfer.id

        exit_code, stdout, stderr = self.execute_command(
            cmd, timeout=config.TRANSFER_SHOW_TIMEOUT, check=check)

        transfer_table = output_parser.table(stdout)
        transfer_dict = {key: value for key, value in transfer_table['values']}

        if check:
            assert_that(transfer_dict['id'], is_(volume_transfer.id))
            if volume_transfer.name:
                assert_that(transfer_dict['name'], is_(volume_transfer.name))
