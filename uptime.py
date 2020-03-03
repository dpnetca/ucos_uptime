#!/usr/bin/env python
from nornir import InitNornir
import paramiko
import socket
import time
import re
import os
import argparse
import sys


def get_ucos_uptime(task, timeout=30):
    """
    """

    # initialize error, command and prompt variables
    error = False
    command = "show status\n"
    prompt = b"admin:"
    hostname = f"{task.host}:"
    result = f"{hostname:<20}"
    # initialize paramiko SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # get device parameters for connection
    device_params = {
        "hostname": task.host.hostname,
        "username": task.host.username,
        "password": task.host.password,
        "timeout": timeout,
        "banner_timeout": timeout,
    }

    # not really needed
    if not error:
        # connect device and handle common errors
        try:
            client.connect(**device_params)
        except socket.timeout:
            result += "Socket timeput, unable to connect"
            error = True
        except paramiko.ssh_exception.AuthenticationException:
            result += "Authenication failed"
            error = True
        except paramiko.ssh_exception.SSHException as e:
            result += f"SSH Exception: {e}"
            error = True

    # if no errors continue on
    if not error:
        # invoke shell, wait for admin prompt send command and capture results
        try:
            shell = client.invoke_shell()
            output = recv_until_prompt(shell, prompt, timeout)
            shell.send(command)
            output = recv_until_prompt(shell, prompt, timeout)
            shell.close()
            client.close()
        except TimeoutError:
            result += "Timeout waiting for prompt"
            error = True

    # if no errors continue on
    if not error:
        # parse status output and handle common errors
        try:
            output = output.decode("utf-8")
            uptime = parse_uptime(output)
            result = f"{task.host}: {uptime}"
            print(result)
            return result
        except AttributeError:
            result = f"{task.host}: match not found"

    print(result)
    return result


def recv_until_prompt(channel, prompt, timeout, nbytes=65535):
    output = b""
    for _ in range(timeout):
        if channel.recv_ready():
            output += channel.recv(nbytes)
        if prompt in output:
            return output
        time.sleep(1)
    raise TimeoutError(
        f"timed out in {timeout} seconds without seeing admin prompt:"
        f" \"{prompt.decode('utf-8')}\""
    )


def parse_uptime(status):
    """
    TODO:Handle additional outputs
    up 50 days, 11 min,
    up 50 days,  1:27,
    up 50 days, 12:27,
    """
    regex = r"up\s+(.+),\s+\d+\s+user"
    match = re.search(regex, status)
    return match.group(1)


def parse_config():
    yaml_dir = "yamls"

    if getattr(sys, "frozen", False):
        dirname = os.path.dirname(sys.executable)
    else:
        dirname = os.path.dirname(__file__)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-C",
        "--config_file",
        help="specify custom config file location",
        default=os.path.join(dirname, yaml_dir, "config.yaml"),
    )
    parser.add_argument(
        "-H",
        "--host_file",
        help="specify custom host file location",
        default=os.path.join(dirname, yaml_dir, "hosts.yaml"),
    )
    parser.add_argument(
        "-G",
        "--group_file",
        help="specify custom group file location",
        default=os.path.join(dirname, yaml_dir, "groups.yaml"),
    )
    parser.add_argument(
        "-D",
        "--defaults_file",
        help="specify custom defaults file location",
        default=os.path.join(dirname, yaml_dir, "defaults.yaml"),
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":

    config = parse_config()

    nr = InitNornir(
        config_file=config.config_file,
        inventory={
            "plugin": "nornir.plugins.inventory.simple.SimpleInventory",
            "options": {
                "host_file": config.host_file,
                "group_file": config.group_file,
                "defaults_file": config.defaults_file,
            },
        },
    )

    result = nr.run(task=get_ucos_uptime)
