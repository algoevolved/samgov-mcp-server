import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

BASE_URL = "https://api.usaspending.gov/api/v2"
_DEFAULT_TIMEOUT = 30.0

def _award_type_codes(award_type):
    mapping = {"contracts": ["A","B","C","D"], "grants": ["02","03","04","05"],
               "direct_payments": ["06","07","08","09"], "loans": ["07","08"]}
    return mapping.get(award_type, mapping["contracts"])

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)), reraise=True)
async def search_awards(keywords=None, agency_name=None, recipient_name=None, award_type="contracts",
                        min_amount=None, max_amount=None, start_date=None, end_date=None, limit=20, page=1):
    filters = {"award_type_codes": _award_type_codes(award_type)}
    if keywords: filters["keywords"] = keywords
    if agency_name: filters["agencies"] = [{"type": "awarding", "tier": "toptier", "name": agency_name}]
    if recipient_name: filters["recipient_search_text"] = [recipient_name]
    if min_amount or max_amount: filters["award_amounts"] = [{"lower_bound": min_amount or 0, "upper_bound": max_amount or 10_000_000_000}]
    if start_date or end_date: filters["time_period"] = [{"start_date": start_date or "2000-01-01", "end_date": end_date or "2099-12-31"}]
    payload = {"filters": filters,
               "fields": ["Award ID","Recipient Name","Award Amount","Total Outlays","Description",
                           "Contract Award Type","Awarding Agency","Awarding Sub Agency","Start Date","End Date"],
               "limit": min(limit, 100), "page": page, "sort": "Award Amount", "order": "desc"}
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.post(f"{BASE_URL}/search/spending_by_award/", json=payload)
        resp.raise_for_status()
        return resp.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)), reraise=True)
async def get_agency_spending(agency_name, fiscal_year=None, limit=20):
    import datetime
    fy = fiscal_year or datetime.datetime.now().year
    payload = {"filters": {"time_period": [{"start_date": f"{fy-1}-10-01", "end_date": f"{fy}-09-30"}],
                            "agencies": [{"type": "awarding", "tier": "toptier", "name": agency_name}],
                            "award_type_codes": _award_type_codes("contracts")},
               "category": "recipient", "limit": min(limit, 100), "page": 1}
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.post(f"{BASE_URL}/search/spending_by_category/", json=payload)
        resp.raise_for_status()
        return resp.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)), reraise=True)
async def get_recipient_awards(recipient_name, limit=20):
    payload = {"filters": {"recipient_search_text": [recipient_name], "award_type_codes": _award_type_codes("contracts")},
               "fields": ["Award ID","Recipient Name","Award Amount","Description","Awarding Agency","Start Date","End Date"],
               "limit": min(limit, 100), "page": 1, "sort": "Award Amount", "order": "desc"}
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.post(f"{BASE_URL}/search/spending_by_award/", json=payload)
        resp.raise_for_status()
        return resp.json()
