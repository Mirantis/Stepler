"""
---------------
Glance fixtures
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

import logging

from hamcrest import assert_that, is_not  # noqa
import pytest

from stepler import config
from stepler.glance import steps
from stepler.third_party import utils

__all__ = [
    'api_glance_steps',
    'api_glance_steps_v1',
    'api_glance_steps_v2',
    'cirros_image',
    'create_image',
    'create_images',
    'get_glance_steps',
    'glance_steps',
    'glance_steps_v1',
    'glance_steps_v2',
    'ubuntu_image',
    'images_cleanup',
    'ubuntu_xenial_image',
]

LOGGER = logging.getLogger(__name__)
# images which should be missed, when unexpected images will be removed
SKIPPED_IMAGES = []  # TODO(schipiga): describe its mechanism in docs


@pytest.yield_fixture
def images_cleanup():
    """Callable function fixture to clear unexpected images.

    It provides cleanup before and after test. Cleanup before test is callable
    with injecton of glance steps. Should be called before returning of
    instantiated glance steps.
    """
    _glance_steps = [None]

    def _images_cleanup(glance_steps):
        assert_that(glance_steps, is_not(None))
        _glance_steps[0] = glance_steps  # inject glance steps for finalizer
        # check=False because in best case no images will be present
        images = glance_steps.get_images(name_prefix=config.STEPLER_PREFIX,
                                         check=False)
        if SKIPPED_IMAGES:
            image_names = [image.name for image in SKIPPED_IMAGES]
            LOGGER.debug(
                "SKIPPED_IMAGES contains images {!r}. They will not be "
                "removed in cleanup procedure.".format(image_names))

        images = [image for image in images if image not in SKIPPED_IMAGES]
        if images:
            glance_steps.delete_images(images)

    yield _images_cleanup

    _images_cleanup(_glance_steps[0])


# TODO(schipiga): In future will rename `glance_steps` -> `image_steps`
@pytest.fixture(scope='session')
def get_glance_steps(request, get_glance_client):
    """Callable session fixture to get glance steps.

    Args:
        get_glance_client (function): function to get glance client

    Returns:
        function: function to get glance steps
    """
    def _get_glance_steps(version, is_api):
        glance_client = get_glance_client(version, is_api)

        glance_steps_cls = {
            '1': steps.GlanceStepsV1,
            '2': steps.GlanceStepsV2,
        }[version]

        return glance_steps_cls(glance_client)

    return _get_glance_steps


@pytest.fixture
def glance_steps_v1(get_glance_steps):
    """Function fixture to get glance steps for v1.

    Args:
        get_glance_steps (function): function to get glance steps

    Returns:
        GlanceStepsV1: instantiated glance steps v1
    """
    return get_glance_steps(version='1', is_api=False)


@pytest.fixture
def glance_steps_v2(get_glance_steps):
    """Function fixture to get glance steps for v2.

    Args:
        get_glance_steps (function): function to get glance steps

    Returns:
        GlanceStepsV2: instantiated glance steps v2
    """
    return get_glance_steps(version='2', is_api=False)


@pytest.fixture
def api_glance_steps_v1(get_glance_steps):
    """Function fixture to get API glance steps for v1.

    Args:
        get_glance_steps (function): function to get glance steps

    Returns:
        GlanceStepsV1: instantiated glance steps v1
    """
    return get_glance_steps(version='1', is_api=True)


@pytest.fixture
def api_glance_steps_v2(get_glance_steps):
    """Function fixture to get API glance steps for v2.

    Args:
        get_glance_steps (function): function to get API glance steps

    Returns:
        GlanceSteps: instantiated glance steps
    """
    return get_glance_steps(version='1', is_api=True)


@pytest.fixture
def glance_steps(get_glance_steps, images_cleanup):
    """Function fixture to get API glance steps.

    Args:
        get_glance_steps (function): function to get glance steps
        images_cleanup (function): function to make images cleanup right
            after glance steps initialization

    Returns:
        GlanceStepsV1: instantiated glance steps v1
    """
    _glance_steps = get_glance_steps(
        version=config.CURRENT_GLANCE_VERSION, is_api=False)
    images_cleanup(_glance_steps)
    return _glance_steps


@pytest.fixture
def api_glance_steps(get_glance_steps):
    """Function fixture to get API glance steps.

    Args:
        get_glance_steps (function): function to get API glance steps

    Returns:
        GlanceSteps: instantiated glance steps
    """
    return get_glance_steps(
        version=config.CURRENT_GLANCE_VERSION, is_api=True)


@pytest.yield_fixture
def create_images(glance_steps):
    """Callable function fixture to create images with options.

    Can be called several times during a test.
    After the test it destroys all created images.

    Args:
        glance_steps (object): instantiated glance steps

    Returns:
        function: function to create images as batch with options
    """
    images = []

    def _create_images(image_names, image_url, *args, **kwgs):
        image_path = utils.get_file_path(image_url)
        _images = glance_steps.create_images(
            image_names, image_path, *args, **kwgs)
        images.extend(_images)
        return _images

    yield _create_images

    if images:
        glance_steps.delete_images(images)


@pytest.fixture
def create_image(create_images):
    """Callable function fixture to create single image with options.

    Can be called several times during a test.
    After the test it destroys all created images.

    Args:
        create_images (function): function to create images with options

    Returns:
        function: function to create single image with options
    """
    def _create_image(image_name, image_url, *args, **kwgs):
        return create_images([image_name], image_url, *args, **kwgs)[0]

    return _create_image


@pytest.yield_fixture(scope='session')
def ubuntu_image(get_glance_steps):
    """Session fixture to create ubuntu image.

    Creates image from config.UBUNTU_QCOW2_URL with default options.

    Args:
        get_glance_steps (function): function to get glance steps

    Returns:
        object: ubuntu glance image
    """
    image_name = next(utils.generate_ids('ubuntu'))
    image_path = utils.get_file_path(config.UBUNTU_QCOW2_URL)

    _ubuntu_image = get_glance_steps(
        version=config.CURRENT_GLANCE_VERSION,
        is_api=False).create_images([image_name], image_path)[0]

    SKIPPED_IMAGES.append(_ubuntu_image)

    yield _ubuntu_image

    get_glance_steps(
        version=config.CURRENT_GLANCE_VERSION,
        is_api=False).delete_images([_ubuntu_image])

    SKIPPED_IMAGES.remove(_ubuntu_image)


@pytest.yield_fixture(scope='session')
def ubuntu_xenial_image(get_glance_steps):
    """Session fixture to create ubuntu xenial image.

    Creates image from config.UBUNTU_XENIAL_QCOW2_URL with default options.

    Args:
        get_glance_steps (function): function to get glance steps

    Returns:
        object: ubuntu glance image
    """
    image_name = next(utils.generate_ids('ubuntu-xenial'))
    image_path = utils.get_file_path(config.UBUNTU_XENIAL_QCOW2_URL)

    _ubuntu_image = get_glance_steps(
        version=config.CURRENT_GLANCE_VERSION,
        is_api=False).create_images([image_name], image_path)[0]

    SKIPPED_IMAGES.append(_ubuntu_image)

    yield _ubuntu_image

    get_glance_steps(
        version=config.CURRENT_GLANCE_VERSION,
        is_api=False).delete_images([_ubuntu_image])

    SKIPPED_IMAGES.remove(_ubuntu_image)


@pytest.yield_fixture(scope='session')
def cirros_image(get_glance_steps):
    """Session fixture to create cirros image with default options.

    Args:
        get_glance_steps (function): function to get glance steps

    Returns:
        object: cirros glance image
    """
    image_name = next(utils.generate_ids('cirros'))
    image_path = utils.get_file_path(config.CIRROS_QCOW2_URL)

    _cirros_image = get_glance_steps(
        version=config.CURRENT_GLANCE_VERSION,
        is_api=False).create_images([image_name], image_path)[0]

    SKIPPED_IMAGES.append(_cirros_image)

    yield _cirros_image

    get_glance_steps(
        version=config.CURRENT_GLANCE_VERSION,
        is_api=False).delete_images([_cirros_image])

    SKIPPED_IMAGES.remove(_cirros_image)
