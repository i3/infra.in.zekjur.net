#!/usr/bin/python3

import struct
import json
import subprocess
import socket
import argparse
import time

# Workspaces in the format of 1:2:3, with negative integers ok.

# List of monitors, with x/y offset from center
centerScreen = "DVI-I-1"
monitors = { "DVI-D-2": (-1, 0), # Left at dock
             "DVI-I-1": ( 0, 0), # Center for docking station
             "DVI-D-1": ( 1, 0), # Right at dock
}

ipcheader = b'i3-ipc'
ipccmds = { 'COMMAND':        0,
            'GET_WORKSPACES': 1,
            'GET_OUTPUTS':    3,
            }

# Obtain socket
socketfile = subprocess.Popen(['/usr/bin/i3','--get-socket'],
                              stdout=subprocess.PIPE).communicate()[0].rstrip()

def socketCommand(mode, command=''):

    i3socket = socket.socket(socket.AF_UNIX)
    i3socket.connect(socketfile)
    i3socket.send( struct.pack("=6sLL" + str(len(command)) + "s", b'i3-ipc', len(command), ipccmds[mode], command.encode()) )
    reply = i3socket.recv(8192)

    data = struct.unpack('=ccccccLL',reply[:14])
    assert b''.join(data[0:6]) == b'i3-ipc'
    size = data[6]

    payload = struct.unpack("=ccccccLL" + str(size) + "s", reply)[8]

    i3socket.close()

    print(command)
    print(json.loads(payload.decode()))
    return json.loads(payload.decode())


def getOutputs():
    """
[{'active': True,
  'current_workspace': '0:0:0',
  'name': 'DVI-I-1',
  'primary': False,
  'rect': {'height': 1080, 'width': 1920, 'x': 1920, 'y': 0}},
 {'active': True,
  'current_workspace': '-1:-1:0',
  'name': 'DVI-D-1',
  'primary': False,
  'rect': {'height': 1080, 'width': 1920, 'x': 3840, 'y': 0}},
 {'active': True,
  'current_workspace': '-1:0:0',
  'name': 'DVI-D-2',
  'primary': False,
  'rect': {'height': 1080, 'width': 1920, 'x': 0, 'y': 0}},
 {'active': False,
  'current_workspace': None,
  'name': 'HDMI-1',
  'primary': False,
  'rect': {'height': 0, 'width': 0, 'x': 0, 'y': 0}}]
"""
    return socketCommand('GET_OUTPUTS')


def getWorkspaces():
    """
[{'focused': True,
  'name': '0:0:0',
  'num': 0,
  'output': 'DVI-I-1',
  'rect': {'height': 1061, 'width': 1920, 'x': 1920, 'y': 0},
  'urgent': False,
  'visible': True},
 {'focused': False,
  'name': '-1:0:0',
  'num': None,
  'output': 'DVI-D-2',
  'rect': {'height': 1061, 'width': 1920, 'x': 0, 'y': 0},
  'urgent': False,
  'visible': True},
 {'focused': False,
  'name': '1:0:0',
  'num': 1,
  'output': 'DVI-D-1',
  'rect': {'height': 1061, 'width': 1920, 'x': 3840, 'y': 0},
  'urgent': False,
  'visible': False},
 {'focused': False,
  'name': '-1:-1:0',
  'num': None,
  'output': 'DVI-D-1',
  'rect': {'height': 1061, 'width': 1920, 'x': 3840, 'y': 0},
  'urgent': False,
  'visible': True}]
"""
    return socketCommand('GET_WORKSPACES')


def changeWorkspaces( dx, dy, dz):

    outputs = getOutputs()
    workspaces = getWorkspaces()
    currentOutput   = [i for i in workspaces if i['focused'] == True ][0]['output']

    # Don't adjust based on data from every screen. Find center position and move it, then set the rest using offsets
    currentCenterWS = [i for i in workspaces if i['output']  == centerScreen and i['visible'] == True][0]['name']

    # Enforce tag format or reset position
    try:
        coords = [int(i) for i in currentCenterWS.strip("'").split('_')]
    except ValueError:
        coords = [0,0,0]

    # Change all outputs to a workspace uniquely named by output temporarily
    for output in monitors:
        socketCommand('COMMAND', "focus output " + output)
        socketCommand('COMMAND', "workspace "    + output)

    # Set each monitor by offset from center and the new delta
    for output in monitors:
        newWS = "{:d}_{:d}_{:d}".format(coords[0] + monitors[output][0] + dx,
                                        coords[1] + monitors[output][1] + dy,
                                        coords[2] + dz)
        socketCommand('COMMAND', "focus output " + output)
        socketCommand('COMMAND', "workspace "    + newWS)
        socketCommand('COMMAND', "move workspace to output " + output)

    # Restore focus
    socketCommand('COMMAND', "focus output " + currentOutput)


# MAIN
parser = argparse.ArgumentParser(description='Change i3 workspaces in a 3d space')
parser.add_argument('x', help='Delta X', nargs=1, type=int, default=0)
parser.add_argument('y', help='Delta Y', nargs=1, type=int, default=0)
parser.add_argument('z', help='Delta Z', nargs=1, type=int, default=0)
options = parser.parse_args()

changeWorkspaces(options.x[0], options.y[0], options.z[0])

