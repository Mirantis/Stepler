===================
Launcher parameters
===================

---------------------
Environment variables
---------------------

* ``OS_AUTH_URL`` - openstack keystone auth URL. Is required explicitly:
  **v3** - ``http://keystone/url/v3``, **v2** - ``http://keystone/url/v2.0``.
* ``OS_USERNAME`` - openstack user name. By default is ``admin``.
* ``OS_PASSWORD`` - openstack user password. By default is ``password``.
* ``OS_PROJECT_NAME`` - openstack project name. By default is ``admin``.
* ``OS_PROJECT_DOMAIN_NAME`` - openstack project domain name. By default is
  ``default``.
* ``OS_USER_DOMAIN_NAME`` - openstack user domain name. By default is
  ``default``.
* ``OS_DASHBOARD_URL`` - URL of horizon dashboard. Is required for UI testing.
* ``VIRTUAL_DISPLAY`` - Flag to notify that virtual framebuffer should be used.
  It requires of installed ``xvfb``. Is disabled by default.
* ``TEST_REPORTS_DIR`` - directory where ``test_reports`` folder will be
  created. By default it will be in directory where tests are launched.
* ``OS_FLOATING_NETWORK`` - name of external (floating) network. By default is
  ``admin_floating_net``.

--------------
Pytest options
--------------

* ``--disable-steps-checker`` - Suppress steps consitency checking before
  tests. Only for debugging. Isn't recommended on production.
* ``--snapshot-name <snapshot name>`` - Specify environment snapshot name for
  cloud reverting. Is required for destructive tests.
