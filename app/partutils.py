# This includes utilities that can be used to inspect disks and
# partitions, as well as change them (with superuser privilege).

import json
import subprocess
import pathlib


MOUNT_LOCATIONS = ['/', '/boot', 'swap', '/home', '/var', '/opt']


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


def _Mount(disk, target):
    target.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(['mount', disk, target])


def ExecutePartition(cfg, install_root):
    device = cfg.get('/', 'None')
    if device is None:
        return False

    install_root = pathlib.Path(install_root)

    try:
        subprocess.check_call(['parted', '-s', device, 'mklabel', 'gpt'])
        subprocess.check_call(
            ['parted', '-s', '-a', 'optimal', device,
             'mkpart', 'ESP_BOOT', 'fat32', '0%', '512MB'])
        subprocess.check_call(
            ['parted', '-s', '-a', 'optimal', device,
             'mkpart', 'NIXOS_SWAP', 'linux-swap', '512MB', '8704MB'])
        subprocess.check_call(
            ['parted', '-s', '-a', 'optimal', device,
             'mkpart', 'NIXOS_SYS', 'ext4', '8704MB', '100%'])
        subprocess.check_call(['parted', '-s', device, 'set', '1', 'boot', 'on'])
        subprocess.check_call(['mkfs.fat', '{}1'.format(device), '-F', '32'])
        subprocess.check_call(['mkswap', '{}2'.format(device)])
        subprocess.check_call(['mkfs.ext4', '{}3'.format(device)])
        try:
            subprocess.check_call(['umount', '{}1'.format(device)])
            subprocess.check_call(['umount', '{}3'.format(device)])
        except subprocess.CalledProcessError:
            pass
        _Mount('{}3'.format(device), install_root)
        _Mount('{}1'.format(device), pathlib.Path(install_root, 'boot'))
        # TODO(breakds): Add "swapon".
    except subprocess.CalledProcessError as error:
        print(error)
        return False

    return True
    
