import datetime
from mcp.types import Tool
from clients.usaspending_client import get_agency_spending as _spending, search_awards as _search

SCHEMA = Tool(
    name="analyze_agency_spending",
    description="Analyze a federal agency's contract spending patterns. Shows top vendors, obligations, and recent contracts. Identify target agencies and market white space.",
    inputSchema={"type": "object", "properties": {
        "agency_name": {"type": "string", "description": "Agency name (e.g. Department of Defense, NASA)"},
        "fiscal_year": {"type": "integer"}, "keywords": {"type": "array", "items": {"type": "string"}},
        "limit": {"type": "integer", "default": 20, "minimum": 5, "maximum": 50},
    }, "required": ["agency_name"]},
)

async def run(agency_name, fiscal_year=None, keywords=None, limit=20):
    fy = fiscal_year or datetime.datetime.now().year
    spend = await _spending(agency_name=agency_name, fiscal_year=fy, limit=limit)
    awards = await _search(keywords=keywords, agency_name=agency_name,
                            start_date=f"{fy-1}-10-01", end_date=f"{fy}-09-30", limit=50)
    vendors = spend.get("results", [])
    recent = awards.get("results", [])
    total_count = awards.get("page_metadata", {}).get("total", 0)
    total_val = sum(a.get("Award Amount", 0) or 0 for a in recent)
    lines = [f"# {agency_name} — FY{fy}\n{total_count:,} contracts | ${total_val:,.0f} sample\n"]
    if vendors:
        lines.append("## Top Vendors\n")
        for i, v in enumerate(vendors, 1):
            pct = v.get("percentage_of_total", 0)
            lines.append(f"{i:2}. {v.get('name','?')}: ${v.get('amount',0):,.0f}" + (f" ({pct:.1f}%)" if pct else ""))
    if recent:
        lines.append("\n## Recent Contracts\n")
        for a in recent[:10]:
            lines.append(f"  • {a.get('Recipient Name','?')}: ${a.get('Award Amount',0):,.0f} — {(a.get('Description') or '')[:80]}")
    return "\n".join(lines)
