from github import Github
from pathlib import Path

import time
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
    print('https://github.com/settings/tokens')
    exit()

g = Github(settings['token'])

all_orgs_repos = []
workflows = []
latest_runs = []
latest_runs_failed = []

start = time.time()
orgs = g.get_user().get_orgs()

print("Getting all repos...")
tic = time.perf_counter()
for org in orgs: 
    all_orgs_repos.extend(org.get_repos())
toc = time.perf_counter()
print(f"Found {len(all_orgs_repos)} repos. Took {toc - tic:0.4f} seconds\n")

print("Getting all workflows...")
tic = time.perf_counter()
for repo in all_orgs_repos:
    workflows.extend(repo.get_workflows())
toc = time.perf_counter()
print(f"Found {len(workflows)} workflows. Took {toc - tic:0.4f} seconds\n")

print("Checking workflow runs...")
tic = time.perf_counter()
for workflow in workflows:
    runs = workflow.get_runs()
    try:
        latest_runs.append(runs[0])
        if runs[0].conclusion != 'success':
            latest_runs_failed.append(runs[0])
    except IndexError:
        pass
toc = time.perf_counter()
print(f"Took {toc - tic:0.4f} seconds\n")

end = time.time()
print(f'Total: {end - start:0.4f}s')

if len(latest_runs_failed) > 0:
    print(f'{bcolors.BOLD}{bcolors.UNDERLINE}There are failed workflows!{bcolors.ENDC}')
    for failed_run in latest_runs_failed:
        print(f'{bcolors.FAIL} {failed_run.repository.name:24s} {bcolors.ENDC} {failed_run.html_url}')
