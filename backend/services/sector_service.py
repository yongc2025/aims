"""Sector heatmap data service."""

from backend.storage.analysis_repository import get_sector_heatmap as query_sector_heatmap


def get_sector_heatmap():
    """Return sector heatmap data from storage."""
    return query_sector_heatmap()
