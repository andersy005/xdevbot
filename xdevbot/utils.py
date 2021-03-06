import logging
from typing import List, Tuple, Union

import yaml
from aiohttp import ClientSession, ClientTimeout

logger = logging.getLogger('xdevbot')


def repo_fullname_from_url(url: str) -> str:
    return '/'.join(url.split('/')[-2:])


def split_issue_ref(ref: str) -> Tuple[str]:
    s = ref.split('/')
    return s[-4], s[-3], int(s[-1])


def refs_from_note(note: str) -> str:
    refs = set()
    for word in note.split():
        s = word.split('/')
        if (
            len(s) == 7
            and s[0].lower() in ('http:', 'https:')
            and s[1] == ''
            and s[2].lower() == 'github.com'
            and s[5].lower() in ('issues', 'pull')
        ):
            try:
                int(s[6])
            except ValueError:
                continue
            else:
                refs.add(word)
    return list(refs)


async def log_rate_limits(
    category: Union[str, List[str]] = 'core',
    token: str = None,
    timeout: int = 60,
) -> dict:
    if isinstance(category, str):
        category = [category]
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'token {token}'
    timeout = ClientTimeout(total=timeout)
    async with ClientSession(headers=headers, timeout=timeout) as session:
        response = await session.get('https://api.github.com/rate_limit')
        if response.status == 200:
            rates = await response.json()
            for k in category:
                r_k = rates['resources'][k]
                msg = (
                    f"{k.upper()} Rate Limits: {r_k['remaining']} remaining of {r_k['limit']} total"
                )
                logger.info(msg)
        else:
            logger.warning(f'Failed to retrieve rate limits [{response.status}]')


async def read_remote_yaml(url: str, timeout: int = 60):
    timeout = ClientTimeout(total=timeout)
    async with ClientSession(timeout=timeout) as session:
        response = await session.get(url)
        if response.status != 200:
            raise RuntimeError(f'Failed to read config file: {response.status}')
        text = await response.text()
    return yaml.safe_load(text)
