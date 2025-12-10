"""
Simple test to verify conftest.py works without async fixtures
"""


def test_test_config_fixture(test_config):
    """Test that test config fixture works."""
    assert "management_server_url" in test_config
    assert "trading_gateway_url" in test_config
    assert "test_user" in test_config
    assert test_config["test_user"]["username"] == "testuser"
