from datetime import time as dt_time, timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.podcasts.models import RSSSource, RSSList, RSSSchedule
from apps.podcasts.tasks import dispatch_rss_schedules_task
from apps.users.models import User


class RSSAutomationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='rss-auto-user',
            email='rss-auto-user@example.com',
            password='test-pass-123',
            is_creator=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_rss_source(self):
        url = reverse('podcasts:rss-source-list')
        payload = {
            'name': 'HN',
            'url': 'https://news.ycombinator.com/rss',
            'description': 'hacker news',
            'is_active': True,
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RSSSource.objects.filter(creator=self.user).count(), 1)

    def test_create_rss_list_with_sources(self):
        source = RSSSource.objects.create(
            creator=self.user,
            name='HN',
            url='https://news.ycombinator.com/rss',
            is_active=True,
        )
        url = reverse('podcasts:rss-list-list')
        payload = {
            'name': 'Tech List',
            'description': 'daily list',
            'source_ids': [source.id],
            'is_active': True,
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rss_list = RSSList.objects.get(id=response.data['id'])
        self.assertEqual(rss_list.sources.count(), 1)

    @patch('apps.podcasts.tasks.run_rss_schedule_task.delay')
    def test_create_and_trigger_schedule(self, mock_delay):
        source = RSSSource.objects.create(
            creator=self.user,
            name='HN',
            url='https://news.ycombinator.com/rss',
            is_active=True,
        )
        rss_list = RSSList.objects.create(
            creator=self.user,
            name='Tech List',
            description='d',
            is_active=True,
        )
        rss_list.sources.add(source)

        create_url = reverse('podcasts:rss-schedule-list')
        payload = {
            'name': 'Daily Tech',
            'rss_list_id': rss_list.id,
            'template': 'news_flash',
            'max_items': 5,
            'deduplicate': True,
            'sort_by': 'latest',
            'timezone_name': 'Asia/Shanghai',
            'run_time': '08:30',
            'frequency': 'daily',
            'week_days': [],
            'is_active': True,
        }
        create_response = self.client.post(create_url, payload, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(create_response.data['next_run_at'])

        schedule_id = create_response.data['id']
        trigger_url = reverse('podcasts:rss-schedule-trigger', kwargs={'pk': schedule_id})
        trigger_response = self.client.post(trigger_url, {}, format='json')

        self.assertEqual(trigger_response.status_code, status.HTTP_202_ACCEPTED)
        mock_delay.assert_called_once_with(schedule_id, trigger_type='manual')

    @patch('apps.podcasts.tasks.run_rss_schedule_task.delay')
    def test_dispatch_due_schedules(self, mock_delay):
        source = RSSSource.objects.create(
            creator=self.user,
            name='HN',
            url='https://news.ycombinator.com/rss',
            is_active=True,
        )
        rss_list = RSSList.objects.create(
            creator=self.user,
            name='Tech List',
            description='d',
            is_active=True,
        )
        rss_list.sources.add(source)
        schedule = RSSSchedule.objects.create(
            creator=self.user,
            name='Daily Tech',
            rss_list=rss_list,
            template='news_flash',
            max_items=5,
            deduplicate=True,
            sort_by='latest',
            timezone_name='Asia/Shanghai',
            run_time=dt_time(hour=8, minute=30),
            frequency='daily',
            is_active=True,
            next_run_at=timezone.now() - timedelta(minutes=1),
        )

        result = dispatch_rss_schedules_task(limit=10)
        schedule.refresh_from_db()

        self.assertIn('Queued 1 schedules', result)
        self.assertEqual(schedule.last_status, 'queued')
        self.assertTrue(schedule.next_run_at > timezone.now())
        mock_delay.assert_called_once_with(schedule.id, trigger_type='auto')
