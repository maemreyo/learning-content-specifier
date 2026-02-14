#!/usr/bin/env python3
"""Fetch trending topics for a unit run (best-effort, deterministic JSON artifact)."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

GOOGLE_TRENDS_RSS_URLS = [
    "https://trends.google.com/trending/rss?geo={geo}",
    "https://trends.google.com/trendingsearches/daily/rss?geo={geo}",
]

HT_NS = "https://trends.google.com/trending/rss"

SPORTS_HINTS = {
    "vs",
    "nfl",
    "nba",
    "mlb",
    "nhl",
    "uefa",
    "fifa",
    "cricket",
    "match",
    "score",
}

EDUCATION_TECH_HINTS = {
    "ai",
    "education",
    "school",
    "university",
    "learning",
    "teacher",
    "student",
    "research",
    "climate",
    "health",
    "economy",
    "technology",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Factory repository root")
    parser.add_argument("--unit-dir", required=True, help="Unit directory")
    parser.add_argument("--geo", default="US", help="Google Trends geo code")
    parser.add_argument("--max-topics", type=int, default=12, help="Maximum number of topics")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    return payload if isinstance(payload, dict) else None


def contract_version(repo_root: Path) -> str:
    index_path = repo_root / "contracts" / "index.json"
    payload = load_json(index_path)
    if isinstance(payload, dict):
        version = str(payload.get("contract_version", "")).strip()
        if version:
            return version
    return "1.0.0"


def fetch_rss(geo: str) -> str | None:
    for raw_url in GOOGLE_TRENDS_RSS_URLS:
        url = raw_url.format(geo=geo)
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 lcs-trend-fetcher"})
        try:
            with urlopen(request, timeout=8) as response:  # nosec: B310
                return response.read().decode("utf-8", errors="replace")
        except (TimeoutError, URLError, OSError):
            continue
    return None


def parse_pub_date(value: str) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except Exception:  # noqa: BLE001
        return datetime.now(UTC)


def pedagogical_fit(title: str, news_title: str) -> str:
    text = f"{title} {news_title}".strip().lower()
    if any(token in text for token in EDUCATION_TECH_HINTS):
        return "high"
    if any(token in text for token in SPORTS_HINTS):
        return "low"
    return "medium"


def classify_topic(title: str, news_title: str) -> str:
    text = f"{title} {news_title}".strip().lower()
    if any(token in text for token in {"ai", "technology", "chip", "software", "app"}):
        return "technology"
    if any(token in text for token in {"education", "school", "teacher", "student", "learning"}):
        return "education"
    if any(token in text for token in {"climate", "heat", "weather", "flood"}):
        return "climate"
    if any(token in text for token in {"health", "medical", "vaccine", "disease"}):
        return "health"
    if any(token in text for token in {"economy", "market", "price", "jobs", "inflation"}):
        return "economy"
    if any(token in text for token in SPORTS_HINTS):
        return "sports"
    return "general"


def parse_items(xml_payload: str, max_topics: int) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_payload)
    items = root.findall("./channel/item")

    parsed: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in items:
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        title_key = title.casefold()
        if title_key in seen:
            continue
        seen.add(title_key)

        pub_date = parse_pub_date((item.findtext("pubDate") or "").strip())
        approx_traffic = (item.findtext(f"{{{HT_NS}}}approx_traffic") or "").strip()
        link = (item.findtext("link") or "").strip() or "https://trends.google.com/trends/"

        news_item = item.find(f"{{{HT_NS}}}news_item")
        news_title = ""
        news_url = ""
        news_source = ""
        if news_item is not None:
            news_title = (news_item.findtext(f"{{{HT_NS}}}news_item_title") or "").strip()
            news_url = (news_item.findtext(f"{{{HT_NS}}}news_item_url") or "").strip()
            news_source = (news_item.findtext(f"{{{HT_NS}}}news_item_source") or "").strip()

        parsed.append(
            {
                "title": title,
                "captured_at": pub_date.strftime("%Y-%m-%d"),
                "trend_window": "7d",
                "approx_traffic": approx_traffic,
                "source_url": link,
                "source_type": "google_trends",
                "news_title": news_title,
                "news_url": news_url,
                "news_source": news_source,
                "category": classify_topic(title, news_title),
                "pedagogical_fit": pedagogical_fit(title, news_title),
            }
        )

    parsed.sort(key=lambda row: (row["pedagogical_fit"] != "high", row["category"] == "sports", row["title"]))
    return parsed[:max_topics]


def load_fallback_topics(repo_root: Path) -> list[dict[str, Any]]:
    fallback = (
        repo_root.parent
        / "subjects"
        / "english"
        / ".lcs"
        / "template-pack"
        / "v1"
        / "topic-pools"
        / "trending-topics.en.json"
    )
    payload = load_json(fallback)
    if not isinstance(payload, dict):
        return []
    topics = payload.get("topics", [])
    if not isinstance(topics, list):
        return []

    result: list[dict[str, Any]] = []
    for item in topics:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "title": str(item.get("title", "")).strip(),
                "captured_at": str(item.get("captured_at", "")).strip() or datetime.now(UTC).strftime("%Y-%m-%d"),
                "trend_window": "90d",
                "approx_traffic": "",
                "source_url": str(item.get("source_url", "")).strip(),
                "source_type": str(item.get("source_type", "industry_report")).strip() or "industry_report",
                "news_title": "",
                "news_url": "",
                "news_source": "",
                "category": "education",
                "pedagogical_fit": "high",
            }
        )
    return result


def attach_topic_ids(topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for index, topic in enumerate(topics, start=1):
        captured = str(topic.get("captured_at", datetime.now(UTC).strftime("%Y-%m-%d")))
        year_month = captured[:7]
        safe_year_month = year_month if len(year_month) == 7 else datetime.now(UTC).strftime("%Y-%m")
        topic_id = f"TREND-{safe_year_month}-{index:02d}".replace("-", "-", 1)
        # transform TREND-YYYY-MM-XX
        topic_id = f"TREND-{safe_year_month}-{index:02d}"
        enriched_topic = dict(topic)
        enriched_topic["topic_id"] = topic_id
        enriched.append(enriched_topic)
    return enriched


def write_trend_file(unit_dir: Path, payload: dict[str, Any]) -> Path:
    trend_file = unit_dir / "trend-topics.json"
    trend_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return trend_file


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    unit_dir = Path(args.unit_dir).resolve()
    unit_dir.mkdir(parents=True, exist_ok=True)

    rss = fetch_rss(args.geo)
    source_mode = "google_trends_rss"
    topics: list[dict[str, Any]] = []

    if rss:
        try:
            topics = parse_items(rss, max_topics=max(1, int(args.max_topics)))
        except Exception:  # noqa: BLE001
            topics = []

    if not topics:
        topics = load_fallback_topics(repo_root)
        source_mode = "fallback_pool"

    topics = attach_topic_ids(topics[: max(1, int(args.max_topics))])

    payload = {
        "contract_version": contract_version(repo_root),
        "unit_id": unit_dir.name,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": source_mode,
        "geo": args.geo,
        "topics": topics,
    }
    trend_file = write_trend_file(unit_dir, payload)

    result = {
        "STATUS": "PASS" if topics else "WARN",
        "UNIT_DIR": str(unit_dir),
        "TREND_TOPICS_FILE": str(trend_file),
        "TOPIC_COUNT": len(topics),
        "PROVIDER": source_mode,
    }
    if args.json:
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(f"STATUS: {result['STATUS']}")
        print(f"TREND_TOPICS_FILE: {trend_file}")
        print(f"TOPIC_COUNT: {len(topics)}")
        print(f"PROVIDER: {source_mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
