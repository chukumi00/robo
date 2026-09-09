from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone


from .models import AMR, Order, Task


class DashboardTests(TestCase):
	def test_index_calculates_dashboard_operation_rates(self):
		now = timezone.now()
		AMR.objects.create(robot_state=1, operation_state=3, battery=80)
		AMR.objects.create(robot_state=1, operation_state=0, battery=70)
		AMR.objects.create(robot_state=0, operation_state=0, battery=60)
		Order.objects.create(
			order_type=Order.OrderType.INBOUND,
			req_time=now,
			due_time=now,
			status=Order.Status.COMPLETED,
		)
		Order.objects.create(
			order_type=Order.OrderType.OUTBOUND,
			req_time=now,
			due_time=now,
			status=Order.Status.WAITING,
		)

		response = self.client.get(reverse('robotapp:index'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'AMR 운영 가능률')
		self.assertContains(response, '67%')
		self.assertContains(response, 'AMR 가동률')
		self.assertContains(response, '33%')
		self.assertContains(response, '입출고 처리율')
		self.assertContains(response, '50%')

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


