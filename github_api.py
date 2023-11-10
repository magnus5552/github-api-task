import asyncio
import os.path
import sys

import httpx

API_ENDPOINT = 'https://api.github.com'
HEADERS = {'Accept': 'application/vnd.github+json'}
LOGGING_ENABLED = False


def configure_session():
    session = httpx.AsyncClient(base_url=API_ENDPOINT,
                                headers=HEADERS,
                                event_hooks={'response': [log_response]},
                                timeout=httpx.Timeout(60, connect=600),
                                limits=httpx.Limits(max_keepalive_connections=100))
    if os.path.exists('SECRET_KEY'):
        with open('SECRET_KEY', 'r') as file:
            secret_key = file.read().replace('\n', '')
            session.headers['Authorization'] = f'Bearer {secret_key}'
    return session


async def log_response(response: httpx.Response):
    if not LOGGING_ENABLED:
        return

    content = await response.aread()

    elapsed = response.elapsed.total_seconds()
    if response.is_success:
        print('success', '-', elapsed, ':', response.url)
        return

    print('fail', '-', elapsed, ':', response.url, file=sys.stderr)
    print(content, file=sys.stderr)


class GithubClient:
    async def get(self, request: str, params=None, headers=None):
        await self.event.wait()
        request = self.session.build_request('GET', request,
                                             headers=headers,
                                             params=params)
        async with self.semaphore:
            response = await self.session.send(request)
            if 'retry-after' in response.headers:
                wait_time = int(response.headers['retry-after'])
                await self._wait_for_retry(wait_time)
                response = await self.session.send(request)

        if response.headers['X-RateLimit-Remaining'] == '0':
            raise httpx.HTTPError('Исчерпан лимит запросов')

        if response.status_code == 409:
            return []

        response.raise_for_status()
        return response.json()

    async def get_org_repos(self, organization: str, page: int):
        params = {'page': page, 'per_page': 100}
        return await self.get(f'/orgs/{organization}/repos', params=params)

    async def get_commits(self, repo: str, page: int):
        params = {'page': page, 'per_page': 100}
        return await self.get(f'/repos/{repo}/commits', params=params)

    async def _wait_for_retry(self, delay):
        self.event.clear()
        await asyncio.sleep(delay)
        self.event.set()

    async def __aenter__(self):
        self.semaphore = asyncio.Semaphore(100)
        self.event = asyncio.Event()
        self.event.set()
        self.session = configure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
