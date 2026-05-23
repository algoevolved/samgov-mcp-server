import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import settings

BASE_URL = "https://api.sam.gov/prod"
_DEFAULT_TIMEOUT = 30.0

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)), reraise=True)
async def search_opportunities(keywords=None, agency=None, naics_code=None, set_aside=None,
                               notice_type=None, posted_from=None, posted_to=None, limit=20, offset=0):
    params = {"api_key": settings.SAM_API_KEY, "limit": min(limit, 100), "offset": offset, "active": "Yes"}
    if keywords: params["keyword"] = keywords
    if agency: params["organizationName"] = agency
    if naics_code: params["naicsCode"] = naics_code
    if set_aside: params["typeOfSetAside"] = set_aside
    if notice_type: params["ptype"] = notice_type
    if posted_from: params["postedFrom"] = posted_from
    if posted_to: params["postedTo"] = posted_to
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/opportunities/v2/search", params=params)
        resp.raise_for_status()
        return resp.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)), reraise=True)
async def get_opportunity_details(notice_id):
    params = {"api_key": settings.SAM_API_KEY, "noticeid": notice_id}
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/opportunities/v2/search", params=params)
        resp.raise_for_status()
        data = resp.json()
        opps = data.get("opportunitiesData", [])
        return opps[0] if opps else {}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)), reraise=True)
async def get_entity_info(uei=None, cage_code=None, company_name=None, limit=10):
    params = {"api_key": settings.SAM_API_KEY,
              "includeSections": "entityRegistration,coreData,assertions,repsAndCerts,pointsOfContact",
              "registrationStatus": "A", "limit": min(limit, 100)}
    if uei: params["ueiSAM"] = uei
    if cage_code: params["cageCode"] = cage_code
    if company_name: params["legalBusinessName"] = company_name
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/entity-information/v3/entities", params=params)
        resp.raise_for_status()
        return resp.json()
