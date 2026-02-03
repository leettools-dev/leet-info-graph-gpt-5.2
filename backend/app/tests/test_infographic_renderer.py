from app.services.infographic import InfographicRenderer


def test_renderer_happy_path_with_sources():
    r = InfographicRenderer()
    rendered = r.render_session_infographic(
        prompt="Summarize EV market trends",
        sources=[
            {"source_id": 1, "title": "IEA Global EV Outlook", "url": "https://example.com", "confidence": 0.9},
            {"source_id": 2, "title": "BloombergNEF report", "url": "https://example.com/2", "confidence": 0.8},
        ],
    )

    assert rendered.svg_bytes.startswith(b"<svg")
    assert rendered.layout_meta["title"]
    assert len(rendered.layout_meta["key_bullets"]) >= 1
    assert rendered.layout_meta["claims"][0]["source_ids"] == [1, 2]


def test_renderer_escapes_xml_and_handles_no_sources():
    r = InfographicRenderer()
    rendered = r.render_session_infographic(prompt='A & B < C > D "quote"', sources=[])

    # Title should be XML-escaped
    assert "&amp;" in rendered.layout_meta["title"]
    assert "&lt;" in rendered.layout_meta["title"]
    assert "&gt;" in rendered.layout_meta["title"]
    assert "&quot;" in rendered.layout_meta["title"]

    # With no sources, we still produce a bullet/claim
    assert rendered.layout_meta["key_bullets"] == ["Add sources to generate richer results."]
    assert rendered.layout_meta["claims"][0]["source_ids"] == []
