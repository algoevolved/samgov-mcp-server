from mcp.types import Tool
from clients.sam_client import search_opportunities as _search

SCHEMA = Tool(
    name="search_opportunities",
    description="Search active federal contract opportunities on SAM.gov. Returns solicitation titles, agencies, NAICS codes, response deadlines, and set-aside designations.",
    inputSchema={"type": "object", "properties": {
        "keywords": {"type": "string", "description": "Keywords to search in opportunity titles and descriptions"},
        "agency": {"type": "string", "description": "Agency name or acronym (e.g. NAVY, HHS)"},
        "naics_code": {"type": "string", "description": "6-digit NAICS code"},
        "set_aside": {"type": "string", "enum": ["SBA","8A","WOSB","EDWOSB","HUBZone","SDVOSB","VSB"]},
        "notice_type": {"type": "string", "enum": ["PreSol","Solicitation","Award","JA","SSSA","SSSS"]},
        "posted_from": {"type": "string", "description": "YYYY-MM-DD"},
        "posted_to": {"type": "string", "description": "YYYY-MM-DD"},
        "limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100},
    }},
)

async def run(keywords=None, agency=None, naics_code=None, set_aside=None, notice_type=None, posted_from=None, posted_to=None, limit=20):
    data = await _search(keywords=keywords, agency=agency, naics_code=naics_code, set_aside=set_aside,
                         notice_type=notice_type, posted_from=posted_from, posted_to=posted_to, limit=limit)
    opps = data.get("opportunitiesData", [])
    total = data.get("totalRecords", 0)
    if not opps: return "No active opportunities found matching your criteria."
    lines = [f"Found {total:,} opportunities (showing {len(opps)}):\n"]
    for i, o in enumerate(opps, 1):
        lines.append(f"{i}. {o.get('title','Untitled')}\n   Agency: {o.get('organizationName','?')}\n   Type: {o.get('type','?')} | NAICS: {o.get('naicsCode','?')} | Set-Aside: {o.get('typeOfSetAside','Full & Open')}\n   Sol #: {o.get('solicitationNumber','?')} | Deadline: {o.get('responseDeadLine','?')}\n   Notice ID: {o.get('noticeId','?')} | {o.get('uiLink','')}\n")
    return "\n".join(lines)
