from github import Github
from pathlib import Path

import json

project_folder = Path(__file__).parent.resolve()
settings_path = f'{project_folder}/data/token.json'
default_settings = {
        "token": ""
    }

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

Path(f'{project_folder}/data').mkdir(parents=True, exist_ok=True)

if not Path(settings_path).is_file():
    print(f'Creating token.json')
    with open(settings_path, 'a') as f:
        json.dump(default_settings, f, indent=2)

with open(settings_path, "r") as settings:
    settings = json.load(settings)

if not settings['token']:
    print(f'No token in {settings_path}! Please add it and try again.')
    exit()

g = Github(settings['token'])

orgs = g.get_user().get_orgs() 
all_orgs_repos = []
workflows = []
latest_runs = []
latest_runs_failed = []

for org in orgs: 
    for repo in org.get_repos():
        all_orgs_repos.append(repo)

for repo in all_orgs_repos:
    for workflow in repo.get_workflows():
        workflows.append(workflow)

for workflow in workflows:
    runs = workflow.get_runs()
    try:
        latest_runs.append(runs[0])
        if runs[0].conclusion != 'success':
            latest_runs_failed.append(runs[0])
    except IndexError:
        pass

if len(latest_runs_failed) > 0:
    print(f'{bcolors.BOLD}{bcolors.UNDERLINE}There are failed workflows!{bcolors.ENDC}')
    for failed_run in latest_runs_failed:
        print(f'{bcolors.FAIL} {failed_run.repository.name}: {bcolors.ENDC} {failed_run.html_url}')
