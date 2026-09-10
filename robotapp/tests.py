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

	def test_index_calculates_todays_task_status_distribution(self):
		now = timezone.now()
		Task.objects.create(task_time=now, status=Task.Status.WAITING)
		Task.objects.create(task_time=now, status=Task.Status.IN_PROGRESS)
		Task.objects.create(task_time=now, status=Task.Status.COMPLETED)
		Task.objects.create(task_time=now - timedelta(days=1), status=Task.Status.CANCELLED)

		response = self.client.get(reverse('robotapp:index'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['today_task_count'], 3)
		self.assertEqual(
			response.context['task_status_distribution'],
			[
				{'label': '대기', 'count': 1, 'percent': 33, 'color_class': 'bg-blue'},
				{'label': '진행', 'count': 1, 'percent': 33, 'color_class': 'bg-green'},
				{'label': '완료', 'count': 1, 'percent': 33, 'color_class': 'bg-orange'},
				{'label': '취소', 'count': 0, 'percent': 0, 'color_class': 'bg-purple'},
			],
		)

	def test_index_shows_active_tasks_from_database(self):
		now = timezone.now()
		waiting_task = Task.objects.create(
			task_time=now, status=Task.Status.WAITING, priority=Task.Priority.NORMAL,
		)
		in_progress_task = Task.objects.create(
			task_time=now, status=Task.Status.IN_PROGRESS, priority=Task.Priority.URGENT,
		)
		completed_task = Task.objects.create(
			task_time=now, status=Task.Status.COMPLETED, priority=Task.Priority.NORMAL,
		)

		response = self.client.get(reverse('robotapp:index'))

		self.assertContains(response, f'TSK-{waiting_task.task_id:04d}')
		self.assertContains(response, f'TSK-{in_progress_task.task_id:04d}')
		self.assertNotContains(response, f'TSK-{completed_task.task_id:04d}')
		self.assertNotContains(response, '작업 유형')

	def test_realtime_monitor_shows_database_operations(self):
		now = timezone.now()
		amr = AMR.objects.create(robot_state=1, operation_state=3, battery=25)
		active_task = Task.objects.create(
			task_time=now, amr=amr, status=Task.Status.IN_PROGRESS, priority=Task.Priority.URGENT,
		)
		completed_task = Task.objects.create(
			task_time=now, status=Task.Status.COMPLETED,
		)

		response = self.client.get(reverse('robotapp:realtime_monitor'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, f'AMR-{amr.amr_id:03d}')
		self.assertContains(response, f'TASK-{active_task.task_id:04d}')
		self.assertNotContains(response, f'TASK-{completed_task.task_id:04d}')
		self.assertContains(response, '배터리 부족')


