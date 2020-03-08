# This includes utilities that can be used to inspect disks and
# partitions, as well as change them (with superuser privilege).

import json
import subprocess


def GetBlockInfo():
    output = subprocess.check_output(['lsblk', '--json'])
    return json.loads(output)
