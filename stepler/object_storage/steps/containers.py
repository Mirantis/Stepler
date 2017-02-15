"""
------------------------------
Object Storage container steps
------------------------------
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

from hamcrest import (assert_that, empty, is_in, is_not, has_items,
                      has_entries, equal_to)  # noqa H301

from stepler import base
from stepler.third_party import steps_checker
from stepler.third_party import utils

__all__ = ['ContainerSwiftSteps', 'ContainerCephSteps']


class ContainerSwiftSteps(base.BaseSteps):
    """Swift container steps."""

    @steps_checker.step
    def create(self, name, check=True):
        """Step to create container and check it exists in containers list.

        Args:
            name (str): container name
            check (bool, optional): flag whether to check this step or not

        Returns:
            dict: created container

        Raises:
            AssertionError: if check failed
        """
        self._client.put_container(name)
        container = self.get(name, check=check)
        if check:
            self.check_presence(name)
        return container

    @steps_checker.step
    def get(self, name, check=True):
        """Step to get container by name.

        Args:
            name (str): container name
            check (bool, optional): flag whether to check this step or not

        Returns:
            dict: container

        Raises:
            AssertionError: if container dict is empty
        """
        container, _ = self._client.get_container(name)
        if check:
            assert_that(container, is_not(empty()))
        return container

    @steps_checker.step
    def delete(self, name, check=True):
        """Step to delete container by name.

        Args:
            name (str): container name
            check (bool, optional): flag whether to check this step or not

        Raises:
            AssertionError: if container is not deleted
        """
        self._client.delete_container(name)
        if check:
            self.check_presence(name, must_present=False)

    @steps_checker.step
    def check_presence(self, name, must_present=True):
        """Step to check container presence.

        Args:
            name (str): container name
            must_present (bool, optional): flag whether container should exist
                or not

        Raises:
            AssertionError: if check failed
        """
        _, containers = self._client.get_container('', full_listing=True)
        matcher = has_items(has_entries(name=name))
        if not must_present:
            matcher = is_not(matcher)
        assert_that(containers, matcher)

    @steps_checker.step
    def put_object(self, container_name, object_name, content, check=True):
        """Step to put object to container.

        Args:
            container_name (str): container name
            object_name (str): object name
            content (str): content to put
            check (bool, optional): flag whether to check this step or not

        Raises:
            AssertionError: if object is not present in container
        """
        self._client.put_object(container_name, object_name, content)
        if check:
            self.check_object_presence(container_name, object_name)

    @steps_checker.step
    def get_object(self, container_name, object_name, check=True):
        """Step to get (download) object from container.

        Args:
            container_name (str): container name
            object_name (str): object name
            check (bool, optional): flag whether to check this step or not

        Returns:
            str: object content
        """
        _, content = self._client.get_object(container_name, object_name)
        if check:
            assert_that(content, is_not(empty()))
        return content

    @steps_checker.step
    def delete_object(self, container_name, object_name, check=True):
        """Step to delete object from container.

        Args:
            container_name (str): container name
            object_name (str): object name
            check (bool, optional): flag whether to check this step or not

        Raises:
            AssertionError: if object is present in container after deleting
        """
        self._client.delete_object(container_name, object_name)
        if check:
            self.check_object_presence(container_name, object_name,
                                       must_present=False)

    @steps_checker.step
    def check_object_presence(self, container_name, object_name,
                              must_present=True):
        """Step to check object presence.

        Args:
            container_name (str): container name
            object_name (str): object name
            must_present (bool, optional): flag whether object should exist or
                not

        Raises:
            AssertionError: if check failed
        """
        _, objects = self._client.get_container(container_name,
                                                full_listing=True)
        matcher = has_items(has_entries(name=object_name))
        if not must_present:
            matcher = is_not(matcher)
        assert_that(objects, matcher)

    @steps_checker.step
    def check_object_content(self, container_name, object_name,
                             expected_content):
        """Step to check object content.

        Args:
            container_name (str): container name
            object_name (str): object name
            expected_content (str): expected content

        Raises:
            AssertionError: if object content is not equal to expected content
        """
        content = self.get_object(container_name, object_name)
        assert_that(content, equal_to(expected_content))


class ContainerCephSteps(base.BaseSteps):
    """Ceph container steps."""

    @steps_checker.step
    def create(self, bucket_name=None, check=True):
        """Step to create bucket.

        Args:
            bucket_name (str|None): bucket name
            check (bool, optional): flag whether to check this step or not

        Returns:
            bucket (obj): created bucket

        Raises:
            AssertionError: if check failed
        """
        bucket_name = bucket_name or next(utils.generate_ids())
        bucket = self._client.create_bucket(Bucket=bucket_name)
        if check:
            self.check_presence(bucket_name)
        return bucket

    @steps_checker.step
    def list(self, check=True):
        """Step to list all buckets.

        Args:
            check (bool, optional): flag whether to check this step or not

        Returns:
            buckets_name_list (dict): list of all buckets

        Raises:
            AssertionError: if check failed
        """
        buckets_name_list = self._client.list_buckets()
        if check:
            assert_that(buckets_name_list, is_not(empty()))
        return buckets_name_list

    @steps_checker.step
    def check_presence(self, bucket_name, must_present=True):
        """Step to check container presents in containers list.

        Args:
            bucket_name (str): bucket name
            must_present (bool, optional): flag whether container should exist
                or not

        Raises:
            AssertionError: if check failed
        """
        buckets_name_list = self.list()
        for bucket in buckets_name_list['Buckets']:
            if must_present:
                assert_that(bucket_name, is_in(bucket['Name']))
            else:
                assert_that(bucket_name, is_not(is_in(bucket['Name'])))
