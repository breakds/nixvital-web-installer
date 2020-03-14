import pathlib
import subprocess
import shutil

import vitalutils

def GetMachineList(vital_dir):
    result = []
    machine_root = pathlib.Path(vital_dir, 'machines')
    for candidate in machine_root.glob('*.nix'):
        result.append(str(candidate.relative_to(machine_root)))
    return result

def GenerateHardwareConfig(install_root):
    pathlib.Path(install_root, 'etc', 'nixos').mkdir(parents=True, exist_ok=True)
    ret = subprocess.run(['nixos-generate-config', '--root', install_root,
                          '--show-hardware-config'], capture_output=True)

    hardware_config = pathlib.Path(install_root, 'etc', 'nixos',
                                   'hardware-configuration.nix')

    with open(hardware_config, 'w') as out:
        out.write(ret.stdout.decode('utf-8'))


def SetupNixvital(install_root, vital_dir):
    source = pathlib.Path(vital_dir)
    target = pathlib.Path(install_root, 'opt/nixvital')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)

    vital_symlink = pathlib.Path(install_root, 'etc/nixos/nixvital')
    vital_symlink.parent.mkdir(parents=True, exist_ok=True)
    if vital_symlink.exists():
        vital_symlink.unlink()
    vital_symlink.symlink_to(pathlib.Path('../../opt/nixvital'))


def RewriteConfiguration(install_root, username, machine, hostname):
    # TODO(breakds) Use nixos-version to get the NixOS version first
    #   ret = subprocess.run(['nixos-version'], capture_output=True)
    #   print(ret.stdout)

    with open('/etc/machine-id', 'r') as f:
        machine_id = f.read(8)

    config_path = pathlib.Path(install_root, 'etc/nixos/configuration.nix')
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as out:
        out.write('{ config, pkgs, ... }:\n\n')
        out.write('{\n')
        out.write('  imports = [\n')
        out.write('    ./hardware-configuration.nix\n')
        out.write('    ./nixvital/machines/{}\n'.format(machine))
        out.write('  ];\n\n')
        out.write('  vital.mainUser = "{}";\n'.format(username))
        out.write('  networking.hostName = "{}";\n'.format(hostname))
        out.write('  networking.hostId = "{}";\n'.format(machine_id))
        out.write('\n')
        out.write('  # This value determines the NixOS release with which your system is to be\n')
        out.write('  # compatible, in order to avoid breaking some software such as database\n')
        out.write('  # servers. You should change this only after NixOS release notes say you\n')
        out.write('  # should.\n')
        out.write('  system.stateVersion = "19.09"; # Did you read the comment?\n')
        out.write('}\n')


def Message(scenario=None):
    return {
        'accent': 'positive',
        'header': 'Configuration generated successfully',
        'text': 'Please run `sudo nixos-install` in /mnt to finish.',
    }
