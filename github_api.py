import os.path

import requests as r
from jsonpath_ng.ext import parse

API_ENDPOINT = 'http://api.github.com'
HEADERS = {'Accept': 'application/vnd.github+json'}
email_expr = parse(f'$[*].commit.author.email')

if os.path.exists('SECRET_KEY'):
    with open('SECRET_KEY') as file:
        SECRET_KEY = file.read()
        HEADERS['Authorization'] = f'Bearer {SECRET_KEY}'


def get(request: str, params=None, headers=None):
    prep_headers = HEADERS.copy().update(headers) \
        if headers is not None \
        else HEADERS
    response = r.get(API_ENDPOINT + request,
                     headers=prep_headers,
                     params=params)
    response.raise_for_status()
    return response.json()


def get_organization_repos(org_name: str):
    response = get(f'/orgs/{org_name}/repos')
    return [x['full_name'] for x in response]


def get_commits(repo_name: str, page: int):
    params = {'page': page, 'per_page': 100}
    return get(f'/repos/{repo_name}/commits', params=params)
