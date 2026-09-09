from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone


from .models import AMR, Task


class DashboardTests(TestCase):
	def test_index_shows_todays_completed_tasks_per_amr(self):
		now = timezone.now()
		first_amr = AMR.objects.create(robot_state=1, operation_state=0, battery=80)
		second_amr = AMR.objects.create(robot_state=1, operation_state=0, battery=70)

		for _ in range(2):
			Task.objects.create(
				task_time=now - timedelta(hours=1), amr=first_amr,
				status=Task.Status.COMPLETED, end_time=now,
			)
		Task.objects.create(
			task_time=now - timedelta(days=1), amr=second_amr,
			status=Task.Status.COMPLETED, end_time=now - timedelta(days=1),
		)
		Task.objects.create(
			task_time=now, amr=second_amr, status=Task.Status.IN_PROGRESS,
		)

		response = self.client.get(reverse('robotapp:index'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'AMR-001')
		self.assertContains(response, 'AMR-002')


