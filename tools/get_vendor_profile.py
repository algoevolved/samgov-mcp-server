from mcp.types import Tool
from clients.sam_client import get_entity_info as _get

SCHEMA = Tool(
    name="get_vendor_profile",
    description="Look up a registered federal contractor's SAM.gov entity profile. Returns certifications, NAICS codes, CAGE/UEI, and active registration status.",
    inputSchema={"type": "object", "properties": {
        "uei": {"type": "string"}, "cage_code": {"type": "string"},
        "company_name": {"type": "string"}, "limit": {"type": "integer", "default": 10},
    }},
)

async def run(uei=None, cage_code=None, company_name=None, limit=10):
    if not any([uei, cage_code, company_name]): return "Please provide at least one of: uei, cage_code, or company_name."
    data = await _get(uei=uei, cage_code=cage_code, company_name=company_name, limit=limit)
    entities = data.get("entityData", [])
    if not entities: return "No registered entities found."
    lines = [f"Found {data.get('totalRecords',0):,} entities (showing {len(entities)}):\n"]
    for i, e in enumerate(entities, 1):
        reg = e.get("entityRegistration", {})
        core = e.get("coreData", {})
        addr = core.get("physicalAddress", {})
        loc = ", ".join(filter(None, [addr.get("city",""), addr.get("stateOrProvinceCode",""), addr.get("countryCode","")]))
        naics = [n.get("naicsCode","") for n in core.get("naicsCodeList",{}).get("naicsCode",[])[:5]]
        lines.append(f"{i}. {reg.get('legalBusinessName','?')}\n   UEI: {reg.get('ueiSAM','?')} | CAGE: {reg.get('cageCode','?')} | Status: {reg.get('registrationStatus','?')}\n   Location: {loc}" + (f"\n   NAICS: {', '.join(naics)}" if naics else "") + "\n")
    return "\n".join(lines)
