"""
------------
Volume tests
------------
"""

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import pytest

from stepler.third_party import utils


@pytest.mark.idempotent_id('3421a84f-5a15-4195-ba58-1e143092ef1e')
def test_create_volume_from_snapshot(volume_snapshot, volume_steps):
    """**Scenario:** Verify creation volume from snapshot.

    **Setup:**

        #. Create volume1
        #. Create snapshot from volume1

    **Steps:**

        #. Create volume2 from snapshot
        #. Delete volume2

    **Teardown:**

        #. Delete snapshot
        #. Delete volume1
    """
    volume_name = next(utils.generate_ids('volume'))
    volume = volume_steps.create_volume(name=volume_name,
                                        snapshot_id=volume_snapshot.id)
    volume_steps.delete_volume(volume)


@pytest.mark.idempotent_id('965cb50a-2900-4788-974f-9def0648484a')
def test_create_delete_10_volumes(volume_steps):
    """**Scenario:** Verify that 10 cinder volumes can be created and deleted.

    **Steps:**

    #. Create 10 cinder volumes
    #. Delete 10 cinder volumes

    **Teardown:**

    #. Delete volumes
    """
    volumes_names = utils.generate_ids('volume', count=10)

    volumes = volume_steps.create_volumes(names=volumes_names)
    volume_steps.delete_volumes(volumes)


@pytest.mark.idempotent_id('45783965-096f-46d6-a863-e466cc9d2d49')
def test_create_volume_without_name(create_volume):
    """**Scenario:** Verify creation of volume without name.

    **Steps:**

    #. Create volume without name

    **Teardown:**

    #. Delete volume
    """
    create_volume()


@pytest.mark.idempotent_id('8b08bc8f-e1f4-4f6e-8f98-dfcb1f9f538a')
def test_create_volume_description(create_volume):
    """**Scenario:** Verify creation of volume with description.

    **Steps:**

    #. Create volume with description

    **Teardown:**

    #. Delete volume
    """
    description = next(utils.generate_ids(prefix='volume'))
    create_volume(description=description)


@pytest.mark.idempotent_id('56cc7c76-ae92-423d-81ad-8cece5f875ad')
def test_create_volume_description_max(create_volume):
    """**Scenario:** Verify creation of volume with max description length.

    **Steps:**

    #. Create volume with description length == max(255)

    **Teardown:**

    #. Delete volume
    """
    description = next(utils.generate_ids(prefix='volume', length=255))
    create_volume(description=description)


@pytest.mark.idempotent_id('978a580d-22c3-4e98-8ff9-7ff8541cdd48')
@pytest.mark.parametrize('size', [0, -1, '', ' ', 'abc', '*&^%$%'])
def test_create_volume_wrong_size(volume_steps, size):
    """**Scenario:** Verify creation of volume with zero/negative size.

    **Steps:**

    #. Create volume with size 0/-1 Gbs
    #. Check that BadRequest occurred
    """
    volume_steps.check_negative_volume_creation_incorrect_size(size=size)


@pytest.mark.idempotent_id('bcd12002-dfd3-44c9-b270-d844d61a009c')
def test_negative_create_volume_name_long(volume_steps):
    """**Scenario:** Verify creation of volume with name length > 255.

    **Steps:**

    #. Try to create volume with name length > 255
    #. Check that BadRequest exception raised
    """
    long_name = next(utils.generate_ids(length=256))
    volume_steps.check_negative_volume_not_created(name=long_name)
