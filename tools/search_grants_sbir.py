from mcp.types import Tool
from clients.sbir_client import search_solicitations as _sol, get_award_info as _awards

SCHEMA = Tool(
    name="search_grants_sbir",
    description="Search SBIR/STTR small business innovation grants. Phase I ~$200K, Phase II ~$1.5M, non-dilutive. Find open opportunities or research what topics agencies are funding.",
    inputSchema={"type": "object", "properties": {
        "keywords": {"type": "string"}, "agency": {"type": "string", "enum": ["DOD","HHS","NSF","DOE","NASA","USDA","EPA","DOT","ED","DHS"]},
        "phase": {"type": "string", "enum": ["Phase I","Phase II"]},
        "mode": {"type": "string", "enum": ["open","awards"], "default": "open"},
        "limit": {"type": "integer", "default": 20},
    }},
)

async def run(keywords=None, agency=None, phase=None, mode="open", limit=20):
    if mode == "awards":
        data = await _awards(agency=agency, keywords=keywords, limit=limit)
        items = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if not items: return "No SBIR/STTR award records found."
        lines = [f"SBIR/STTR Awards ({len(items)}):\n"]
        for i, a in enumerate(items[:limit], 1):
            lines.append(f"{i}. {a.get('firm','?')} — {a.get('title','?')}\n   ${a.get('award_amount',0):,.0f} | {a.get('award_year','?')} | {a.get('agency','?')}\n")
        return "\n".join(lines)
    data = await _sol(keywords=keywords, agency=agency, phase=phase, open_only=True, limit=limit)
    items = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    if not items: return "No open SBIR/STTR solicitations found."
    lines = [f"Open SBIR/STTR Solicitations ({len(items)}):\n"]
    for i, s in enumerate(items[:limit], 1):
        lines.append(f"{i}. {s.get('program_title', s.get('title','?'))}\n   {s.get('agency','?')} | {s.get('phase','?')} | Closes: {s.get('close_date', s.get('closeDate','?'))}\n   {(s.get('program_description', s.get('description','')) or '')[:150]}\n")
    return "\n".join(lines)
