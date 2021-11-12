from util import store, util, db
from util.db import db_session, User, Organization
from src.forms import AddOrganizationForm, JenkinsApiForm

from flask import Flask, render_template, session, request, url_for, redirect, g, jsonify
from flask_github import GitHub
from pathlib import Path

import requests

SECRET_KEY = 'development key'
store.ROOT_DIR = Path(__file__).parent.resolve()

util.prepare_files()
db.create_database()

app = Flask(__name__)
app.config.from_object(__name__)

github = GitHub(app)

def get_all_user_orgs():
    if g.user is not None:
        all_orgs = []
        for org in github.get(f'/user/orgs'):
            all_orgs.append(org)
        for org in github.get(f'/users/{g.user.github_login}/orgs'):
            if org not in all_orgs:
                all_orgs.append(org)
        for org in Organization.query.filter_by(user_github_id=g.user.github_id).all():
            all_orgs.append(github.get(f'/orgs/{org.github_login}'))
        return all_orgs


# =========================
# Main app routes
# =========================

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', jenkins_url=session.get('jenkins_url'))

@app.route("/workflows")
def workflows():
    all_workflow_runs = []
    failed_runs = []
    for org in get_all_user_orgs():
        all_org_repos = github.get(f'/orgs/{org["login"]}/repos')
        for repo in all_org_repos:
            repo_workflows = github.get(f'/repos/{repo["full_name"]}/actions/runs')
            if repo_workflows['total_count'] > 0:
                run = repo_workflows['workflow_runs'][0]
                if run['conclusion'] == 'success':
                    all_workflow_runs.append(run)
                elif run['conclusion'] == 'failure':
                    failed_runs.append(run)
    return render_template('workflows.html', workflows=all_workflow_runs, failed_runs=failed_runs)

@app.route("/orgs", methods=['GET', 'POST'])
def orgs():
    form = AddOrganizationForm()
    if form.validate_on_submit():
        org = Organization(form.org_github_name.data, g.user.github_login)
        db_session.add(org)
        db_session.commit()
        return redirect(url_for('orgs'))
    orgs = get_all_user_orgs()
    return render_template('orgs.html', orgs=orgs, form=form)

@app.route("/<org_name>/repos")
def repos(org_name):
    repos = github.get(f'/orgs/{org_name}/repos')
    for repo in repos:
        repo["last_commit"] = github.get(f'/repos/{org_name}/{repo["name"]}/commits')[0]
    return render_template('repos.html', repos=repos, org_name=org_name)

@app.route("/repo/<owner_name>/<repo_name>")
def repo(owner_name, repo_name):
    repo = github.get(f'/repos/{owner_name}/{repo_name}')
    return render_template('repo.html', repo=repo)

@app.route("/missing-organizations")
def missing_organizations():
    return render_template('missing-organizations.html')

@app.route("/settings", methods=['GET', 'POST'])
def settings():
    form = JenkinsApiForm()
    if form.validate_on_submit():
        session['jenkins_url'] = form.jenkins_url.data
        return redirect(url_for('settings'))
    return render_template('settings.html', form=form, jenkins_url=session.get('jenkins_url'))

@app.route("/jenkins")
def jenkins():
    #fetch jenkins build jobs from url
    jenkins_url = session.get('jenkins_url')
    if jenkins_url is None:
        return redirect(url_for('settings'))
    jenkins_url = jenkins_url.rstrip('/')
    jenkins_response = requests.get(f'https://{jenkins_url}/api/json?pretty=true')
    if jenkins_response.status_code != 200:
        return render_template('jenkins.html', error='Error fetching Jenkins jobs')
    jenkins_json = jenkins_response.json()
    jenkins_jobs = jenkins_json['jobs']
    #fetch jenkins builds from url
    jenkins_builds = {}
    for job in jenkins_jobs:
        job_name = job['name']
        job_url = f'https://{jenkins_url}/job/{job_name}/api/json?pretty=true'
        job_response = requests.get(job_url)
        if job_response.status_code != 200:
            return render_template('jenkins.html', error='Error fetching Jenkins builds')
        job_json = job_response.json()
        jenkins_builds[job_name] = job_json['builds']
    return render_template('jenkins.html', jenkins_builds=jenkins_builds)

@app.route("/api/orgs")
def api_orgs():
    return jsonify(github.get(f'/user/orgs'))


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
        return github.authorize(scope="read:user,repo,read:org")
    else:
        return 'Already logged in'

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))
