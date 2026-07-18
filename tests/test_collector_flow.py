"""AIMS collector pipeline tests."""

from backend.agents.validator_agent import validate_market_data


def test_validator_accepts_minimal_valid_payload():
    payload = {
        "date": "2026-07-17",
        "source": "test"
    }

    result = validate_market_data(payload)

    assert result["status"] == "passed"
    assert result["quality_score"] > 0


def test_validator_rejects_missing_date():
    payload = {
        "source": "test"
    }

    result = validate_market_data(payload)

    assert result["status"] == "failed"
    assert "date" in str(result["errors"])
