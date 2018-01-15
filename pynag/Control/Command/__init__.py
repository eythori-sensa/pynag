# -*- coding: utf-8 -*-
#
# pynag - Python Nagios plug-in and configuration environment
# Copyright (C) 2011 Pall Sigurdsson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
The Command module is capable of sending commands to Nagios via
the configured communication path.
"""

from __future__ import absolute_import
import time
import os

from pynag.Parsers import main
from pynag.Parsers import livestatus

import pynag.errors
from pynag.Control.Command import autogenerated_commands as __autogenerated_commands
from six.moves import map

path_to_command_file = None


class CommandError(pynag.errors.PynagError):
    """Base class for errors in this module."""


def find_command_file(cfg_file=None):
    """
    Returns path to nagios command_file by looking at what is defined in nagios.cfg

    Args:
        cfg_file (str): Path to nagios.cfg configuration file

    Returns:
        str. Path to the nagios command file

    Raises:
        CommandError

    """
    global path_to_command_file

    # If we have been called before, the path should be cached in a global variable
    if path_to_command_file:
        return path_to_command_file

    # If we reach here, we have to parse nagios.cfg to find path
    # to our command file
    main_config = main.MainConfig(cfg_file)
    command_file = main_config.get('command_file')

    if not command_file:
        raise CommandError("command_file not found in your nagios.cfg (%s)" % main_config.filename)

    path_to_command_file = command_file
    return command_file


def send_command(command_id, command_file=None, timestamp=None, *args):
    """
    Send one specific command to the command pipe

    Args:
        command_id (str): Identifier string of the nagios command Eg: ``ADD_SVC_COMMENT``

        command_file (str): Path to nagios command file.

        timestamp (int): Timestamp in time_t format of the time when the external command was sent to the command file. If 0 of None, it will be set to time.time(). Default 0.

        args: Command arguments.

    """
    if not timestamp:
        timestamp = time.time()
    timestamp = int(timestamp)
    command_arguments = list(map(str, args))
    command_arguments = ";".join(command_arguments)
    command_string = "[%s] %s;%s" % (timestamp, command_id, command_arguments)
    try:
        if not command_file:
            command_file = find_command_file()
        _write_to_command_file(command_file, command_string)
    except Exception:
        _write_to_livestatus(command_string)


def _write_to_livestatus(command_string):
    """ Send a specific command to mk-livestatus

    See http://nagios.sourceforge.net/docs/nagioscore/3/en/extcommands.html for details

    Args:
        command_string (str): String the will be sent as a livestatus command.
    """
    livestatus_instance = livestatus.Livestatus()
    livestatus_instance.query("COMMAND %s" % command_string)


def _write_to_command_file(command_file, command_string=""):
    """ Send a specific command to nagios command pipe.

    See http://nagios.sourceforge.net/docs/nagioscore/3/en/extcommands.html for details

    Args:
        command_file (str): Path to the Nagios command file.
        command_string (str): String that will be written to the command file
                              and executed as a Nagios external command.
    """
    try:
        f = open(command_file, 'a')
        f.write(command_string + '\n')
        f.close()
    except OSError as e:
        fd = os.open(command_file, os.O_WRONLY | os.O_APPEND)
        command_string = command_string + '\n'
        if isinstance(command_string, str):
            command_string = command_string.encode()
        os.write(fd, command_string)
        os.close(fd)


# Everything in autogenerated_commands gets imported directly into this module.
filename = __autogenerated_commands.__file__
if filename.endswith('.pyc'):
    filename = filename.strip('c')
exec(compile(open(filename).read(), filename, 'exec'))
