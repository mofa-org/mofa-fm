"""
Source ingestion helpers for RSS or plain webpages.
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Dict, List
from urllib.parse import urlparse

import requests

from .rss_ingest import (
    _generate_script_with_llm,
    _normalize_roles,
    _items_to_reference_text,
    fetch_rss_items,
)

TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    no_tags = TAG_RE.sub(" ", text or "")
    return WHITESPACE_RE.sub(" ", html.unescape(no_tags)).strip()


def _validate_source_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("链接仅支持 http/https")
    return source_url


class _SimpleHTMLExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.in_script = False
        self.in_style = False
        self.in_paragraph = False
        self.title_parts: List[str] = []
        self.current_paragraph: List[str] = []
        self.paragraphs: List[str] = []

    def handle_starttag(self, tag, attrs):
        tag = (tag or "").lower()
        if tag == "title":
            self.in_title = True
        elif tag in {"script", "style", "noscript"}:
            self.in_script = tag == "script"
            self.in_style = tag == "style"
        elif tag == "p":
            self.in_paragraph = True
            self.current_paragraph = []

    def handle_endtag(self, tag):
        tag = (tag or "").lower()
        if tag == "title":
            self.in_title = False
        elif tag == "script":
            self.in_script = False
        elif tag in {"style", "noscript"}:
            self.in_style = False
        elif tag == "p":
            text = _strip_html(" ".join(self.current_paragraph))
            if len(text) >= 30:
                self.paragraphs.append(text)
            self.in_paragraph = False
            self.current_paragraph = []

    def handle_data(self, data):
        if not data or self.in_script or self.in_style:
            return
        if self.in_title:
            self.title_parts.append(data)
        if self.in_paragraph:
            self.current_paragraph.append(data)


def _extract_webpage_text(url: str, timeout: int = 15) -> Dict[str, str]:
    _validate_source_url(url)

    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; mofa-fm-source-bot/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        timeout=timeout,
    )
    response.raise_for_status()

    parser = _SimpleHTMLExtractor()
    parser.feed(response.text or "")

    title = _strip_html(" ".join(parser.title_parts))
    text_parts = parser.paragraphs[:12]
    body = _strip_html(" ".join(text_parts))
    if not body:
        body = _strip_html(response.text)[:2000]
    if not body:
        raise ValueError("网页正文提取失败")

    return {
        "title": title or "网页内容",
        "content": body,
        "url": url,
    }


def _webpage_to_reference(page: Dict[str, str]) -> str:
    return (
        f"来源：{page['title']}\n"
        f"链接：{page['url']}\n\n"
        f"正文摘录：\n{page['content']}"
    ).strip()


def collect_source_material(source_url: str, max_items: int = 8) -> Dict[str, object]:
    """
    Collect source material first: RSS preferred, webpage fallback.
    """
    _validate_source_url(source_url)

    try:
        feed_title, items = fetch_rss_items(rss_url=source_url, max_items=max_items)
        reference_text = _items_to_reference_text(feed_title=feed_title, items=items)
        return {
            "source_type": "rss",
            "source_title": feed_title,
            "items": items,
            "reference_text": reference_text,
        }
    except Exception:
        page = _extract_webpage_text(source_url)
        return {
            "source_type": "webpage",
            "source_title": page["title"],
            "items": [
                {
                    "title": page["title"],
                    "link": page["url"],
                    "description": page["content"][:500],
                    "published": "",
                }
            ],
            "reference_text": _webpage_to_reference(page),
        }


def generate_script_from_material(material: Dict[str, object], template: str = "news_flash") -> str:
    """
    Generate script from collected source material.
    """
    source_title = str(material.get("source_title") or "")
    reference_text = str(material.get("reference_text") or "")
    if not source_title or not reference_text:
        raise ValueError("source material incomplete")

    script = _generate_script_with_llm(
        feed_title=source_title,
        reference_text=reference_text,
        template=template,
    )
    return _normalize_roles(script)


def generate_script_from_source(
    source_url: str,
    max_items: int = 8,
    template: str = "news_flash",
) -> Dict[str, object]:
    """
    Collect source material and generate script in one call.
    """
    material = collect_source_material(source_url=source_url, max_items=max_items)
    script = generate_script_from_material(material, template=template)

    return {
        "source_type": material["source_type"],
        "source_title": material["source_title"],
        "items": material["items"],
        "script": script,
    }
