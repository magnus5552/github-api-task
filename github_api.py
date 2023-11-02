import os.path

import requests as r

API_ENDPOINT = 'http://api.github.com'
HEADERS = {'Accept': 'application/vnd.github+json'}

session = r.session()
session.headers.update(HEADERS)

if os.path.exists('SECRET_KEY'):
    with open('SECRET_KEY') as file:
        SECRET_KEY = file.read()
        session.headers['Authorization'] = f'Bearer {SECRET_KEY}'


def get(request: str, params=None, headers=None):
    response = session.get(API_ENDPOINT + request,
                           headers=headers,
                           params=params)
    response.raise_for_status()
    return response.json()


def get_org_repos(org_name: str, page: int):
    params = {'page': page, 'per_page': 100}
    return get(f'/orgs/{org_name}/repos', params=params)


def get_commits(repo_name: str, page: int):
    params = {'page': page, 'per_page': 100}
    return get(f'/repos/{repo_name}/commits', params=params)


def get_all_items(func):
    returned_count = 100
    page = 1
    while returned_count == 100:
        items = func(page)
        yield from items

        returned_count = len(items)
        page += 1
