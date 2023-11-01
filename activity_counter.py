import sys
from collections import Counter

from github_api import get_commits, email_expr, get_organization_repos


def get_commits_authors_count(repo_name: str):
    returned_count = 100
    page = 1
    all_authors = Counter()
    while returned_count == 100:
        commits = get_commits(repo_name, page)
        authors = [x.value for x in email_expr.find(commits)]
        all_authors.update(authors)

        returned_count = len(authors)
        page += 1
    return all_authors


if __name__ == '__main__':
    authors_count = Counter()
    for repo in get_organization_repos(sys.argv[1]):
        authors_count.update(get_commits_authors_count(repo))

    most_common = authors_count.most_common(100)
    for index, (author, count) in enumerate(most_common, start=1):
        print(f'{index}: {author} - {count}')