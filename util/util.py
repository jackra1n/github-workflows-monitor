from pathlib import Path
from util import store

import json

def prepare_files():
    # Create 'data' folder if it doesn't exist
    Path('data').mkdir(parents=True, exist_ok=True)

    # Create database file if it doesn't exist
    if not Path(store.DATABASE_URI).is_file():
        open(store.DATABASE_URI, 'a')

def prepare_terminal():
    default_settings = {
        "token": ""
    }
    project_folder = store.ROOT_DIR
    settings_path = f'{project_folder}/data/token.json'
    Path(f'{project_folder}/data').mkdir(parents=True, exist_ok=True)

    if not Path(settings_path).is_file():
        print(f'Creating token.json')
        with open(settings_path, 'a') as f:
            json.dump(default_settings, f, indent=2)