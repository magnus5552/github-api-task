import sys
from collections import Counter

from github_api import get_commits, get_org_repos, get_all_items


def get_commits_emails(repo_name: str):
    commits = get_all_items(lambda page: get_commits(repo_name, page))
    commits = filter(lambda x: not x['commit']['message'].startswith('Merge'), 
                     commits)
    emails = map(lambda x: x['commit']['author']['email'], commits)

    return emails


def get_all_repos(org_name: str):
    repos = get_all_items(lambda page: get_org_repos(org_name, page))
    return map(lambda x: x['full_name'], repos)


def main():
    org_name = sys.argv[1]

    authors_count = Counter()
    for repo in get_all_repos(org_name):
        authors_count.update(get_commits_emails(repo))

    most_common = authors_count.most_common(100)
    for index, (author, count) in enumerate(most_common, start=1):
        print(f'{index}: {author} - {count}')


if __name__ == '__main__':
    main()
