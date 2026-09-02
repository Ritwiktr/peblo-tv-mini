from app.services.search import search_catalogue


def _cat():
    return {
        "sections": [
            {
                "id": "featured",
                "title": "Featured",
                "shows": [
                    {
                        "title": "Moti's Many Lives",
                        "synopsis": "A dog across India",
                        "categories": ["adventure", "india"],
                        "seasons": [
                            {
                                "season_number": 1,
                                "episodes": [
                                    {
                                        "title": "The Lost Kite",
                                        "languages": ["en", "hi"],
                                        "content_group": "g1",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
            {
                "id": "songs",
                "title": "Songs",
                "shows": [
                    {
                        "title": "Peblo Songs",
                        "synopsis": "Singalong",
                        "categories": ["music"],
                        "seasons": [
                            {
                                "season_number": 1,
                                "episodes": [
                                    {"title": "Rain Song", "languages": ["en"], "content_group": "g2"}
                                ],
                            }
                        ],
                    }
                ],
            },
        ]
    }


def test_q_matches_episode_title():
    out = search_catalogue(_cat(), q="kite")
    assert out["count"] == 1
    assert out["shows"][0]["title"].startswith("Moti")


def test_filters_compose():
    out = search_catalogue(_cat(), q="song", category="music", language="en", section="songs")
    assert out["count"] == 1
    out = search_catalogue(_cat(), q="song", category="music", language="hi", section="songs")
    assert out["count"] == 0


def test_language_filter_hides_english_only():
    out = search_catalogue(_cat(), language="hi")
    assert out["count"] == 1
    assert "Moti" in out["shows"][0]["title"]
