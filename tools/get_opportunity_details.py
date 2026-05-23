from mcp.types import Tool
from clients.sam_client import get_opportunity_details as _get

SCHEMA = Tool(
    name="get_opportunity_details",
    description="Get complete details of a specific federal contract opportunity by its SAM.gov Notice ID.",
    inputSchema={"type": "object", "properties": {"notice_id": {"type": "string"}}, "required": ["notice_id"]},
)

async def run(notice_id):
    opp = await _get(notice_id=notice_id)
    if not opp: return f"No opportunity found with Notice ID: {notice_id}"
    contacts = [f"  {c.get('type','')}: {c.get('fullName','?')} | {c.get('email','?')}" for c in (opp.get("pointOfContact") or [])]
    atts = [f"  - {a.get('name','File')}: {a.get('url','')}" for a in (opp.get("resourceLinks") or [])]
    place = opp.get("placeOfPerformance", {})
    place_str = ", ".join(filter(None, [place.get("city",{}).get("name",""), place.get("state",{}).get("code",""), place.get("country",{}).get("code","")]))
    return "\n".join(filter(None, [
        f"# {opp.get('title','Untitled')}",
        f"Agency: {opp.get('organizationName','')} | Type: {opp.get('type','?')} | Sol#: {opp.get('solicitationNumber','?')}",
        f"NAICS: {opp.get('naicsCode','?')} | Set-Aside: {opp.get('typeOfSetAside','Full & Open')}",
        f"Posted: {opp.get('postedDate','?')} | Deadline: {opp.get('responseDeadLine','?')}",
        f"Place of Performance: {place_str or 'N/A'}",
        f"Link: {opp.get('uiLink','')}",
        "", "## Description", (opp.get("description") or "No description.")[:3000],
        ("\n## Contacts\n" + "\n".join(contacts)) if contacts else None,
        ("\n## Attachments\n" + "\n".join(atts)) if atts else None,
    ]))
