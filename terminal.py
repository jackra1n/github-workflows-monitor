from util import terminal_colors as clr

from github import Github

import time
import json

settings_path = f'./data/token.json'

with open(settings_path, "r") as settings:
    settings = json.load(settings)

if not settings['token']:
    print(f'No token in {settings_path}! Please add it and try again.')
    print('https://github.com/settings/tokens')
    exit()

g = Github(settings['token'])

all_orgs_repos = []
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
    try:
        last_run = repo.get_workflow_runs()[0]
        latest_runs.append(last_run)
        if last_run.conclusion != 'success':
            latest_runs_failed.append(last_run)
    except IndexError:
        pass
toc = time.perf_counter()
print(f"Found {len(latest_runs)} workflows. Took {toc - tic:0.4f} seconds\n")

end = time.time()
print(f'Total: {end - start:0.4f}s')

if len(latest_runs_failed) > 0:
    print(f'{clr.BOLD}{clr.UNDERLINE}There are failed workflows!{clr.ENDC}')
    for failed_run in latest_runs_failed:
        print(f'{clr.FAIL} {failed_run.repository.name:24s} {clr.ENDC} {failed_run.html_url}')
