from flask import Flask, render_template, jsonify
from github import Github
from pathlib import Path

import json

import github

app = Flask(__name__)

project_folder = Path(__file__).parent.resolve()
settings_path = f'{project_folder}/data/token.json'
default_settings = {
        "token": ""
    }

if not Path(settings_path).is_file():
    print(f'Creating token.json')
    with open(settings_path, 'a') as f:
        json.dump(default_settings, f, indent=2)

with open(settings_path, "r") as settings:
    settings = json.load(settings)

if not settings['token']:
    print(f'No token in {settings_path}! Please add it and try again.')

g = Github(settings['token'])
github_user = g.get_user().login

all_orgs_repos = []
workflows = []

orgs = g.get_user().get_orgs()
for org in orgs: 
    for repo in org.get_repos():
        all_orgs_repos.append(repo)

for repo in all_orgs_repos:
    for workflow in repo.get_workflows():
        workflows.append(workflow)

@app.route("/")
@app.route("/home")
def home_page():
    return render_template('home.html', user = f'{github_user}')

@app.route("/workflows")
def workflows_page():
    print(f"workflows is type: {type(workflows)}")
    return render_template('workflows.html', workflows = f'{workflows}')