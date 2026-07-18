"""Validation rules for AIMS market data before persistence."""

from typing import Any


REQUIRED_FIELDS = ["date"]


class ValidationResult:
    def __init__(self, passed: bool, errors: list[str], score: int):
        self.passed = passed
        self.errors = errors
        self.score = score

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "passed" if self.passed else "failed",
            "quality_score": self.score,
            "errors": self.errors,
        }


def validate_market_data(data: dict[str, Any]) -> ValidationResult:
    errors = []

    for field in REQUIRED_FIELDS:
        if not data.get(field):
            errors.append(f"missing required field: {field}")

    if not isinstance(data, dict):
        errors.append("data must be dictionary")

    score = max(0, 100 - len(errors) * 20)

    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        score=score,
    )
