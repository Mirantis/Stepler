"""
---------------------------------
Object Storage container fixtures
---------------------------------
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

import boto3
import pytest

from stepler import config
from stepler.object_storage import steps as object_storage_steps

__all__ = [
    'container_steps',
]


@pytest.fixture
def container_steps(swift_client, os_faults_steps, ec2_steps, user_steps):
    """Function fixture to get swift container steps.

    Returns:
        object: instantiated swift or rbd container steps
    """
    if os_faults_steps.get_default_glance_backend() == "swift":
        return object_storage_steps.ContainerSwiftSteps(swift_client)
    else:
        user = user_steps.get_user(name=config.USERNAME)
        ec2_creds = ec2_steps.list(user)[0]
        auth_url = config.AUTH_URL.rsplit(':')
        endpoint_url = '{}:{}'.format(auth_url[0], auth_url[1])
        s3 = boto3.client('s3',
                          aws_access_key_id=ec2_creds.access,
                          aws_secret_access_key=ec2_creds.secret,
                          endpoint_url='{}:8080'.format(endpoint_url))
        return object_storage_steps.ContainerCephSteps(s3)
