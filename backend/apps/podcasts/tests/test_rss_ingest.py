from unittest import TestCase
from unittest.mock import patch

from apps.podcasts.services.rss_ingest import (
    collect_rss_material,
    fetch_rss_items,
    generate_script_from_rss,
)


SAMPLE_RSS = b"""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Hacker News</title>
    <item>
      <title>Item One</title>
      <link>https://example.com/1</link>
      <description><![CDATA[First <b>description</b>]]></description>
      <pubDate>Sat, 07 Feb 2026 08:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Item Two</title>
      <link>https://example.com/2</link>
      <description>Second description</description>
      <pubDate>Sat, 07 Feb 2026 09:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


class _MockResponse:
    def __init__(self, body: bytes):
        self.content = body

    def raise_for_status(self):
        return None


class RSSIngestServiceTests(TestCase):
    @patch("apps.podcasts.services.rss_ingest.requests.get")
    def test_fetch_rss_items(self, mock_get):
        mock_get.return_value = _MockResponse(SAMPLE_RSS)
        feed_title, items = fetch_rss_items("https://news.ycombinator.com/rss", max_items=1)

        self.assertEqual(feed_title, "Hacker News")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Item One")
        self.assertEqual(items[0]["description"], "First description")

    @patch("apps.podcasts.services.rss_ingest._generate_script_with_llm")
    @patch("apps.podcasts.services.rss_ingest.requests.get")
    def test_generate_script_from_rss_via_llm(self, mock_get, mock_generate_llm):
        mock_get.return_value = _MockResponse(SAMPLE_RSS)
        mock_generate_llm.return_value = "【主播A】这是AI总结\n【主播B】这是AI扩展"
        result = generate_script_from_rss(
            rss_url="https://news.ycombinator.com/rss",
            max_items=2,
        )

        self.assertEqual(result["feed_title"], "Hacker News")
        self.assertEqual(len(result["items"]), 2)
        self.assertIn("【大牛】", result["script"])
        self.assertIn("【一帆】", result["script"])
        mock_generate_llm.assert_called_once()

    @patch("apps.podcasts.services.rss_ingest.fetch_rss_items")
    def test_collect_rss_material_deduplicate_and_sort(self, mock_fetch):
        mock_fetch.side_effect = [
            (
                "FeedA",
                [
                    {
                        "title": "Same Item",
                        "link": "https://example.com/same",
                        "description": "dup",
                        "published": "Sat, 07 Feb 2026 09:00:00 GMT",
                    },
                    {
                        "title": "Old Item",
                        "link": "https://example.com/old",
                        "description": "old",
                        "published": "Sat, 07 Feb 2026 07:00:00 GMT",
                    },
                ],
            ),
            (
                "FeedB",
                [
                    {
                        "title": "Same Item",
                        "link": "https://example.com/same",
                        "description": "dup",
                        "published": "Sat, 07 Feb 2026 09:00:00 GMT",
                    },
                    {
                        "title": "New Item",
                        "link": "https://example.com/new",
                        "description": "new",
                        "published": "Sat, 07 Feb 2026 10:00:00 GMT",
                    },
                ],
            ),
        ]

        material = collect_rss_material(
            rss_urls=["https://a.example/rss", "https://b.example/rss"],
            max_items=5,
            deduplicate=True,
            sort_by="latest",
        )

        self.assertEqual(material["source_title"], "FeedA / FeedB")
        self.assertEqual(len(material["items"]), 3)
        self.assertEqual(material["items"][0]["title"], "New Item")
        self.assertEqual(material["items"][1]["title"], "Same Item")
