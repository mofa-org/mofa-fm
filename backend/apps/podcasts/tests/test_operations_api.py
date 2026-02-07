from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from apps.interactions.models import Follow
from apps.podcasts.models import Episode, Show
from apps.users.models import User


class OperationsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='ops-user',
            email='ops-user@example.com',
            password='test-pass-123',
            is_creator=True,
        )
        self.other = User.objects.create_user(
            username='ops-other',
            email='ops-other@example.com',
            password='test-pass-123',
            is_creator=True,
        )

        self.show_a = Show.objects.create(
            title='Show A',
            description='Show A desc',
            cover=SimpleUploadedFile('show-a.jpg', b'a', content_type='image/jpeg'),
            creator=self.user,
        )
        self.show_b = Show.objects.create(
            title='Show B',
            description='Show B desc',
            cover=SimpleUploadedFile('show-b.jpg', b'b', content_type='image/jpeg'),
            creator=self.other,
        )

        self.episode_a = Episode.objects.create(
            show=self.show_a,
            title='Episode A',
            description='A long enough description for share card testing.',
            status='published',
            audio_file=SimpleUploadedFile('a.mp3', b'audio-a', content_type='audio/mpeg'),
            play_count=100,
            like_count=10,
            published_at=timezone.now(),
        )
        self.episode_b = Episode.objects.create(
            show=self.show_b,
            title='Episode B',
            description='Another description.',
            status='published',
            audio_file=SimpleUploadedFile('b.mp3', b'audio-b', content_type='audio/mpeg'),
            play_count=20,
            like_count=2,
            published_at=timezone.now(),
        )

    def test_recommendations_anonymous_returns_items(self):
        url = reverse('podcasts:recommended_episodes')
        response = self.client.get(url, {'limit': 4})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
        self.assertGreaterEqual(len(response.data['items']), 1)
        self.assertIn('reason', response.data['items'][0])
        self.assertIn('episode', response.data['items'][0])

    def test_recommendations_authenticated_prefers_followed(self):
        Follow.objects.create(user=self.user, show=self.show_a)
        self.client.force_authenticate(self.user)

        url = reverse('podcasts:recommended_episodes')
        response = self.client.get(url, {'limit': 4})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['items']), 1)
        first_item = response.data['items'][0]
        self.assertEqual(first_item['reason'], '来自你订阅的内容')
        self.assertEqual(first_item['episode']['show']['id'], self.show_a.id)

    def test_episode_share_card_endpoint(self):
        url = reverse('podcasts:episode_share_card', kwargs={'episode_id': self.episode_a.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.episode_a.title)
        self.assertEqual(response.data['show_title'], self.show_a.title)
        self.assertIn('/shows/', response.data['share_url'])
        self.assertIn(self.episode_a.title, response.data['share_text'])

    @patch('apps.podcasts.tasks.generate_source_podcast_task.delay')
    def test_generate_from_source_without_show_uses_default_show(self, mock_delay):
        self.client.force_authenticate(self.user)
        url = reverse('podcasts:episode_generate_from_source')
        payload = {
            'source_url': 'https://news.ycombinator.com/',
            'template': 'news_flash',
            'max_items': 3,
            'dry_run': False,
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        episode = Episode.objects.get(id=response.data['episode_id'])
        self.assertEqual(episode.show.creator_id, self.user.id)
        self.assertTrue(episode.show.slug.startswith(f'audio-workbench-{self.user.id}'))
        mock_delay.assert_called_once()

    @patch('apps.podcasts.tasks.generate_podcast_task.delay')
    def test_generate_from_script_without_show_uses_default_show(self, mock_delay):
        self.client.force_authenticate(self.user)
        url = reverse('podcasts:episode_generate')
        payload = {
            'title': 'Script Episode',
            'script': '【大牛】测试\n【一帆】好的',
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        episode = Episode.objects.get(id=response.data['episode_id'])
        self.assertEqual(episode.show.creator_id, self.user.id)
        self.assertTrue(episode.show.slug.startswith(f'audio-workbench-{self.user.id}'))
        mock_delay.assert_called_once()
