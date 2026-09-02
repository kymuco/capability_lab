from dataclasses import replace

from capability_lab.player_window import render_player_window_html_v1
from capability_lab.player_window.demo import build_civilization_bootstrap_player_window_demo_v1


def test_local_html_is_self_contained_and_uses_non_authoritative_vocabulary() -> None:
    window = build_civilization_bootstrap_player_window_demo_v1()
    html = render_player_window_html_v1(window)

    assert "Supported — scoped" in html
    assert "Unknown" in html
    assert "Could be considered" in html
    assert "Prerequisite evidence gap" in html
    assert "Explicit exploration" in html
    assert "Narrative projection" in html
    assert "Recorded significance note" in html

    assert "default-src 'none'" in html
    assert 'name="robots" content="noindex,nofollow"' in html
    assert "<script" not in html.lower()
    assert "https://" not in html.lower()
    assert "http://" not in html.lower()
    assert "<link" not in html.lower()

    forbidden = (
        "Mastered",
        "Human Level",
        "XP ",
        "Recommended next",
        "Best next",
        "Blocked",
        "You are weak",
    )
    assert all(term not in html for term in forbidden)


def test_source_text_is_escaped_and_never_becomes_trusted_html() -> None:
    window = build_civilization_bootstrap_player_window_demo_v1()
    capability = replace(
        window.capabilities[0],
        concept_name='<script>alert("owned")</script>',
    )
    tampered_display_window = replace(window, capabilities=(capability,))
    html = render_player_window_html_v1(tampered_display_window)

    assert '<script>alert("owned")</script>' not in html
    assert "&lt;script&gt;alert(&quot;owned&quot;)&lt;/script&gt;" in html
