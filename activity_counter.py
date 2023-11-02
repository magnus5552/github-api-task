import asyncio
import sys
import time
from collections import Counter

import re
from itertools import chain

from github_api import get_all_items, GithubClient

page_expr = re.compile(r'&page=(\d*)')


async def get_commits_emails_by_page(repo_name: str,
                                     page: int,
                                     client: GithubClient):
    commits = await client.get_commits(repo_name, page)
    emails = [x['commit']['author']['email'] for x in commits
              if not x['commit']['message'].startswith('Merge')]
    return emails


async def get_commits_emails(repo_name: str, client: GithubClient):
    pages_count = await get_pages_count(f'https://api.github.com/repos/{repo_name}/commits', client)

    emails_by_pages = [asyncio.ensure_future(get_commits_emails_by_page
                                             (repo_name, page, client))
                       for page in range(1, pages_count + 1)]
    emails = await asyncio.gather(*emails_by_pages)
    emails = chain.from_iterable(emails)
    return Counter(emails)


async def get_all_repos(org_name: str, client: GithubClient):
    pages_count = await get_pages_count(
        f'https://api.github.com/org/{org_name}/repos', client)

    repos_by_page = \
        [asyncio.ensure_future(client.get_org_repos(org_name, page))
         for page in range(1, pages_count + 1)]
    repos_by_page = await asyncio.gather(*repos_by_page)
    return [x['full_name'] for repos in repos_by_page for x in repos]


async def get_pages_count(url: str, client: GithubClient):
    response = await client.session.get(url,
                                        params={'per_page': 100},
                                        timeout=20)
    if 'last' not in response.links:
        return 1
    match = page_expr.search(response.links['last']['url'])
    page = match[1] if match is not None else 1
    return int(page)


async def main():
    start = time.time()

    org_name = sys.argv[1]

    authors_count = Counter()
    async with GithubClient() as client:
        repos = await get_all_repos(org_name, client)

        commit_stats = [asyncio.ensure_future(get_commits_emails(repo, client))
                        for repo in repos]
        commit_stats = await asyncio.gather(*commit_stats)

    for stat in commit_stats:
        authors_count.update(stat)

    most_common = authors_count.most_common(100)
    for index, (author, count) in enumerate(most_common, start=1):
        print(f'{index}: {author} - {count}')

    print(f"--- {time.time() - start} seconds ---")


if __name__ == '__main__':
    asyncio.run(main())
