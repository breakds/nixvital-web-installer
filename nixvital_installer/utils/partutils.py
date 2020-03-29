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


def _IsNVME(device):
    return device.lower().find('nvme') > -1


def _GetPart(device, num):
    if _IsNVME(device):
        return '{}p{}'.format(device, num)
    return '{}{}'.format(device, num)


def ExecutePartition(cfg, install_root):
    device = cfg.get('/', 'None')
    if device is None:
        return False

    install_root = pathlib.Path(install_root)

    try:
        # TODO(breakds): Check /proc/swap and swapoff everything, and umount everything.
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
        part_root = _GetPart(device, 3)
        part_swap = _GetPart(device, 2)
        part_boot = _GetPart(device, 1)
        subprocess.check_call(['parted', '-s', device, 'set', '1', 'boot', 'on'])
        subprocess.check_call(['mkfs.fat', part_boot, '-F', '32'])
        subprocess.check_call(['mkswap', part_swap])
        subprocess.check_call(['mkfs.ext4', '-F', part_root])
        try:
            subprocess.check_call(['umount', part_boot])
            subprocess.check_call(['umount', part_root])
        except subprocess.CalledProcessError:
            pass
        _Mount(part_root, install_root)
        _Mount(part_boot, pathlib.Path(install_root, 'boot'))
        subprocess.check_call(['swapon', part_swap])
    except subprocess.CalledProcessError as error:
        print(error)
        return False

    return True
    
