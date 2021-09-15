from util import store, util, db
from util.db import User, db_session

from flask import Flask, render_template, session, request, url_for, redirect, g
from flask_github import GitHub
from pathlib import Path

import json

SECRET_KEY = 'development key'
store.ROOT_DIR = Path(__file__).parent.resolve()

util.prepare_files()
db.create_database()

app = Flask(__name__)
app.config.from_object(__name__)

github = GitHub(app)


# =========================
# Main app routes
# =========================

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/workflows")
def workflows():
    orgs = github.get(f'/user/orgs')
    all_workflow_runs = []
    failed_runs = []
    for org in orgs:
        all_org_repos = github.get(f'/orgs/{org["login"]}/repos')
        for repo in all_org_repos:
            repo_workflows = github.get(f'/repos/{repo["full_name"]}/actions/runs')
            if repo_workflows['total_count'] > 0:
                for workflow in repo_workflows['workflow_runs']:
                    if workflow['conclusion'] == 'success':
                        all_workflow_runs.append(workflow)
                    elif workflow['conclusion'] == 'failure':
                        failed_runs.append(workflow)
    return render_template('workflows.html', workflows=all_workflow_runs, failed_runs=failed_runs)

@app.route("/orgs")
def orgs():
    orgs = github.get(f'/user/orgs')
    return render_template('orgs.html', orgs = orgs)

@app.route("/<org_name>/repos")
def repos(org_name):
    repos = github.get(f'/orgs/{org_name}/repos')
    return render_template('repos.html', repos=repos)

@app.route("/repo/<owner_name>/<repo_name>")
def repo(owner_name, repo_name):
    repo = github.get(f'/repos/{owner_name}/{repo_name}')
    return render_template('repo.html', repo=repo)


# =========================
# Github authentication stuff below
# =========================

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])
        if not g.user:
            session.pop('user_id')

@app.after_request
def after_request(response):
    db_session.remove()
    return response

@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token

@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    next_url = request.args.get('next') or url_for('home')
    if access_token is None:
        return redirect(next_url)

    user = User.query.filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
        db_session.add(user)

    user.github_access_token = access_token

    g.user = user
    github_user = github.get('/user')
    user.github_id = github_user['id']
    user.github_login = github_user['login']

    db_session.commit()

    session['user_id'] = user.id
    return redirect(next_url)

@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github.authorize(scope="user,read:org,repo")
    else:
        return 'Already logged in'

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))
