"""
LEATrace Integration Tests — API Endpoints.

Tests the FastAPI application endpoints via TestClient.
Uses SQLite in-memory for database isolation.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Creates a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    """Tests for /api/health."""

    def test_health_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_has_status(self, client):
        data = client.get("/api/health").json()
        assert data["status"] == "healthy"

    def test_health_has_version(self, client):
        data = client.get("/api/health").json()
        assert data["version"] == "2.0.0"

    def test_health_has_chain_count(self, client):
        data = client.get("/api/health").json()
        assert data["supported_chains"] == 11

    def test_health_has_timestamp(self, client):
        data = client.get("/api/health").json()
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z")


class TestInvestigationChainsAPI:
    """Tests for /api/investigation/chains."""

    def test_list_chains(self, client):
        response = client.get("/api/investigation/chains")
        assert response.status_code == 200
        data = response.json()
        assert data["total_chains"] == 11
        assert len(data["chains"]) == 11

    def test_chain_metadata_structure(self, client):
        data = client.get("/api/investigation/chains").json()
        for chain in data["chains"]:
            assert "chain_id" in chain
            assert "display_name" in chain
            assert "native_token" in chain
            assert "chain_type" in chain

    def test_chain_types_correct(self, client):
        data = client.get("/api/investigation/chains").json()
        chain_map = {c["chain_id"]: c["chain_type"] for c in data["chains"]}
        assert chain_map["ethereum"] == "evm"
        assert chain_map["bitcoin"] == "utxo"
        assert chain_map["solana"] == "account"
        assert chain_map["litecoin"] == "utxo"
        assert chain_map["dogecoin"] == "utxo"


class TestAddressValidationAPI:
    """Tests for /api/investigation/chains/{chain}/validate/{address}."""

    def test_valid_eth_address(self, client):
        response = client.get("/api/investigation/chains/ethereum/validate/0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28")
        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_invalid_eth_address(self, client):
        response = client.get("/api/investigation/chains/ethereum/validate/not_valid")
        assert response.status_code == 200
        assert response.json()["valid"] is False

    def test_unknown_chain_404(self, client):
        response = client.get("/api/investigation/chains/fakecoin/validate/0x123")
        assert response.status_code == 404


class TestChainDetectionAPI:
    """Tests for /api/investigation/detect-chain/{address}."""

    def test_detect_evm(self, client):
        response = client.get("/api/investigation/detect-chain/0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28")
        assert response.status_code == 200
        assert response.json()["detected_chain"] == "ethereum"

    def test_detect_bitcoin(self, client):
        response = client.get("/api/investigation/detect-chain/bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq")
        assert response.status_code == 200
        assert response.json()["detected_chain"] == "bitcoin"

    def test_detect_unknown(self, client):
        response = client.get("/api/investigation/detect-chain/notanaddress")
        assert response.status_code == 200
        assert response.json()["detected_chain"] is None


class TestSanctionsAPI:
    """Tests for /api/investigation/sanctions."""

    def test_sanctions_check_non_sanctioned(self, client):
        response = client.get("/api/investigation/sanctions/check/0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28")
        assert response.status_code == 200
        data = response.json()
        assert "is_sanctioned" in data

    def test_sanctions_stats(self, client):
        response = client.get("/api/investigation/sanctions/stats")
        assert response.status_code == 200
        data = response.json()
        assert "loaded" in data
        assert "total_addresses" in data

    def test_batch_sanctions(self, client):
        response = client.post("/api/investigation/sanctions/batch", json={
            "addresses": [
                "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28",
                "0x1234567890abcdef1234567890abcdef12345678",
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["total_checked"] == 2


class TestPricesAPI:
    """Tests for /api/investigation/prices."""

    def test_prices_endpoint(self, client):
        response = client.get("/api/investigation/prices")
        assert response.status_code == 200
        data = response.json()
        assert "prices" in data


class TestSecurityHeaders:
    """Tests that security headers are set on all responses."""

    def test_has_x_content_type_options(self, client):
        response = client.get("/api/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_has_x_frame_options(self, client):
        response = client.get("/api/health")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_has_hsts(self, client):
        response = client.get("/api/health")
        assert "max-age" in response.headers.get("Strict-Transport-Security", "")

    def test_has_request_duration(self, client):
        response = client.get("/api/health")
        assert "X-Request-Duration-Ms" in response.headers
