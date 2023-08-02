from flask import Flask, render_template, request, redirect, url_for
import json
from fuzzywuzzy import fuzz, process
from collections import defaultdict
import os

JSON_PATH = 'data/protocol_mapping.json'
GITHUB_DATA_PATH = 'data/crypto_ecosystems.json'

app = Flask(__name__)


def flatten_github_data(projects):
    flattened_orgs = []
    for project in projects:
        github_orgs = project.get('github_organizations', [])
        flattened_orgs.extend(github_orgs)
    flattened_orgs = set(flattened_orgs)
    orgs = [x.replace('https://github.com/','').lower() for x in flattened_orgs]
    return orgs


def find_closest_matches(name, orgs, num_matches=10):
    matches = [(org,100) for org in orgs if name.lower() in org.lower()]
    closest_matches = process.extract(name, orgs, limit=num_matches, scorer=fuzz.token_sort_ratio)
    matches.extend(closest_matches)
    matches.sort(key=lambda x: x[1], reverse=True)
    repo_names = []
    for repo,_ in matches:
        if repo not in repo_names:
            repo_names.append(repo)
    return repo_names


@app.route('/', methods=['GET', 'POST'])
def home():
    with open(JSON_PATH) as f:
        data = json.load(f)

    with open(GITHUB_DATA_PATH) as f:
        github_data = json.load(f)

    github_orgs = flatten_github_data(github_data)

    # Compute summary stats
    total_projects = len(data)
    projects_with_actual_repo = sum('actual_repo' in entry for entry in data)
    projects_without_actual_repo = total_projects - projects_with_actual_repo

    # Filter out projects that already have an 'actual_repo'
    projects = sorted([entry['project'] for entry in data if 'actual_repo' not in entry], key=str.lower)

    if request.method == 'POST':
        project_name = request.form.get('project')
        repo_name = request.form.get('repo')
        if project_name and repo_name and repo_name != 'unknown':
            for project in data:
                if project['project'] == project_name:
                    project['actual_repo'] = repo_name
                    break
        elif repo_name == 'unknown':
            repo_name = request.form.get('custom_repo')
            if repo_name:  # if custom_repo is not blank
                for project in data:
                    if project['project'] == project_name:
                        project['actual_repo'] = repo_name
                        break
        with open(JSON_PATH, 'w') as f:
            json.dump(data, f, indent=4)

        # Redirect to the next project without 'actual_repo'
        if project_name in projects:
            current_index = projects.index(project_name)
            try:
                next_project = projects[current_index + 1]
            except IndexError:
                next_project = None  # if we're at the end of the list
        else:
            next_project = None  # if the current project isn't in the list
        return redirect(url_for('home', project=next_project))  # if next_project is None, we will be redirected to the homepage

    if request.method == 'GET' and 'project' in request.args:
        selected_project = request.args['project']
        repos = find_closest_matches(selected_project, github_orgs)
        selected_repo = request.args.get('repo', '')
    else:
        selected_project = None
        repos = []
        selected_repo = ''

    return render_template(
        'home.html', 
        projects=projects, 
        repos=repos, 
        selected_project=selected_project, 
        selected_repo=selected_repo, 
        github_link='https://github.com/' + selected_repo if selected_repo else '#', projects_with_actual_repo=projects_with_actual_repo, 
        projects_without_actual_repo=projects_without_actual_repo
        )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 4444)))
