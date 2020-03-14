import pathlib

import vitalutils

def GetMachineList(vital_dir):
    result = []
    machine_root = pathlib.Path(vital_dir, 'machines')
    for candidate in machine_root.glob('*.nix'):
        result.append(str(candidate.relative_to(machine_root)))
    return result
