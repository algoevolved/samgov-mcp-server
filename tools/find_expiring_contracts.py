import datetime
from mcp.types import Tool
from clients.usaspending_client import search_awards as _search

SCHEMA = Tool(
    name="find_expiring_contracts",
    description="Find federal contracts expiring within a specified window. Expiring contracts are recompete opportunities — the agency must re-solicit. High-value BD intelligence.",
    inputSchema={"type": "object", "properties": {
        "days_out": {"type": "integer", "default": 180, "minimum": 30, "maximum": 730},
        "agency_name": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}},
        "min_amount": {"type": "number"}, "limit": {"type": "integer", "default": 30, "minimum": 1, "maximum": 100},
    }},
)

async def run(days_out=180, agency_name=None, keywords=None, min_amount=None, limit=30):
    today = datetime.date.today()
    future = today + datetime.timedelta(days=days_out)
    data = await _search(keywords=keywords, agency_name=agency_name, min_amount=min_amount,
                         end_date=future.isoformat(), start_date=today.isoformat(), limit=limit)
    results = data.get("results", [])
    total = data.get("page_metadata", {}).get("total", 0)
    if not results: return f"No expiring contracts found in the next {days_out} days."
    lines = [f"Contracts expiring within {days_out} days — {total:,} found (showing {len(results)}):\n{today} → {future}\n"]
    for i, a in enumerate(results, 1):
        end = a.get("End Date", "N/A")
        amt = a.get("Award Amount", 0)
        days_left = "?"
        try: days_left = (datetime.date.fromisoformat(end[:10]) - today).days
        except: pass
        lines.append(f"{i}. {a.get('Recipient Name','?')} | ⏰ {end} ({days_left}d)\n   ${amt:,.0f} | {a.get('Awarding Agency','?')}\n   {(a.get('Description') or '')[:100]}\n")
    lines.append("\u{1F4A1} Watch SAM.gov for pre-solicitation notices 12-18mo before end date.")
    return "\n".join(lines)
