from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RenderedInfographic:
    """Result of rendering an infographic."""

    svg_bytes: bytes
    layout_meta: dict[str, Any]


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class InfographicRenderer:
    """Template-based infographic renderer (MVP).

    Produces a deterministic SVG and a layout metadata payload suitable for storage.

    Note: This is intentionally simple and synchronous. Async job orchestration lives
    in a separate todo (Queue/worker).
    """

    def render_session_infographic(self, *, prompt: str, sources: list[dict[str, Any]]) -> RenderedInfographic:
        title = _xml_escape(prompt.strip()[:80])

        bullets = [
            f"{idx+1}. {s.get('title', '').strip()[:80]}"
            for idx, s in enumerate(sources[:5])
            if s.get("title")
        ]
        if not bullets:
            bullets = ["Add sources to generate richer results."]

        claims: list[dict[str, Any]] = []
        for idx, bullet in enumerate(bullets[:8]):
            claim_source_ids = [
                s.get("source_id")
                for s in sources[: min(2, len(sources))]
                if s.get("source_id") is not None
            ]
            claims.append(
                {
                    "id": f"c{idx+1}",
                    "text": bullet,
                    "source_ids": claim_source_ids,
                    # If a claim has no sources, treat it as an ungrounded suggestion.
                    "grounded": bool(claim_source_ids),
                }
            )

        layout_meta: dict[str, Any] = {
            "title": title,
            "key_bullets": bullets,
            "claims": claims,
            "sources": sources,
            "generated_by": "mvp-svg-template",
            "version": 2,
        }

        lines: list[str] = [
            "<svg xmlns='http://www.w3.org/2000/svg' width='800' height='450'>",
            "<rect width='100%' height='100%' fill='#0B1220'/>",
            "<text x='40' y='70' fill='#E5E7EB' font-family='Arial' font-size='28' font-weight='700'>",
            f"{title}",
            "</text>",
            "<text x='40' y='110' fill='#9CA3AF' font-family='Arial' font-size='14'>Generated infographic (MVP)</text>",
        ]
        y = 160
        for b in bullets[:8]:
            safe = _xml_escape(b)
            lines.append(
                f"<text x='60' y='{y}' fill='#E5E7EB' font-family='Arial' font-size='18'>{safe}</text>"
            )
            y += 36
        lines.append("</svg>")

        return RenderedInfographic(svg_bytes="".join(lines).encode("utf-8"), layout_meta=layout_meta)
