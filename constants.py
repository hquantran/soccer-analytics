"""Shared constants for the soccer analytics ingestion scripts."""

from datetime import datetime


LEAGUE_IDS = [
    39,   # Premier League
    61,   # Ligue 1
    78,   # Bundesliga
    135,  # Serie A
    140,  # La Liga
]

MVP_LEAGUE_IDS = LEAGUE_IDS

# Target seasons for ingestion (inclusive).
# Adjusted to 2023-2025 per request.
SEASONS = [2023, 2024, 2025]
