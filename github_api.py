import os.path
import sys
from collections import Counter

import requests as r
from jsonpath_ng.ext import parse

API_ENDPOINT = 'http://api.github.com'
HEADERS = {'Accept': 'application/vnd.github+json'}
email_expr = parse(f'$[*].payload.commits[*].author.email')

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


def get_repo_contibutors(repo_name: str, page: int):
    params = {'page': page, 'per_page': 100}
    response = get(f'/repos/{repo_name}/contributors', params=params)
    return {x['login']: x['contributions'] for x in response}


def get_commits_authors_count(repo_name: str):
    returned_count = 100
    page = 1
    all_authors = {}
    while returned_count == 100:
        authors = get_repo_contibutors(repo_name, page)
        all_authors.update(authors)

        returned_count = len(authors)
        page += 1
    return all_authors


def get_user_events(username, page):
    params = {'page': page, 'per_page': 100}
    return get(f'/users/{username}/events/public', params=params)


def get_author_email(login: str):
    recv = 100
    page = 1
    email = None
    while recv == 100:
        response = get_user_events(login, page)
        emails = email_expr.find(response)
        if len(emails) > 0:
            email = emails[0].value
            break
        page += 1
        recv = len(response)
    return email


if __name__ == '__main__':
    authors_count = Counter()
    for repo in get_organization_repos(sys.argv[1]):
        authors_count.update(get_commits_authors_count(repo))
    most_common = authors_count.most_common(100)
    for author, count in most_common:
        found_email = get_author_email(author)
        print(author if found_email is None else found_email, count)
