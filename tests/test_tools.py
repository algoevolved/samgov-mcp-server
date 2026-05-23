import os
import pytest

os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("BILLING_ENABLED", "false")
os.environ.setdefault("SAM_API_KEY", os.getenv("SAM_API_KEY", "TEST_KEY"))

class TestSearchOpportunities:
    @pytest.mark.asyncio
    async def test_keyword_search(self):
        from tools.search_opportunities import run
        result = await run(keywords="cybersecurity", limit=5)
        assert isinstance(result, str) and len(result) > 0

    @pytest.mark.asyncio
    async def test_empty_graceful(self):
        from tools.search_opportunities import run
        result = await run(keywords="xyzzy_impossible_12345", limit=5)
        assert isinstance(result, str)

class TestSearchAwards:
    @pytest.mark.asyncio
    async def test_keyword(self):
        from tools.search_awards import run
        result = await run(keywords=["cloud"], limit=5)
        assert isinstance(result, str)

class TestGetVendorProfile:
    @pytest.mark.asyncio
    async def test_no_args(self):
        from tools.get_vendor_profile import run
        assert "Please provide" in await run()

class TestFindExpiringContracts:
    @pytest.mark.asyncio
    async def test_default(self):
        from tools.find_expiring_contracts import run
        assert isinstance(await run(days_out=180, limit=5), str)

class TestCompetitiveLandscape:
    @pytest.mark.asyncio
    async def test_market(self):
        from tools.get_competitive_landscape import run
        assert isinstance(await run(market_keywords=["cybersecurity"], years_back=1, limit=10), str)
