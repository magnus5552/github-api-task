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
from cmd_parser import configure_parser
from github_api import GithubClient

page_expr = re.compile(r'&page=(\d*)')


async def get_commits_emails_by_page(repo: str,
                                     page: int,
                                     client: GithubClient,
                                     limiter):
    async with limiter:
        commits = await client.get_commits(repo, page)

    emails = [x['commit']['author']['email'] for x in commits
              if not x['commit']['message'].startswith('Merge')]
    return emails


async def get_commits_emails(repo: str, client: GithubClient):
    commits_count = await get_elements_count(
        f'https://api.github.com/repos/{repo}/commits', client)
    pages_count = roundup(commits_count)

    limiter = AsyncLimiter(100, 1)

    emails_by_pages = [asyncio.ensure_future(
        get_commits_emails_by_page(repo, page, client, limiter))
        for page in range(1, pages_count + 1)]
    emails = await asyncio.gather(*emails_by_pages)

    emails = chain.from_iterable(emails)
    return Counter(emails)


async def get_repos_by_page(organization, page, client, progress_bar: tqdm):
    repos = await client.get_org_repos(organization, page)
    progress_bar.update(len(repos))
    return [x['full_name'] for x in repos]


async def get_all_repos(organization: str, client: GithubClient):
    repos_count = await get_elements_count(
        f'https://api.github.com/orgs/{organization}/repos', client)
    pages_count = roundup(repos_count)

    with tqdm(desc='fetching repositories',
              total=repos_count,
              leave=False) as progress_bar:
        repos_by_page = []
        for page in range(1, pages_count + 1):
            repos_by_page.append(asyncio.ensure_future(
                get_repos_by_page(organization, page, client, progress_bar)))

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


async def print_top_users(organization: str, count: int):
    authors_count = Counter()
    async with GithubClient() as client:
        repos = await get_all_repos(organization, client)
        commit_stats = [asyncio.ensure_future(get_commits_emails(repo, client))
                        for repo in repos]
        commit_stats = await tqdm_asyncio.gather(*commit_stats,
                                                 desc='processing repositories',
                                                 total=len(commit_stats),
                                                 leave=False)

    for stat in commit_stats:
        authors_count.update(stat)

    most_common = authors_count.most_common(count)
    for index, (author, count) in enumerate(most_common, start=1):
        print(f'{index}: {author} - {count}')


if __name__ == '__main__':
    parser = configure_parser()
    args = parser.parse_args()

    github_api.LOGGING_ENABLED = args.log

    start = time.time()
    asyncio.run(print_top_users(args.organization, args.n))
    print(f"--- {time.time() - start} seconds ---")
