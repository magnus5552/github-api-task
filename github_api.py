import asyncio
import functools
import os.path
import sys
import time

import httpx

API_ENDPOINT = 'https://api.github.com'
HEADERS = {'Accept': 'application/vnd.github+json'}
LOGGING_ENABLED = False


def configure_session():
    session = httpx.AsyncClient(headers=HEADERS)
    if os.path.exists('SECRET_KEY'):
        with open('SECRET_KEY') as file:
            secret_key = file.read()
            session.headers['Authorization'] = f'Bearer {secret_key}'
    return session


def log(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not LOGGING_ENABLED:
            return await func(self, *args, **kwargs)

        start = time.time()
        try:
            result = await func(self, *args, **kwargs)
            print('success', '-', time.time() - start, ':', func.__name__, *args, **kwargs)
            return result
        except httpx.HTTPStatusError as e:
            print('fail', func.__name__, *args, **kwargs, file=sys.stderr)
            print(e.response.text, file=sys.stderr)
            raise

    return wrapper


class GithubClient:

    async def get(self, request: str, params=None, headers=None):
        await self.event.wait()
        async with self.semaphore:
            response = await self.session.get(API_ENDPOINT + request,
                                              headers=headers,
                                              params=params)
            if 'retry-after' in response.headers:
                wait_time = int(response.headers['retry-after'])
                self.event.clear()
                await asyncio.sleep(wait_time)
                self.event.set()
                response = await self.session.get(API_ENDPOINT + request,
                                                  headers=headers,
                                                  params=params)
        response.raise_for_status()
        return response.json()

    @log
    async def get_org_repos(self, org_name: str, page: int):
        params = {'page': page, 'per_page': 100}
        return await self.get(f'/orgs/{org_name}/repos', params=params)

    @log
    async def get_commits(self, repo_name: str, page: int):
        params = {'page': page, 'per_page': 100}
        return await self.get(f'/repos/{repo_name}/commits', params=params)

    async def __aenter__(self):
        self.semaphore = asyncio.Semaphore(100)
        self.event = asyncio.Event()
        self.event.set()
        self.session = configure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
