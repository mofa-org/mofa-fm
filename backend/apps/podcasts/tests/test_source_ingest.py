from unittest import TestCase
from unittest.mock import Mock, patch

from apps.podcasts.services.source_ingest import generate_script_from_source


class SourceIngestTests(TestCase):
    @patch("apps.podcasts.services.source_ingest._generate_script_with_llm")
    @patch("apps.podcasts.services.source_ingest.fetch_rss_items")
    def test_generate_script_from_source_uses_rss(self, mock_fetch_rss, mock_llm):
        mock_fetch_rss.return_value = (
            "Test Feed",
            [
                {
                    "title": "Item 1",
                    "link": "https://example.com/1",
                    "description": "Desc 1",
                    "published": "2026-02-07",
                }
            ],
        )
        mock_llm.return_value = "【主播A】你好\n【主播B】你好"

        result = generate_script_from_source("https://example.com/rss", max_items=3)

        self.assertEqual(result["source_type"], "rss")
        self.assertEqual(result["source_title"], "Test Feed")
        self.assertIn("【大牛】", result["script"])
        self.assertIn("【一帆】", result["script"])

    @patch("apps.podcasts.services.source_ingest._generate_script_with_llm")
    @patch("apps.podcasts.services.source_ingest.requests.get")
    @patch("apps.podcasts.services.source_ingest.fetch_rss_items")
    def test_generate_script_from_source_falls_back_to_webpage(
        self,
        mock_fetch_rss,
        mock_requests_get,
        mock_llm,
    ):
        mock_fetch_rss.side_effect = ValueError("not rss")
        mock_llm.return_value = "【主播A】网页总结\n【主播B】收到"

        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = """
        <html>
          <head><title>Example Article</title></head>
          <body>
            <p>First paragraph with enough words for extraction content.</p>
            <p>Second paragraph with details and context for summary purpose.</p>
          </body>
        </html>
        """
        mock_requests_get.return_value = mock_resp

        result = generate_script_from_source("https://example.com/post/123")

        self.assertEqual(result["source_type"], "webpage")
        self.assertEqual(result["source_title"], "Example Article")
        self.assertEqual(result["items"][0]["title"], "Example Article")
        self.assertIn("【大牛】", result["script"])
        self.assertIn("【一帆】", result["script"])
