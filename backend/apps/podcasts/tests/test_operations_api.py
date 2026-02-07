from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from apps.interactions.models import Follow
from apps.podcasts.models import Episode, Show, ScriptSession
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
        self.normal_user = User.objects.create_user(
            username='normal-user',
            email='normal-user@example.com',
            password='test-pass-123',
            is_creator=False,
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
        self.assertEqual(episode.show.title, f'{self.user.username}的频道')
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
        self.assertEqual(episode.show.title, f'{self.user.username}的频道')
        mock_delay.assert_called_once()

    @patch('apps.podcasts.tasks.generate_podcast_task.delay')
    def test_generate_from_script_with_speaker_config(self, mock_delay):
        self.client.force_authenticate(self.user)
        url = reverse('podcasts:episode_generate')
        payload = {
            'title': 'Script Episode',
            'script': '【大牛】测试\n【一帆】好的',
            'host_name': '主持甲',
            'guest_name': '嘉宾乙',
            'host_voice_id': 'Chinese (Mandarin)_News_Anchor',
            'guest_voice_id': 'Chinese (Mandarin)_Radio_Host',
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        episode = Episode.objects.get(id=response.data['episode_id'])
        speaker_config = (episode.generation_meta or {}).get('speaker_config') or {}
        self.assertEqual(speaker_config.get('host_name'), '主持甲')
        self.assertEqual(speaker_config.get('guest_name'), '嘉宾乙')
        self.assertEqual(speaker_config.get('host_voice_id'), 'Chinese (Mandarin)_News_Anchor')
        self.assertEqual(speaker_config.get('guest_voice_id'), 'Chinese (Mandarin)_Radio_Host')

        self.assertTrue(mock_delay.called)
        _, kwargs = mock_delay.call_args
        self.assertEqual(kwargs['speaker_config']['host_name'], '主持甲')
        self.assertEqual(kwargs['speaker_config']['guest_name'], '嘉宾乙')

    @patch('apps.podcasts.services.voice_catalog.get_available_tts_voices')
    def test_tts_voices_endpoint(self, mock_get_voices):
        self.client.force_authenticate(self.user)
        mock_get_voices.return_value = {
            'source': 'minimax',
            'message': 'success',
            'voices': [
                {
                    'voice_id': 'Chinese (Mandarin)_News_Anchor',
                    'voice_name': 'News Anchor',
                    'language': 'zh',
                }
            ],
            'count': 1,
        }

        url = reverse('podcasts:tts_voices')
        response = self.client.get(url, {'language': 'zh', 'refresh': '1'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['voices'][0]['voice_id'], 'Chinese (Mandarin)_News_Anchor')
        mock_get_voices.assert_called_once_with(language='zh', force_refresh=True)

    @patch('apps.podcasts.tasks.generate_source_podcast_task.delay')
    def test_non_creator_can_generate_from_source(self, mock_delay):
        self.client.force_authenticate(self.normal_user)
        url = reverse('podcasts:episode_generate_from_source')
        payload = {
            'source_url': 'https://news.ycombinator.com/',
            'template': 'news_flash',
            'max_items': 2,
            'dry_run': False,
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        episode = Episode.objects.get(id=response.data['episode_id'])
        self.assertEqual(episode.show.creator_id, self.normal_user.id)
        self.assertTrue(episode.show.slug.startswith(f'audio-workbench-{self.normal_user.id}'))
        self.assertEqual(episode.show.title, f'{self.normal_user.username}的频道')
        mock_delay.assert_called_once()

    @patch('apps.podcasts.services.cover_ai.generate_show_cover_candidates')
    def test_generate_show_cover_options(self, mock_generate):
        self.client.force_authenticate(self.user)
        mock_generate.return_value = [
            {'path': 'show_cover_candidates/2026/02/cand-1.png', 'url': '/media/show_cover_candidates/cand-1.png'}
        ]

        url = reverse('podcasts:generate_show_cover_options', kwargs={'slug': self.show_a.slug})
        response = self.client.post(url, {'count': 4}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['show_id'], self.show_a.id)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['candidates']), 1)
        mock_generate.assert_called_once()

    @patch('apps.podcasts.services.cover_ai.apply_show_cover_candidate')
    def test_apply_show_cover_option(self, mock_apply):
        self.client.force_authenticate(self.user)
        mock_apply.return_value = '/media/covers/2026/02/ai-show-cover.png'

        url = reverse('podcasts:apply_show_cover_option', kwargs={'slug': self.show_a.slug})
        response = self.client.post(
            url,
            {'candidate_path': 'show_cover_candidates/2026/02/cand-1.png'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '封面已更新')
        self.assertEqual(response.data['cover_url'], '/media/covers/2026/02/ai-show-cover.png')
        mock_apply.assert_called_once()

    @patch('apps.podcasts.services.script_ai.ScriptAIService.chat')
    def test_script_chat_ai_failure_returns_fallback_message(self, mock_chat):
        self.client.force_authenticate(self.user)
        mock_chat.return_value = {
            'success': False,
            'error': 'upstream timed out',
            'response': None,
            'script': '',
            'tool_calls': None,
        }
        session = ScriptSession.objects.create(
            creator=self.user,
            title='chat fallback test',
        )

        response = self.client.post(
            f'/api/podcasts/script-sessions/{session.id}/chat/',
            {'message': '测试一下'},
            format='json',
        )
        session.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertFalse(response.data.get('has_script_update'))
        self.assertEqual(len(session.chat_history), 2)
        self.assertEqual(session.chat_history[0].get('role'), 'user')
        self.assertEqual(session.chat_history[1].get('role'), 'assistant')
