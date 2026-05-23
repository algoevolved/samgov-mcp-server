import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

BASE_URL = "https://api.sbir.gov/public/api/v1"
_DEFAULT_TIMEOUT = 30.0

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)), reraise=True)
async def search_solicitations(keywords=None, agency=None, phase=None, open_only=True, limit=20, start=0):
    params = {"rows": min(limit, 100), "start": start}
    if keywords: params["keyword"] = keywords
    if agency: params["agency"] = agency
    if phase: params["phase"] = phase
    if open_only: params["open"] = 1
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/solicitations", params=params)
        resp.raise_for_status()
        return resp.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)), reraise=True)
async def get_award_info(company=None, agency=None, keywords=None, year_from=None, limit=20, start=0):
    params = {"rows": min(limit, 100), "start": start}
    if company: params["firm"] = company
    if agency: params["agency"] = agency
    if keywords: params["keyword"] = keywords
    if year_from: params["year"] = year_from
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/awards", params=params)
        resp.raise_for_status()
        return resp.json()
