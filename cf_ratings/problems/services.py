import requests
from django.conf import settings

CF_API_BASE = 'https://codeforces.com/api'


class CodeforcesAPIError(Exception):
    pass


def fetch_user_info(handle):
    url = f"{CF_API_BASE}/user.info"
    params = {'handles': handle}
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') != 'OK':
            raise CodeforcesAPIError('API returned non-OK status')
        return data['result'][0]
    except requests.RequestException as e:
        raise CodeforcesAPIError(str(e))


def fetch_problem_by_id(problem_id):
    # problem_id is like 2184G; split into numeric prefix and alpha suffix
    import re
    m = re.match(r'^(\d+)([A-Za-z]+)$', problem_id)
    if not m:
        raise CodeforcesAPIError('Invalid problem id format')
    contest_id, index = m.group(1), m.group(2)
    url = f"{CF_API_BASE}/problemset.problems"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') != 'OK':
            raise CodeforcesAPIError('API returned non-OK status')
        problems = data['result']['problems']
        for p in problems:
            if str(p.get('contestId')) == contest_id and p.get('index').upper() == index.upper():
                return p
        raise CodeforcesAPIError('Problem not found on Codeforces')
    except requests.RequestException as e:
        raise CodeforcesAPIError(str(e))
