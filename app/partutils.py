# This includes utilities that can be used to inspect disks and
# partitions, as well as change them (with superuser privilege).

import json
import subprocess


def _DetermineUsage(child):
    mountpoint = child['mountpoint']
    if mountpoint is None:
        return 'Unmounted'
    elif mountpoint.lower().find('swap') > -1:
        return 'Swap'
    return mountpoint


def GetBlockInfo(specified=None):
    '''Returns the block device info in the form below as a dictionary.

    devices:
      - name: /dev/sda
        size: 256 GB
    active:
      name: /dev/sda
      size: 256 GB
      parts:
        - usage: /
          fstype: ext4
          size: 128 GB
        - usage: swap
          fstype: swap
          size: 8 GB
    '''
    text = subprocess.check_output(['lsblk', '--json'])
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
            parts = []
            for child in device.get('children', []):
                usage = _DetermineUsage(child)

                # TODO(breakds): This is a fake fstype
                fstype = 'ext4'
                if usage == 'Swap':
                    fstype = 'swap'
                elif usage == 'Unmounted':
                    fstype = 'unknown'

                icon = 'folder green'
                if usage == '/boot':
                    icon = 'rocket green'
                if usage == 'Unmounted':
                    icon = 'red eye slash'
                elif usage == 'Swap':
                    icon = 'archive green'
                
                parts.append({
                    'usage': usage,
                    'fstype': fstype,
                    'size': child['size'],
                    'icon': icon,
                })
            active = {
                'name': devices[-1]['name'],
                'size': devices[-1]['size'],
                'parts': parts,
            }
    return {
        'devices': devices,
        'active': active,
    }
