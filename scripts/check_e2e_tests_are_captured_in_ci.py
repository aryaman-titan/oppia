# Copyright 2020 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A script to check that travis.yml file & protractor.conf.js have the
same test suites.
"""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import os
import re

import python_utils
import utils

# These 4 test suites are not present in travis ci.
# One is extra (ie. (full: [*.js])) and three other test suites are
# are being run by CircleCI.
TEST_SUITES_NOT_RUN_ON_TRAVIS = [
    'full', 'classroomPageFileUploadFeatures', 'fileUploadFeatures',
    'topicAndStoryEditorFileUploadFeatures']

TRAVIS_CI_FILE_PATH = os.path.join(os.getcwd(), '.travis.yml')
PROTRACTOR_CONF_FILE_PATH = os.path.join(
    os.getcwd(), 'core', 'tests', 'protractor.conf.js')
SAMPLE_TEST_SUITE_THAT_IS_KNOWN_TO_EXIST = 'explorationImprovementsTab'


def get_e2e_suite_names_from_jobs_travis_yml_file():
    """Extracts the env/jobs section from the .travis.yml file.

    Returns:
        list(str): An alphabetically-sorted list of names of test suites
        from the jobs section in the travis.yml file.
    """
    travis_file_content = read_and_parse_travis_yml_file()
    jobs_str = python_utils.convert_to_bytes(travis_file_content['env']['jobs'])
    suites_from_jobs = []
    # The following line extracts the test suite name from the jobs section
    # that is in the form RUN_E2E_TESTS_ACCESSIBILITY=true.
    test_regex = re.compile(r'RUN_E2E_TESTS_([A-Z_]*)=')
    jobs = test_regex.findall(jobs_str)
    for job in jobs:
        suites_from_jobs.append(
            utils.snake_case_to_camel_case(job.lower()))

    return sorted(suites_from_jobs)


def get_e2e_suite_names_from_script_travis_yml_file():
    """Extracts the script section from the .travis.yml file.

    Returns:
        list(str): An alphabetically-sorted list of names of test suites
        from the script section in the travis.yml file.
    """
    travis_file_content = read_and_parse_travis_yml_file()
    script_str = python_utils.convert_to_bytes(travis_file_content['script'])
    # The following line extracts the test suites from patterns like
    # bash scripts/run_e2e_tests.sh --suite="accessibility"
    e2e_test_suite_regex = re.compile(
        r'bash scripts/run_e2e_tests.sh --suite="([a-zA-Z_-]*)"')
    suites_list = e2e_test_suite_regex.findall(script_str)

    return sorted(suites_list)


def get_e2e_suite_names_from_protractor_file():
    """Extracts the test suites section from the .travis.yml file.

    Returns:
        list(str): An alphabetically-sorted list of names of test suites
        from the protractor.conf.js file.
    """
    protractor_config_file_content = read_protractor_conf_file()
    # The following line extracts suite object from protractor.conf.js.
    suite_object_string = re.compile(
        r'suites = {([^}]+)}').findall(protractor_config_file_content)[0]

    # The following line extracts the keys/test suites from the "key: value"
    # pair from the suites object.
    key_regex = re.compile(r'\b([a-zA-Z_-]*):')
    protractor_suites = key_regex.findall(suite_object_string)

    return sorted(protractor_suites)


def read_protractor_conf_file():
    """Returns the contents of core/tests/protractor.conf.js file.

    Returns:
        str. The contents of protractor.conf.js, as a string.
    """
    protractor_config_file_content = python_utils.open_file(
        PROTRACTOR_CONF_FILE_PATH, 'r').read()
    return protractor_config_file_content


def read_and_parse_travis_yml_file():
    """Returns the contents of .travis.yml, as a dict.

    Returns:
        dict. Contents of the travis.yml file parsed as a dict.
    """
    travis_ci_file_content = python_utils.open_file(
        TRAVIS_CI_FILE_PATH, 'r').read()
    travis_ci_dict = utils.dict_from_yaml(travis_ci_file_content)
    return travis_ci_dict


def main():
    """Test the travis ci file and protractor.conf.js to have same
    e2e test suites.
    """
    python_utils.PRINT('Checking e2e tests are captured in travis.yml...')
    protractor_test_suites = get_e2e_suite_names_from_protractor_file()
    yaml_jobs = get_e2e_suite_names_from_jobs_travis_yml_file()
    yaml_scripts = get_e2e_suite_names_from_script_travis_yml_file()

    for excluded_test in TEST_SUITES_NOT_RUN_ON_TRAVIS:
        protractor_test_suites.remove(excluded_test)

    if not yaml_jobs:
        raise Exception('The e2e test suites that have been extracted from '
                        'jobs section from travis.ci are empty.')
    if not yaml_scripts:
        raise Exception('The e2e test suites that have been extracted from '
                        'script section from travis.ci are empty.')
    if not protractor_test_suites:
        raise Exception('The e2e test suites that have been extracted from '
                        'protractor.conf.js are empty.')

    if SAMPLE_TEST_SUITE_THAT_IS_KNOWN_TO_EXIST not in yaml_jobs:
        raise Exception('explorationImprovementsTab is expected to be in '
                        'the e2e test suites extracted from the jobs section '
                        'of .travis.yml file, but it is missing.')
    if SAMPLE_TEST_SUITE_THAT_IS_KNOWN_TO_EXIST not in yaml_scripts:
        raise Exception('explorationImprovementsTab is expected to be in '
                        'the e2e test suites extracted from the script section '
                        'of .travis.yml file, but it is missing.')
    if SAMPLE_TEST_SUITE_THAT_IS_KNOWN_TO_EXIST not in protractor_test_suites:
        raise Exception('explorationImprovementsTab is expected to be in '
                        'the e2e test suites extracted from the '
                        'protractor.conf.js file, but it is missing.')

    if not (protractor_test_suites == yaml_jobs and yaml_jobs == yaml_scripts):
        raise Exception(
            'Protractor test suites and Travis Ci test suites are not in sync.')

    python_utils.PRINT('Done!')


# The 'no coverage' pragma is used as this line is un-testable. This is because
# it will only be called when check_e2e_tests_are_captured_in_ci.py
# is used as a script.
if __name__ == '__main__':  # pragma: no cover
    main()
