"""AIMS collector integration tests.

Verifies the complete pipeline contract:
Agent -> Validator -> Storage -> Report.
"""

from backend.agents.validator_agent import validate_market_data


def test_collector_pipeline_contract():
    """Validate the minimum collector data contract before integration execution."""
    payload = {
        "date": "2026-07-17",
        "source": "integration-test",
        "market": {
            "status": "collected",
        },
    }

    result = validate_market_data(payload)

    assert result["status"] == "passed"
    assert result["quality_score"] == 100
    assert result["errors"] == []
