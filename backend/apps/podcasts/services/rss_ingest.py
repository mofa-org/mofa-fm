"""
RSS ingestion and script generation helpers.
"""
from __future__ import annotations

import html
import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import requests
from django.conf import settings

TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
ROLE_A_PATTERN = re.compile(r"【\s*(主播A|A|Host A|host a|主持人A)\s*】")
ROLE_B_PATTERN = re.compile(r"【\s*(主播B|B|Host B|host b|主持人B)\s*】")


def _strip_html(text: str) -> str:
    if not text:
        return ""
    no_tags = TAG_RE.sub(" ", text)
    return WHITESPACE_RE.sub(" ", html.unescape(no_tags)).strip()


def _safe_text(element: ET.Element | None, name: str) -> str:
    if element is None:
        return ""
    child = element.find(name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _validate_rss_url(rss_url: str) -> str:
    parsed = urlparse(rss_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("RSS 地址仅支持 http/https")
    if not parsed.netloc:
        raise ValueError("RSS 地址无效")
    return rss_url


def fetch_rss_items(rss_url: str, max_items: int = 8, timeout: int = 15) -> Tuple[str, List[Dict[str, str]]]:
    """
    Fetch RSS/Atom feed and return channel title + normalized items.
    """
    _validate_rss_url(rss_url)

    response = requests.get(
        rss_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; mofa-fm-rss-bot/1.0)",
            "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    xml_bytes = response.content

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"RSS 解析失败: {exc}") from exc

    items: List[Dict[str, str]] = []
    channel_title = ""

    if root.tag.lower().endswith("rss"):
        channel = root.find("channel")
        channel_title = _safe_text(channel, "title") if channel is not None else ""
        nodes = channel.findall("item") if channel is not None else []
        for node in nodes:
            title = _safe_text(node, "title")
            link = _safe_text(node, "link")
            description = _strip_html(_safe_text(node, "description"))
            pub_date = _safe_text(node, "pubDate")
            if title:
                items.append(
                    {
                        "title": title,
                        "link": link,
                        "description": description,
                        "published": pub_date,
                    }
                )
    else:
        # Basic Atom support
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        title_node = root.find("atom:title", ns)
        channel_title = title_node.text.strip() if title_node is not None and title_node.text else ""
        for node in root.findall("atom:entry", ns):
            title_node = node.find("atom:title", ns)
            link_node = node.find("atom:link", ns)
            summary_node = node.find("atom:summary", ns)
            updated_node = node.find("atom:updated", ns)
            title = title_node.text.strip() if title_node is not None and title_node.text else ""
            link = link_node.attrib.get("href", "").strip() if link_node is not None else ""
            description = _strip_html(summary_node.text if summary_node is not None and summary_node.text else "")
            published = updated_node.text.strip() if updated_node is not None and updated_node.text else ""
            if title:
                items.append(
                    {
                        "title": title,
                        "link": link,
                        "description": description,
                        "published": published,
                    }
                )

    if not items:
        raise ValueError("RSS 无可用条目")

    return channel_title or "RSS Feed", items[:max_items]


def _items_to_reference_text(feed_title: str, items: List[Dict[str, str]]) -> str:
    lines = [f"来源：{feed_title}", ""]
    for idx, item in enumerate(items, start=1):
        lines.append(f"{idx}. 标题：{item['title']}")
        if item.get("description"):
            lines.append(f"摘要：{item['description']}")
        if item.get("published"):
            lines.append(f"发布时间：{item['published']}")
        if item.get("link"):
            lines.append(f"链接：{item['link']}")
        lines.append("")
    return "\n".join(lines).strip()


def _normalize_roles(script: str) -> str:
    """
    Normalize role tags into generator-compatible aliases.
    """
    normalized = ROLE_A_PATTERN.sub("【大牛】", script)
    normalized = ROLE_B_PATTERN.sub("【一帆】", normalized)
    return normalized.strip()


def _generate_script_with_llm(feed_title: str, reference_text: str) -> str:
    """
    Use OpenAI-compatible API directly to avoid higher-level tool-call parsing noise.
    """
    from openai import OpenAI

    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 未配置")

    client = OpenAI(
        api_key=api_key,
        base_url=getattr(settings, "OPENAI_API_BASE", "https://api.moonshot.cn/v1"),
    )
    model = getattr(settings, "OPENAI_MODEL", "moonshot-v1-8k")

    system_prompt = (
        "你是中文科技播客编剧。"
        "任务：先提炼每条新闻一句要点，再生成可直接 TTS 的双人对话脚本。"
        "硬性格式：只使用【大牛】与【一帆】角色标签。"
        "不要编造事实，不要输出代码块。"
    )
    user_prompt = (
        f"来源：{feed_title}\n\n"
        f"参考材料如下：\n{reference_text}\n\n"
        "请输出完整脚本。"
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
    )
    content = (completion.choices[0].message.content or "").strip()
    if not content:
        raise ValueError("LLM 返回空内容")
    return content


def generate_script_from_rss(rss_url: str, max_items: int = 8) -> Dict[str, object]:
    """
    Generate a podcast script from an RSS URL.
    """
    feed_title, items = fetch_rss_items(rss_url=rss_url, max_items=max_items)
    reference_text = _items_to_reference_text(feed_title=feed_title, items=items)

    script = _generate_script_with_llm(feed_title=feed_title, reference_text=reference_text)
    script = _normalize_roles(script)

    return {
        "feed_title": feed_title,
        "items": items,
        "script": script,
    }
