# Copyright 2016-2017 Red Hat Inc & Xena Networks.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Contributors:
#   Christian Trautman, Red Hat Inc.
#

"""
Xena 2544 execution from command line with final verification step

Instructions:
1.  For linux Install Mono ->
    rpm --import "http://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF"
    yum-config-manager --add-repo http://download.mono-project.com/repo/centos/
    yum -y install mono-complete
2. If python 3 not installed, install python 3. For RHEL instructions are below->
    # install SCL for python33 by adding a repo to find its location to install it
    [rhscl-python33-el7]
    name=Copr repo for python33-el7 owned by rhscl
    baseurl=https://copr-be.cloud.fedoraproject.org/results/rhscl/python33-el7/epel-7-$basearch/
    type=rpm-md
    skip_if_unavailable=True
    gpgcheck=1
    gpgkey=https://copr-be.cloud.fedoraproject.org/results/rhscl/python33-el7/pubkey.gpg
    repo_gpgcheck=0
    enabled=1
    enabled_metadata=1

    # install python33 package
    yum -y install python33 python33-python-tkinter
    # cleanup python 33 repo file
    rm -f /etc/yum.repos.d/python33.repo

3. Enable python33 -> scl enable python33 bash

4. Make sure Xena2544.exe is present in the current folder

5. Arguments to run this script
    -f <path to config file> saved from Xena2544.exe GUI with your config.
    -s enable smart search, if verify fails will resume the search at the half
       way point between the last verify attempt and the minimum search value.
       Otherwise it will just resume at the last verify attempt value minus
       the value threshhold.
    -l <verify length in seconds> Default of 2 hours.
    -r <retry attempts> Maximum number of verify attempts for giving up
    -d Enable debug mode
    -p Output PDF file. By default output of PDF report is disabled. Will cause
       a crash on linux usually as a pdf renderer is not installed.
    -w Enable windows mode. By default it will use the mono package to run the
       exe file. If running on windows this is not necessary.
    -t <search trial duration in seconds> Modify original config to use the
       duration specified.

"""

import argparse
import json
import locale
import logging
import os
import subprocess
import sys
from time import sleep
import xml.etree.ElementTree as ET

_LOGGER = logging.getLogger(__name__)
_LOCALE = locale.getlocale()[1]
_XENA_USER = 'TestUser'
_PYTHON_2 = sys.version_info[0] < 3

class XenaJSON(object):
    """
    Class to modify and read Xena JSON configuration files.
    """
    def __init__(self, json_path):
        """
        Constructor
        :param json_path: path to JSON file to read. Expected files must have
         two module ports with each port having its own stream config profile.
        :return: XenaJSON object
        """
        self.json_data = read_json_file(json_path)
        self.min_tput = self.json_data['TestOptions']['TestTypeOptionMap'][
            'Throughput']['RateIterationOptions']['MinimumValue']
        self.init_tput = self.json_data['TestOptions']['TestTypeOptionMap'][
            'Throughput']['RateIterationOptions']['InitialValue']
        self.max_tput = self.json_data['TestOptions']['TestTypeOptionMap'][
            'Throughput']['RateIterationOptions']['MaximumValue']
        self.value_thresh = self.json_data['TestOptions']['TestTypeOptionMap'][
            'Throughput']['RateIterationOptions']['ValueResolution']
        self.duration = self.json_data['TestOptions']['TestTypeOptionMap'][
            'Throughput']['Duration']

    # pylint: disable=too-many-arguments
    def modify_2544_tput_options(self, initial_value, minimum_value,
                                 maximum_value):
        """
        modify_2544_tput_options
        """
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'RateIterationOptions']['InitialValue'] = initial_value
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'RateIterationOptions']['MinimumValue'] = minimum_value
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'RateIterationOptions']['MaximumValue'] = maximum_value

    def modify_duration(self, duration):
        """
        Modify test duration
        :param duration: test time duration in seconds as int
        :return: None
        """
        self.json_data['TestOptions']['TestTypeOptionMap']['Throughput'][
            'Duration'] = duration

    def modify_reporting(self, pdf_enable=True, csv_enable=False,
                         xml_enable=True, html_enable=False,
                         timestamp_enable=False):
        """
        Modify the reporting options
        :param pdf_enable: Enable pdf output, should disable for linux
        :param csv_enable: Enable csv output
        :param xml_enable: Enable xml output
        :param html_enable: Enable html output
        :param timestamp_enable: Enable timestamp to report
        :return: None
        """
        self.json_data['ReportConfig'][
            'GeneratePdf'] = 'true' if pdf_enable else 'false'
        self.json_data['ReportConfig'][
            'GenerateCsv'] = 'true' if csv_enable else 'false'
        self.json_data['ReportConfig'][
            'GenerateXml'] = 'true' if xml_enable else 'false'
        self.json_data['ReportConfig'][
            'GenerateHtml'] = 'true' if html_enable else 'false'
        self.json_data['ReportConfig'][
            'AppendTimestamp'] = 'true' if timestamp_enable else 'false'

    def write_config(self, path='./2bUsed.x2544'):
        """
        Write the config to out as file
        :param path: Output file to export the json data to
        :return: None
        """
        if not write_json_file(self.json_data, path):
            raise RuntimeError("Could not write out file, please check config")

def main(args):
    _LOGGER.setLevel(logging.DEBUG if args.debug else logging.INFO)
    stream_logger = logging.StreamHandler(sys.stdout)
    stream_logger.setFormatter(logging.Formatter(
        '[%(levelname)-5s]  %(asctime)s : (%(name)s) - %(message)s'))
    _LOGGER.addHandler(stream_logger)
    # get the current json config into an object
    xena_current = XenaJSON(args.config_file)
    # Modify to output xml always as its needed to parse, turn off PDF output
    # unless user specifies it. Usually not supported on Linux. Also need to
    # disable the timestamp
    xena_current.modify_reporting(True if args.pdf_output else False,
                                  True, True, False, False)
    if args.search_trial_duration:
        xena_current.modify_duration(args.search_trial_duration)
    xena_current.write_config('./2bUsed.x2544')

    result = run_xena('./2bUsed.x2544', args.windows_mode)

    # now run the verification step by creating a new config with the desired
    # params
    for _ in range(1, args.retry_attempts +1):
        if result[0] != 'PASS':
            _LOGGER.error('Xena2544.exe Test failed. Please check test config.')
            break
        _LOGGER.info('Verify attempt {}'.format(_))
        old_min = xena_current.min_tput # need this if verify fails
        old_duration = xena_current.duration
        xena_current.modify_2544_tput_options(result[1], result[1],
                                              result[1])
        xena_current.modify_duration(args.verify_duration)
        xena_current.write_config('./verify.x2544')
        # run verify step
        _LOGGER.info('Running verify for {} seconds'.format(
            args.verify_duration))
        verify_result = run_xena('./verify.x2544', args.windows_mode)
        if verify_result[0] == 'PASS':
            _LOGGER.info('Verify passed. Packets lost = {} Exiting'.format(
                verify_result[3]))
            _LOGGER.info('Pass result transmit rate = {}'.format(
                verify_result[1]))
            _LOGGER.info('Pass result transmit fps = {}'.format(
                verify_result[2]))
            break
        else:
            _LOGGER.warn('Verify failed. Packets lost = {}'.format(
                verify_result[3]))
            _LOGGER.info('Restarting Xena2544.exe with new values')
            if args.smart_search:
                new_init = (verify_result[1] - old_min) / 2
            else:
                new_init = result[1] - xena_current.value_thresh
            xena_current.modify_2544_tput_options(
                new_init, old_min, result[1] - xena_current.value_thresh)
            xena_current.modify_duration(
                args.search_trial_duration if args.search_trial_duration else
                old_duration)
            _LOGGER.info('New minimum value: {}'.format(old_min))
            _LOGGER.info('New maximum value: {}'.format(
                result[1] - xena_current.value_thresh))
            _LOGGER.info('New initial rate: {}'.format(new_init))
            xena_current.write_config('./verify.x2544')
            result = run_xena('./verify.x2544', args.windows_mode)
    else:
        _LOGGER.error('Maximum number of verify retries attempted. Exiting...')


def read_json_file(json_file):
    """
    Read the json file path and return a dictionary of the data
    :param json_file: path to json file
    :return: dictionary of json data
    """
    try:
        if _PYTHON_2:
            with open(json_file, 'r') as data_file:
                file_data = json.loads(data_file.read())
        else:
            with open(json_file, 'r', encoding=_LOCALE) as data_file:
                file_data = json.loads(data_file.read())
    except ValueError as exc:
        # general json exception, Python 3.5 adds new exception type
        _LOGGER.exception("Exception with json read: %s", exc)
        raise
    except IOError as exc:
        _LOGGER.exception(
            'Exception during file open: %s file=%s', exc, json_file)
        raise
    return file_data


def run_xena(config_file, windows_mode=False):
    """
    Run Xena2544.exe with the config file specified.
    :param config_file: config file to use
    :param windows_mode: enable windows mode which bypasses the usage of mono
    :return: Tuple of pass or fail result as str, and current transmit rate as
    float, transmit fps, and packets lost
    """
    user_home = os.path.expanduser('~')
    log_path = '{}/Xena/Xena2544-2G/Logs/xena2544.log'.format(user_home)
    # make the folder and log file if they doesn't exist
    if not os.path.exists(log_path):
        os.makedirs(os.path.dirname(log_path))

    # empty the file contents
    open(log_path, 'w').close()

    # setup the xena command line
    args = ["mono" if not windows_mode else "",
            "Xena2544.exe", "-c", config_file, "-e", "-r", "./", "-u",
            _XENA_USER]

    # Sometimes Xena2544.exe completes, but mono holds the process without
    # releasing it, this can cause a deadlock of the main thread. Use the
    # xena log file as a way to detect this.
    log_handle = open(log_path, 'r')
    # read the contents of the log before we start so the next read in the
    # wait method are only looking at the text from this test instance
    log_handle.read()
    mono_pipe = subprocess.Popen(args, stdout=sys.stdout)
    data = ''
    if _PYTHON_2:
        _LOGGER.error('Not supported yet for python 2...')
    else:
        while True:
            try:
                mono_pipe.wait(60)
                log_handle.close()
                break
            except subprocess.TimeoutExpired:
                # check the log to see if Xena2544 has completed and mono is
                # deadlocked.
                data += log_handle.read()
                if 'TestCompletedSuccessfully' in data:
                    log_handle.close()
                    mono_pipe.terminate()
                    break

    # parse the result file and return the needed data
    root = ET.parse(r'./xena2544-report.xml').getroot()
    return (root[0][1][0].get('TestState'),
            float(root[0][1][0].get('TotalTxRatePcnt')),
            int(root[0][1][0].get('TotalTxRateFps')),
            root[0][1][0].get('TotalLossFrames'))


def write_json_file(json_data, output_path):
    """
    Write out the dictionary of data to a json file
    :param json_data: dictionary of json data
    :param output_path: file path to write output
    :return: Boolean if success
    """
    try:
        if _PYTHON_2:
            with open(output_path, 'w') as fileh:
                json.dump(json_data, fileh, indent=2, sort_keys=True,
                          ensure_ascii=True)
        else:
            with open(output_path, 'w', encoding=_LOCALE) as fileh:
                json.dump(json_data, fileh, indent=2, sort_keys=True,
                          ensure_ascii=True)
        return True
    except ValueError as exc:
        # general json exception, Python 3.5 adds new exception type
        _LOGGER.exception(
            "Exception with json write: %s", exc)
        return False
    except IOError as exc:
        _LOGGER.exception(
            'Exception during file write: %s file=%s', exc, output_path)
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--config_file', type=str, required=True,
                        help='Xena 2544 json config file name')
    parser.add_argument('-d', '--debug', action='store_true', required=False,
                        help='Enable debug logging')
    parser.add_argument('-w', '--windows_mode', required=False,
                        action='store_true', help='Use windows mode, no mono')
    parser.add_argument('-l', '--verify_duration', required=False,
                        type=int, default=7200,
                        help='Verification duration in seconds')
    parser.add_argument('-r', '--retry_attempts', type=int, default=10,
                        required=False, help='Maximum verify attempts')
    parser.add_argument('-s', '--smart_search', action='store_true',
                        required=False, help='Enable smart search',
                        default=False)
    parser.add_argument('-p', '--pdf_output', action='store_true',
                        required=False,
                        help='Generate PDF report, do not use on Linux!',
                        default=False)
    parser.add_argument('-t', '--search_trial_duration', required=False,
                        help='Search trial duration in seconds', type=int,
                        default=0)
    args = parser.parse_args()
    if args.debug:
        print("DEBUG ENABLED!!!")
    main(args)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

