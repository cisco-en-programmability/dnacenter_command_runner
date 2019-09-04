#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Cisco DNA Center Get Auth Token

Copyright (c) 2019 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.

"""

__author__ = "Gabriel Zapodeanu TME, ENB"
__email__ = "gzapodea@cisco.com"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2019 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


import requests
import json
import urllib3
import time
import sys

from urllib3.exceptions import InsecureRequestWarning  # for insecure https warnings
from requests.auth import HTTPBasicAuth  # for Basic Auth

from config import DNAC_URL, DNAC_PASS, DNAC_USER

urllib3.disable_warnings(InsecureRequestWarning)  # disable insecure https warnings

DNAC_AUTH = HTTPBasicAuth(DNAC_USER, DNAC_PASS)


def pprint(json_data):
    """
    Pretty print JSON formatted data
    :param json_data: data to pretty print
    :return None
    """
    print(json.dumps(json_data, indent=4, separators=(' , ', ' : ')))


def get_dnac_jwt_token(dnac_auth):
    """
    Create the authorization token required to access Cisco DNA Center
    Call to Cisco DNA C - /api/system/v1/auth/login
    :param dnac_auth - Cisco DNA Center Basic Auth string
    :return Cisco DNA Center Auth Token
    """
    url = DNAC_URL + '/dna/system/api/v1/auth/token'
    header = {'content-type': 'application/json'}
    response = requests.post(url, auth=dnac_auth, headers=header, verify=False)
    response_json = response.json()
    dnac_jwt_token = response_json['Token']
    return dnac_jwt_token


def get_all_device_info(dnac_jwt_token):
    """
    The function will return all network devices info
    :param dnac_jwt_token: Cisco DNA Center token
    :return: Cisco DNA Center device inventory info
    """
    url = DNAC_URL + '/api/v1/network-device'
    header = {'content-type': 'application/json', 'x-auth-token': dnac_jwt_token}
    all_device_response = requests.get(url, headers=header, verify=False)
    all_device_info = all_device_response.json()
    return all_device_info['response']


def get_device_id_name(device_name, dnac_jwt_token):
    """
    This function will find the Cisco DNA Center device id for the device with the name {device_name}
    :param device_name: device hostname
    :param dnac_jwt_token: Cisco DNA Center token
    :return:
    """
    device_id = None
    device_list = get_all_device_info(dnac_jwt_token)
    for device in device_list:
        if device['hostname'] == device_name:
            device_id = device['id']
    return device_id


def get_legit_cli_command_runner(dnac_jwt_token):
    """
    This function will get all the legit CLI commands supported by the {command runner} APIs
    :param dnac_jwt_token: Cisco DNA Centertoken
    :return: list of CLI commands
    """
    url = DNAC_URL + '/dna/intent/api/v1/network-device-poller/cli/legit-reads'
    header = {'content-type': 'application/json', 'x-auth-token': dnac_jwt_token}
    response = requests.get(url, headers=header, verify=False)
    response_json = response.json()
    cli_list = response_json['response']
    return cli_list


def get_content_file_id(file_id, dnac_jwt_token):
    """
    This function will download a file specified by the {file_id}
    :param file_id: file id
    :param dnac_jwt_token: Cisco DNA Centertoken
    :return: file
    """
    url = DNAC_URL + '/dna/intent/api/v1/file/' + file_id
    header = {'content-type': 'application/json', 'x-auth-token': dnac_jwt_token}
    response = requests.get(url, headers=header, verify=False, stream=True)
    response_json = response.json()
    return response_json


def get_output_command_runner(command, device_name, dnac_jwt_token):
    """
    This function will return the output of the CLI command specified in the {command}, sent to the device with the
    hostname {device}
    :param command: CLI command
    :param device_name: device hostname
    :param dnac_jwt_token: Cisco DNA Centertoken
    :return: file with the command output
    """

    # get the Cisco DNA Center device id
    device_id = get_device_id_name(device_name, dnac_jwt_token)

    # get the Cisco DNA Centertask id that will process the CLI command runner
    payload = {
        "commands": [command],
        "deviceUuids": [device_id],
        "timeout": 0
        }
    url = DNAC_URL + '/dna/intent/api/v1/network-device-poller/cli/read-request'
    header = {'content-type': 'application/json', 'x-auth-token': dnac_jwt_token}
    response = requests.post(url, data=json.dumps(payload), headers=header, verify=False)
    response_json = response.json()
    task_id = response_json['response']['taskId']
    print('Task id ', task_id)

    time.sleep(5)  # wait 5 seconds for the command to be executed
    # get task id status
    task_result = check_task_id_output(task_id, dnac_jwt_token)
    print(task_result)
    file_info = json.loads(task_result['progress'])
    file_id = file_info['fileId']

    # get output from file
    time.sleep(2)  # wait for 2 seconds for the file to be ready
    file_output = get_content_file_id(file_id, dnac_jwt_token)
    command_responses = file_output[0]['commandResponses']
    if command_responses['SUCCESS'] is not {}:
        command_output = command_responses['SUCCESS'][command]
    elif command_responses['FAILURE'] is not {}:
        command_output = command_responses['FAILURE'][command]
    else:
        command_output = command_responses['BLACKLISTED'][command]
    return command_output


def check_task_id_output(task_id, dnac_jwt_token):
    """
    This function will check the status of the task with the id {task_id}. Loop one seconds increments until task is completed
    :param task_id: task id
    :param dnac_jwt_token: Cisco DNA Center token
    :return: status - {SUCCESS} or {FAILURE}
    """
    url = DNAC_URL + '/dna/intent/api/v1/task/' + task_id
    header = {'content-type': 'application/json', 'x-auth-token': dnac_jwt_token}
    completed = 'no'
    while completed == 'no':
        try:
            task_response = requests.get(url, headers=header, verify=False)
            task_json = task_response.json()
            task_output = task_json['response']
            completed = 'yes'
        except:
            time.sleep(1)
    return task_output


def main(command, device_hostname):
    """
    This sample script will:
    -

    """

    # obtain the Cisco DNA Center Auth Token
    dnac_token = get_dnac_jwt_token(DNAC_AUTH)

    print('\n\nApplication "command_runner.py" Run Started')

    # obtain all the supported commands
    cli_commands_list = get_legit_cli_command_runner(dnac_token)

    print('\nThe list of CLI commands keywords supported by Cisco DNA Center: \n')
    pprint(cli_commands_list)

    # validate if the desired user command is supported
    cli_command_keyword = command.split(' ')[0]

    if cli_command_keyword in cli_commands_list:
        print('\nThe desired command "' + command + '" is supported')
        command_output = get_output_command_runner(command, device_hostname, dnac_token)
        print(command_output)

    print('\n\nEnd of Application "command_runner.py" Run')


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

