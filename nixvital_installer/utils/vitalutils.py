import shutil
import pathlib
from git import Repo

DEFAULT_REPO = 'https://github.com/breakds/nixvital.git'

def HasNixvitalDir(parent_dir):
    vital_dir = pathlib.Path(parent_dir, 'nixvital')
    return vital_dir.exists() and vital_dir.is_dir()
        

def CloneNixvital(parent_dir, url):
    # Ensure parent directory
    pathlib.Path(parent_dir).mkdir(parents=True, exist_ok=True)

    # Clone if nixvital is not there yet
    vital_dir = pathlib.Path(parent_dir, 'nixvital')
    if vital_dir.exists():
        shutil.rmtree(vital_dir)
    # TODO(breakds): Check whether clone is successful
    # TODO(breakds): Chmod of the local repo to owner = uid 1000
    repo = Repo.clone_from(url, vital_dir)
    return vital_dir


def Message(scenario=None):
    if scenario == 'success':
        return {
            'accent': 'positive',
            'header': 'You now have a local nixvital repo cloned.',
            'text': 'Please proceed to the final step below',
        }
    elif scenario == 'fail':
        return {
            'accent': 'negative',
            'header': 'Clone failed',
            'text': 'Please correct the url and clone it again.',
        }
    return {
        'accent': 'negative',
        'header': 'You do not have a local nixvital repo cloned.',
        'text': 'Please set the url and clone it again.',
    }
        
