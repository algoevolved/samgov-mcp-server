from mcp.types import Tool
from clients.usaspending_client import search_awards as _search

SCHEMA = Tool(
    name="search_awards",
    description="Search historical federal contract awards from USASpending.gov. Returns awarded contracts with dollar amounts, recipients, and performance periods.",
    inputSchema={"type": "object", "properties": {
        "keywords": {"type": "array", "items": {"type": "string"}},
        "agency_name": {"type": "string"},
        "recipient_name": {"type": "string"},
        "award_type": {"type": "string", "enum": ["contracts","grants","direct_payments","loans"], "default": "contracts"},
        "min_amount": {"type": "number"}, "max_amount": {"type": "number"},
        "start_date": {"type": "string"}, "end_date": {"type": "string"},
        "limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100},
    }},
)

async def run(keywords=None, agency_name=None, recipient_name=None, award_type="contracts",
              min_amount=None, max_amount=None, start_date=None, end_date=None, limit=20):
    data = await _search(keywords=keywords, agency_name=agency_name, recipient_name=recipient_name,
                         award_type=award_type, min_amount=min_amount, max_amount=max_amount,
                         start_date=start_date, end_date=end_date, limit=limit)
    results = data.get("results", [])
    total = data.get("page_metadata", {}).get("total", 0)
    if not results: return "No awards found."
    lines = [f"Found {total:,} awards (showing {len(results)}):\n"]
    for i, a in enumerate(results, 1):
        amt = a.get("Award Amount", 0)
        lines.append(f"{i}. {a.get('Recipient Name','?')}\n   ${amt:,.0f} | {a.get('Contract Award Type','?')} | {a.get('Awarding Agency','?')}\n   {a.get('Start Date','?')} → {a.get('End Date','?')}\n   {(a.get('Description') or '')[:100]}\n")
    return "\n".join(lines)
