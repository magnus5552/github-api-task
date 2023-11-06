import asyncio
import math
import re
import sys
import time
from collections import Counter
from itertools import chain

from aiolimiter import AsyncLimiter
from tqdm.asyncio import tqdm, tqdm_asyncio

import github_api
from github_api import GithubClient

page_expr = re.compile(r'&page=(\d*)')


async def get_commits_emails_by_page(repo_name: str,
                                     page: int,
                                     client: GithubClient,
                                     limiter):
    async with limiter:
        commits = await client.get_commits(repo_name, page)

    emails = [x['commit']['author']['email'] for x in commits
              if not x['commit']['message'].startswith('Merge')]
    return emails


async def get_commits_emails(repo_name: str, client: GithubClient):
    commits_count = await get_elements_count(
        f'https://api.github.com/repos/{repo_name}/commits', client)
    pages_count = roundup(commits_count)

    limiter = AsyncLimiter(100, 1)

    emails_by_pages = [asyncio.ensure_future(
        get_commits_emails_by_page(repo_name, page, client, limiter))
        for page in range(1, pages_count + 1)]
    emails = await asyncio.gather(*emails_by_pages)

    emails = chain.from_iterable(emails)
    return Counter(emails)


async def get_repos_by_page(org_name, page, client, progress_bar: tqdm):
    repos = await client.get_org_repos(org_name, page)
    progress_bar.update(len(repos))
    return [x['full_name'] for x in repos]


async def get_all_repos(org_name: str, client: GithubClient):
    repos_count = await get_elements_count(
        f'https://api.github.com/orgs/{org_name}/repos', client)
    pages_count = roundup(repos_count)

    with tqdm(desc='fetching repositories',
              total=repos_count,
              leave=False) as progress_bar:
        repos_by_page = []
        for page in range(1, pages_count + 1):
            repos_by_page.append(asyncio.ensure_future(
                get_repos_by_page(org_name, page, client, progress_bar)))

        repos_by_page = await asyncio.gather(*repos_by_page)
    return chain.from_iterable(repos_by_page)


async def get_elements_count(url: str, client: GithubClient):
    response = await client.session.get(url,
                                        params={'per_page': 1},
                                        timeout=20)
    if 'last' not in response.links:
        return 1
    match = page_expr.search(response.links['last']['url'])
    page = match[1] if match is not None else 1
    return int(page)


def roundup(x):
    return int(math.ceil(x / 100.0))


async def main(org_name: str):
    start = time.time()

    authors_count = Counter()
    async with GithubClient() as client:
        repos = await get_all_repos(org_name, client)
        commit_stats = [asyncio.ensure_future(get_commits_emails(repo, client))
                        for repo in repos]
        commit_stats = await tqdm_asyncio.gather(*commit_stats,
                                                 desc='processing repositories',
                                                 total=len(commit_stats),
                                                 leave=False)

    for stat in commit_stats:
        authors_count.update(stat)

    most_common = authors_count.most_common(100)
    for index, (author, count) in enumerate(most_common, start=1):
        print(f'{index}: {author} - {count}')

    print(f"--- {time.time() - start} seconds ---")


if __name__ == '__main__':
    organization_name = sys.argv[1]
    github_api.LOGGING_ENABLED = len(sys.argv) > 2 and sys.argv[2] == '--log'
    asyncio.run(main(organization_name))
