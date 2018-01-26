# Copyright 2016 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import os
import sys

import nox


LOCAL_DEPS = (
    os.path.join('..', 'api_core'),
    os.path.join('..', 'core'),
)
UNIT_TEST_DEPS = (
    'mock',
    'pytest',
    'pytest-cov',
    'flask',
    'webapp2',
    'webob',
)


@nox.session
def default(session):
    """Default unit test session.

    This is intended to be run **without** an interpreter set, so
    that the current ``python`` (on the ``PATH``) or the version of
    Python corresponding to the ``nox`` binary the ``PATH`` can
    run the tests.
    """
    # Install all test dependencies, then install this package in-place.
    deps = UNIT_TEST_DEPS
    if session.interpreter == 'python2.7':
        deps += ('django >= 1.11.0, < 2.0.0dev',)
    elif session.interpreter is None and sys.version_info[:2] == (2, 7):
        deps += ('django >= 1.11.0, < 2.0.0dev',)
    else:
        deps += ('django',)

    deps += LOCAL_DEPS
    session.install(*deps)
    session.install('-e', '.')

    # Run py.test against the unit tests.
    session.run(
        'py.test',
        '--quiet',
        '--cov=google.cloud.logging',
        '--cov=tests.unit',
        '--cov-append',
        '--cov-config=.coveragerc',
        '--cov-report=',
        '--cov-fail-under=97',
        'tests/unit',
        *session.posargs
    )


@nox.session
@nox.parametrize('py', ['2.7', '3.4', '3.5', '3.6'])
def unit(session, py):
    """Run the unit test suite."""

    # Run unit tests against all supported versions of Python.
    session.interpreter = 'python{}'.format(py)

    # Set the virtualenv dirname.
    session.virtualenv_dirname = 'unit-' + py

    default(session)


@nox.session
@nox.parametrize('py', ['2.7', '3.6'])
def system(session, py):
    """Run the system test suite."""

    # Sanity check: Only run system tests if the environment variable is set.
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''):
        session.skip('Credentials must be set via environment variable.')

    # Run the system tests against latest Python 2 and Python 3 only.
    session.interpreter = 'python{}'.format(py)

    # Set the virtualenv dirname.
    session.virtualenv_dirname = 'sys-' + py

    # Install all test dependencies, then install this package into the
    # virtualenv's dist-packages.
    session.install('mock', 'pytest', *LOCAL_DEPS)
    session.install('../test_utils/', '../bigquery/', '../pubsub/',
                    '../storage/')
    session.install('.')

    # Run py.test against the system tests.
    session.run(
        'py.test',
        '-vvv',
        '-s',
        'tests/system',
        *session.posargs)


@nox.session
def lint(session):
    """Run linters.

    Returns a failure if the linters find linting errors or sufficiently
    serious code quality issues.
    """
    session.interpreter = 'python3.6'
    session.install('flake8', 'pylint', 'gcp-devrel-py-tools', *LOCAL_DEPS)
    session.install('.')
    session.run('flake8', 'google/cloud/logging')
    session.run(
        'gcp-devrel-py-tools', 'run-pylint',
        '--config', 'pylint.config.py',
        '--library-filesets', 'google',
        '--test-filesets', 'tests',
        # Temporarily allow this to fail.
        success_codes=range(0, 100))


@nox.session
def lint_setup_py(session):
    """Verify that setup.py is valid (including RST check)."""
    session.interpreter = 'python3.6'

    # Set the virtualenv dirname.
    session.virtualenv_dirname = 'setup'

    session.install('docutils', 'Pygments')
    session.run(
        'python', 'setup.py', 'check', '--restructuredtext', '--strict')


@nox.session
def cover(session):
    """Run the final coverage report.

    This outputs the coverage report aggregating coverage from the unit
    test runs (not system test runs), and then erases coverage data.
    """
    session.interpreter = 'python3.6'
    session.install('coverage', 'pytest-cov')
    session.run('coverage', 'report', '--show-missing', '--fail-under=100')
    session.run('coverage', 'erase')