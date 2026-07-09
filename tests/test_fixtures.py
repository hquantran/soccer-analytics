from sources.fixtures import flatten_fixture, flatten_fixture_score


def test_flatten_fixture_and_score() -> None:
    record = {
        "fixture": {
            "id": 101,
            "referee": "John",
            "timezone": "UTC",
            "date": "2024-05-01T20:00:00+00:00",
            "timestamp": 1714615200,
            "periods": {"first": 1714615200, "second": 1714615800},
            "venue": {"id": 7, "name": "Stadium", "city": "London"},
            "status": {"long": "Match Finished", "short": "FT", "elapsed": 90, "extra": 0},
        },
        "league": {"id": 39, "name": "Premier League", "country": "England", "season": 2024, "round": "Regular Season"},
        "teams": {
            "home": {"id": 1, "name": "Home", "winner": True},
            "away": {"id": 2, "name": "Away", "winner": False},
        },
        "score": {"halftime": {"home": 1, "away": 0}, "fulltime": {"home": 2, "away": 1}, "extratime": {"home": None, "away": None}, "penalty": {"home": None, "away": None}},
    }

    fixture = flatten_fixture(record)
    score = flatten_fixture_score(101, record)

    assert fixture["fixture_id"] == 101
    assert fixture["league_id"] == 39
    assert fixture["status_short"] == "FT"
    assert fixture["home_team_name"] == "Home"
    assert score["fixture_id"] == 101
    assert score["fulltime_home"] == 2
    assert score["fulltime_away"] == 1
