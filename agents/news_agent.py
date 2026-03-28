from __future__ import annotations

from typing import Any


def analyze_news(headlines: list[str]) -> list[dict[str, Any]]:
    """
    占位版新闻分析器。
    后续可接 OpenAI API / 兼容模型 API。
    """
    results = []
    for headline in headlines:
        results.append(
            {
                "headline": headline,
                "event_type": "unknown",
                "impact_direction": "neutral",
                "affected_assets": [],
                "risk_level": "medium",
                "confidence": 0.50,
            }
        )
    return results
