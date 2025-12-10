#!/usr/bin/env python3
"""
Test Analytics API endpoints
"""

import asyncio
import httpx

BASE_URL = "http://localhost:8002"


async def test_analytics_endpoints():
    """Test analytics endpoints"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        print("🧪 Testing Analytics API Endpoints")
        print("=" * 50)

        # First authenticate
        auth_response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "analytics_test",
                "email": "analytics@test.com",
                "password": "testpass123",
                "full_name": "Analytics Test",
            },
        )

        login_response = await client.post(
            "/api/v1/auth/login/json",
            json={"username": "analytics_test", "password": "testpass123"},
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            client.headers.update({"Authorization": f"Bearer {token}"})
            print("✅ Authenticated successfully")
        else:
            print("❌ Authentication failed")
            return

        # Test analytics endpoints
        endpoints = [
            "/api/v1/analytics/performance",
            "/api/v1/analytics/portfolio",
            "/api/v1/analytics/risk",
            "/api/v1/analytics/market",
        ]

        for endpoint in endpoints:
            try:
                response = await client.get(endpoint)
                if response.status_code == 200:
                    print(f"✅ {endpoint}: {response.status_code} - OK")
                else:
                    print(
                        f"⚠️ {endpoint}: {response.status_code} - {response.text[:100]}"
                    )
            except Exception as e:
                print(f"❌ {endpoint}: Error - {str(e)}")

        # Check OpenAPI schema for analytics tags
        try:
            schema_response = await client.get("/openapi.json")
            if schema_response.status_code == 200:
                schema = schema_response.json()
                tags = schema.get("tags", [])
                analytics_tags = [
                    tag for tag in tags if "analytics" in tag.get("name", "").lower()
                ]
                print(f"\n📋 OpenAPI Tags with 'analytics': {len(analytics_tags)}")
                for tag in analytics_tags:
                    print(
                        f"   - {tag.get('name')}: {tag.get('description', 'No description')[:100]}..."
                    )
            else:
                print(f"❌ OpenAPI schema: {schema_response.status_code}")
        except Exception as e:
            print(f"❌ OpenAPI check failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_analytics_endpoints())
