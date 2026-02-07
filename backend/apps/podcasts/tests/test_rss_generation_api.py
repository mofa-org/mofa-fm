from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.podcasts.models import Episode, Show
from apps.users.models import User


class RSSGenerationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="test-pass-123",
            is_creator=True,
        )
        self.client.force_authenticate(user=self.user)

        cover = SimpleUploadedFile("cover.jpg", b"fake-cover-bytes", content_type="image/jpeg")
        self.show = Show.objects.create(
            title="My Show",
            description="desc",
            cover=cover,
            creator=self.user,
        )

    @patch("apps.podcasts.services.rss_ingest.generate_script_from_rss_sources")
    def test_generate_from_rss_dry_run_with_multi_sources(self, mock_generate):
        mock_generate.return_value = {
            "feed_title": "FeedA / FeedB",
            "items": [{"title": "A"}, {"title": "B"}],
            "script": "【大牛】新闻一\n【一帆】新闻二",
        }

        payload = {
            "show_id": self.show.id,
            "rss_urls": [
                "https://news.ycombinator.com/rss",
                "https://example.com/feed.xml",
            ],
            "template": "news_flash",
            "max_items": 6,
            "deduplicate": True,
            "sort_by": "latest",
            "dry_run": True,
        }
        url = reverse("podcasts:episode_generate_from_rss")
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["feed_title"], "FeedA / FeedB")
        self.assertEqual(response.data["item_count"], 2)
        self.assertIn("【大牛】", response.data["script"])
        mock_generate.assert_called_once_with(
            rss_urls=payload["rss_urls"],
            max_items=6,
            deduplicate=True,
            sort_by="latest",
            template="news_flash",
        )

    @patch("apps.podcasts.tasks.generate_rss_podcast_task.delay")
    @patch("apps.podcasts.tasks.generate_rss_podcast_task.apply_async")
    def test_generate_from_rss_scheduled_dispatches_apply_async(self, mock_apply_async, mock_delay):
        eta = timezone.now() + timedelta(hours=1)
        payload = {
            "show_id": self.show.id,
            "rss_urls": [
                "https://news.ycombinator.com/rss",
                "https://example.com/feed.xml",
            ],
            "template": "news_flash",
            "max_items": 4,
            "deduplicate": False,
            "sort_by": "title",
            "scheduled_at": eta.isoformat(),
            "dry_run": False,
        }
        url = reverse("podcasts:episode_generate_from_rss")
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("scheduled", response.data["message"])
        episode = Episode.objects.get(id=response.data["episode_id"])
        self.assertEqual(episode.generation_meta.get("rss_urls"), payload["rss_urls"])
        self.assertEqual(episode.generation_meta.get("deduplicate"), False)
        self.assertEqual(episode.generation_meta.get("sort_by"), "title")

        called_kwargs = mock_apply_async.call_args.kwargs
        self.assertEqual(called_kwargs["args"][0], episode.id)
        self.assertEqual(called_kwargs["args"][1], payload["rss_urls"])
        self.assertEqual(called_kwargs["args"][2], 4)
        self.assertEqual(called_kwargs["args"][3], False)
        self.assertEqual(called_kwargs["args"][4], "title")
        self.assertEqual(called_kwargs["args"][5], "news_flash")
        self.assertIsNotNone(called_kwargs.get("eta"))
        mock_delay.assert_not_called()

    @patch("apps.podcasts.tasks.generate_rss_podcast_task.delay")
    def test_generate_from_rss_with_speaker_config(self, mock_delay):
        payload = {
            "show_id": self.show.id,
            "rss_urls": ["https://news.ycombinator.com/rss"],
            "template": "news_flash",
            "max_items": 4,
            "deduplicate": True,
            "sort_by": "latest",
            "dry_run": False,
            "host_name": "晨播",
            "guest_name": "晚评",
            "host_voice_id": "Chinese (Mandarin)_News_Anchor",
            "guest_voice_id": "Chinese (Mandarin)_Radio_Host",
        }
        url = reverse("podcasts:episode_generate_from_rss")
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        episode = Episode.objects.get(id=response.data["episode_id"])
        speaker_config = (episode.generation_meta or {}).get("speaker_config") or {}
        self.assertEqual(speaker_config.get("host_name"), "晨播")
        self.assertEqual(speaker_config.get("guest_name"), "晚评")
        self.assertEqual(speaker_config.get("host_voice_id"), "Chinese (Mandarin)_News_Anchor")
        self.assertEqual(speaker_config.get("guest_voice_id"), "Chinese (Mandarin)_Radio_Host")

        self.assertTrue(mock_delay.called)
        _, kwargs = mock_delay.call_args
        self.assertEqual(kwargs["speaker_config"]["host_name"], "晨播")
        self.assertEqual(kwargs["speaker_config"]["guest_name"], "晚评")

    @patch("apps.podcasts.tasks.generate_podcast_task.delay")
    @patch("apps.podcasts.tasks.generate_rss_podcast_task.delay")
    def test_generate_from_rss_with_manual_script_uses_script_task(self, mock_rss_delay, mock_script_delay):
        payload = {
            "show_id": self.show.id,
            "rss_urls": ["https://news.ycombinator.com/rss"],
            "template": "news_flash",
            "max_items": 4,
            "deduplicate": True,
            "sort_by": "latest",
            "dry_run": False,
            "script": "【大牛】手工改稿\n\n【一帆】继续讨论",
        }
        url = reverse("podcasts:episode_generate_from_rss")
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        episode = Episode.objects.get(id=response.data["episode_id"])
        self.assertEqual((episode.generation_meta or {}).get("script_mode"), "manual")
        self.assertIn("【大牛】", episode.script or "")
        mock_script_delay.assert_called_once()
        mock_rss_delay.assert_not_called()

    @patch("apps.podcasts.tasks.generate_rss_podcast_task.delay")
    def test_retry_generation_rss_dispatches_rss_task(self, mock_delay):
        episode = Episode.objects.create(
            show=self.show,
            title="rss failed",
            description="AI Generated Podcast from RSS: https://news.ycombinator.com/rss",
            status="failed",
            generation_stage="failed",
            generation_error="boom",
            generation_meta={
                "type": "rss",
                "source_url": "https://news.ycombinator.com/rss",
                "rss_urls": [
                    "https://news.ycombinator.com/rss",
                    "https://example.com/feed.xml",
                ],
                "max_items": 5,
                "template": "news_flash",
                "deduplicate": True,
                "sort_by": "latest",
            },
            audio_file=SimpleUploadedFile("pending.mp3", b"", content_type="audio/mpeg"),
        )

        url = reverse("podcasts:retry_generation", kwargs={"episode_id": episode.id})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_delay.assert_called_once_with(
            episode.id,
            ["https://news.ycombinator.com/rss", "https://example.com/feed.xml"],
            5,
            True,
            "latest",
            "news_flash",
        )

    @patch("apps.podcasts.tasks.generate_podcast_task.delay")
    @patch("apps.podcasts.tasks.generate_rss_podcast_task.delay")
    def test_retry_generation_rss_manual_script_dispatches_script_task(self, mock_rss_delay, mock_script_delay):
        episode = Episode.objects.create(
            show=self.show,
            title="rss manual failed",
            description="AI Generated Podcast from RSS: https://news.ycombinator.com/rss",
            status="failed",
            generation_stage="failed",
            generation_error="boom",
            script="【大牛】手工稿\n【一帆】继续",
            generation_meta={
                "type": "rss",
                "rss_urls": ["https://news.ycombinator.com/rss"],
                "script_mode": "manual",
            },
            audio_file=SimpleUploadedFile("pending.mp3", b"", content_type="audio/mpeg"),
        )

        url = reverse("podcasts:retry_generation", kwargs={"episode_id": episode.id})
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_script_delay.assert_called_once_with(episode.id, episode.script)
        mock_rss_delay.assert_not_called()
