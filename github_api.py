import os.path

import httpx

API_ENDPOINT = 'https://api.github.com'
HEADERS = {'Accept': 'application/vnd.github+json'}


async def get_all_items(func):
    returned_count = 100
    page = 1
    while returned_count == 100:
        items = await func(page)
        for item in items:
            yield item

        returned_count = len(items)
        page += 1


def configure_session():
    session = httpx.AsyncClient(headers=HEADERS)
    if os.path.exists('SECRET_KEY'):
        with open('SECRET_KEY') as file:
            secret_key = file.read()
            session.headers['Authorization'] = f'Bearer {secret_key}'
    return session


class GithubClient:

    async def get(self, request: str, params=None, headers=None):
        try:
            print('PENDING -', request, params)
            response = await self.session.get(API_ENDPOINT + request,
                                              headers=headers,
                                              params=params,
                                              timeout=20)
            response.raise_for_status()
            return response.json()
        except:
            print('FAILED -', request, params)
            raise

    async def get_org_repos(self, org_name: str, page: int):
        params = {'page': page, 'per_page': 100}
        return await self.get(f'/orgs/{org_name}/repos', params=params)

    async def get_commits(self, repo_name: str, page: int):
        params = {'page': page, 'per_page': 100}
        return await self.get(f'/repos/{repo_name}/commits', params=params)

    async def __aenter__(self):
        self.session = configure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
