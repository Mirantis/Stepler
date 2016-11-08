"""
-----------------------
Glance CLI client steps
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

import hashlib
import os
import os.path
import tempfile

from hamcrest import assert_that, contains_string, equal_to, empty, is_  # noqa
from six import moves

from stepler.cli_clients.steps import base
from stepler.third_party import output_parser
from stepler.third_party import steps_checker


class CliGlanceSteps(base.BaseCliSteps):
    """CLI glance client steps."""

    @steps_checker.step
    def create_image(self, image_file, disk_format, container_format,
                     image_name=None, api_version=2, check=True):
        """Step to create image.

        Args:
            image_file (str): image file to be uploaded
            image_name (str): name of created image
            disk_format (str): disk format of image
            container_format (str): container format of image
            api_version (int): API version of Glance
            check (bool): flag whether to check result or not

        Returns:
            tuple: execution result (image dict, exit_code, stdout, stderr)

        Raises:
            AnsibleExecutionException: if command execution failed
        """
        image = None
        cmd = 'glance image-create'
        if image_file:
            cmd += ' --file ' + moves.shlex_quote(image_file)
        if image_name:
            cmd += ' --name ' + moves.shlex_quote(image_name)
        if disk_format:
            cmd += ' --disk-format ' + disk_format
        if container_format:
            cmd += ' --container-format ' + container_format

        exit_code, stdout, stderr = self.execute_command(
            cmd, environ={'OS_IMAGE_API_VERSION': api_version},
            check=check)

        if check:
            image_table = output_parser.table(stdout)
            image = {key: value for key, value in image_table['values']}

        return image, exit_code, stdout, stderr

    @steps_checker.step
    def check_negative_image_create_without_properties(self, filename,
                                                       api_version=2):
        """Step to check image is not created from file without properties.

        Args:
            filename (str): filename (doesn't matter if it exists or not)
            api_version (int): glance api version (1 or 2). Default is 2

        Raises:
            AssertionError: if command exit code is not 1 or stderr doesn't
                contain expected message
        """
        error_message = ("Must provide --container-format, "
                         "--disk-format when using --file.")
        image, exit_code, stdout, stderr = self.create_image(
            image_file=filename,
            disk_format=None,
            container_format=None,
            api_version=api_version,
            check=False)
        assert_that(exit_code, equal_to(1))
        assert_that(stderr, contains_string(error_message))

    @steps_checker.step
    def create_file(self, size=0):
        """Step to create file.

        Args:
            size (int): file size in MB
        """
        temp = tempfile.NamedTemporaryFile()
        temp.write(os.urandom(size * 1024))
        temp.close()
        return temp.name

    @steps_checker.step
    def get_image_id(self, name):
        """Step to create image.
        """
        cmd = ("glance image-create --name Test --container-format bare "
               "--disk-format qcow2 --file {0} | "
               "grep id |awk ' {print $4} ' ").format(name)
        result = self.execute_command(cmd)
        return result

    @steps_checker.step
    def download_image(self, uploaded_image_id, downloaded_image_name):
        """Step to download image.
        """
        cmd = 'glance image-download {0} > {1}'.format(
            uploaded_image_id, downloaded_image_name)
        result = self.execute_command(cmd)
        return result

    @steps_checker.step
    def md5_sum(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @steps_checker.step
    def delete_image(self, image_id, check=True):
        """Step to delete image.
        """
        cmd = 'glance image-delete {}'.format(image_id)
        result = self.execute_command(cmd, check=check)
        if check:
            assert_that(result, is_(empty()))

    @steps_checker.step
    def delete_file(self, name_file):
        """Step to delete file.
        """
        if os.path.exists(name_file) is True:
            os.remove(name_file)
        else:
            return False
