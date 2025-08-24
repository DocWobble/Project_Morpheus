import os
import sys
import asyncio
import httpx

# Ensure repo root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Morpheus_Client import app


def test_admin_page_served():
    async def fetch_admin():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/admin/")

    resp = asyncio.run(fetch_admin())
    assert resp.status_code == 200
    assert "Orpheus Admin" in resp.text
