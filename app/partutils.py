# This includes utilities that can be used to inspect disks and
# partitions, as well as change them (with superuser privilege).

import json
import subprocess


def _ConstructPart(child):
    name = '/dev/{}'.format(child['name'])
    fstype = child['fstype'] if child['fstype'] else 'Unknown'
    size = child['size']
    mountpoint = child['mountpoint'] if child['mountpoint'] else 'unmounted'
    label = child['label'] if child['label'] else 'NOLABEL'

    icon = 'folder'
    if mountpoint.lower().find('swap') > -1:
        icon = 'archive'

    return {
        'name': name,
        'fstype': fstype,
        'size': size,
        'mountpoint': mountpoint,
        'label': label,
        'icon': icon,
    }


def GetBlockInfo(specified=None):
    '''Returns the block device info in the form below as a dictionary.

    devices:
      - name: /dev/sda
        size: 256 GB
    active:
      name: /dev/sda
      size: 256 GB
      parts:
        - name: /dev/sda1
          fstype: ext4
          size: 128G
          mountpoint: /home
          label: NIXOS_HOME
          icon: folder
        - name: /dev/sda2
          ...
    '''
    text = subprocess.check_output([
        'lsblk', '-oNAME,SIZE,FSTYPE,TYPE,LABEL,MOUNTPOINT', '--json'])
    parsed = json.loads(text)

    devices = []
    active = None
    for device in parsed['blockdevices']:
        if device['type'] != 'disk':
            continue
        devices.append({
            'name': '/dev/{}'.format(device['name']),
            'size': device['size'],
            'active': '',
        })

        if (specified is None and active is None) or specified == devices[-1]['name']:
            devices[-1]['active'] = 'active blue'
            active = {
                'name': devices[-1]['name'],
                'size': devices[-1]['size'],
                'parts': [_ConstructPart(child) for child in device.get('children', [])],
            }
    return {
        'devices': devices,
        'active': active,
    }
