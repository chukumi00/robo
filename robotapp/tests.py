import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AMR, Location, Task, TaskRecord, Zone


class AmrLocationApiTests(TestCase):
	def setUp(self):
		zone = Zone.objects.create(
			name='테스트 구역', state=0, org_x=0, org_y=0, org_z=0,
			width=100, length=100, height=10,
		)
		location = Location.objects.create(
			location_code=1, x_coord=0, y_coord=0, z_coord=0, state=0,
			max_storage=100, cur_storage=0, zone=zone,
		)
		self.amr = AMR.objects.create(
			robot_state=1, operation_state=3, battery=80, location=location,
		)
		self.task = Task.objects.create(
			task_time=timezone.now(), amr=self.amr, status=Task.Status.IN_PROGRESS,
		)
		self.url = reverse('robotapp:amr_location_api', args=[self.amr.amr_id])

	def test_location_update_records_same_position_at_each_time(self):
		payload = {'task_id': self.task.task_id, 'x': 12.5, 'y': 8, 'z': 0, 'timestamp': '2026-09-08T12:00:00+00:00'}
		response = self.client.post(self.url, data=json.dumps(payload), content_type='application/json')

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()['created'])
		self.assertEqual(TaskRecord.objects.count(), 1)
		self.assertEqual(TaskRecord.objects.get().task, self.task)

		response = self.client.post(self.url, data=json.dumps(payload), content_type='application/json')

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()['created'])
		self.assertEqual(TaskRecord.objects.count(), 2)

	def test_location_update_rejects_invalid_payload(self):
		response = self.client.post(self.url, data='{"x": "bad"}', content_type='application/json')

		self.assertEqual(response.status_code, 400)
		self.assertEqual(TaskRecord.objects.count(), 0)

	def test_task_record_list_renders_naive_record_time(self):
		TaskRecord.objects.create(
			task=self.task, x_coord=1, y_coord=2, z_coord=0,
			record_time=timezone.now(), task_status=self.task.status,
		)

		response = self.client.get(reverse('robotapp:task_record_list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '시간순 이동 경로')

	def test_task_record_list_filters_path_data_by_amr(self):
		other_amr = AMR.objects.create(robot_state=1, operation_state=3, battery=70)
		other_task = Task.objects.create(
			task_time=timezone.now(), amr=other_amr, status=Task.Status.IN_PROGRESS,
		)
		TaskRecord.objects.create(
			task=self.task, x_coord=10, y_coord=20, z_coord=0,
			record_time=timezone.now(), task_status=self.task.status,
		)
		TaskRecord.objects.create(
			task=other_task, x_coord=90, y_coord=80, z_coord=0,
			record_time=timezone.now(), task_status=other_task.status,
		)

		response = self.client.get(
			reverse('robotapp:task_record_list'), {'amr_id': self.amr.amr_id},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '"x": 10.0')
		self.assertNotContains(response, '"x": 90.0')

	def test_task_record_list_filters_by_displayed_task_number(self):
		TaskRecord.objects.create(
			task=self.task, x_coord=15, y_coord=25, z_coord=0,
			record_time=timezone.now(), task_status=self.task.status,
		)

		response = self.client.get(
			reverse('robotapp:task_record_list'),
			{'task_id': f'TASK-{self.task.task_id:04d}'},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '"x": 15.0')

	def test_task_record_list_uses_same_time_order_for_table_and_path(self):
		older = TaskRecord.objects.create(
			task=self.task, x_coord=1, y_coord=2, z_coord=0,
			record_time=timezone.now(), task_status=self.task.status,
		)
		newer = TaskRecord.objects.create(
			task=self.task, x_coord=3, y_coord=4, z_coord=0,
			record_time=older.record_time + timedelta(seconds=1),
			task_status=self.task.status,
		)

		response = self.client.get(
			reverse('robotapp:task_record_list'), {'amr_id': self.amr.amr_id},
		)
		content = response.content.decode()

		self.assertLess(content.index('"x": 1.0'), content.index('"x": 3.0'))
		self.assertLess(content.index('(1.0, 2.0)'), content.index('(3.0, 4.0)'))

	def test_task_record_list_json_refresh_returns_current_amr_path(self):
		TaskRecord.objects.create(
			task=self.task, x_coord=44, y_coord=55, z_coord=0,
			record_time=timezone.now(), task_status=self.task.status,
		)

		response = self.client.get(
			reverse('robotapp:task_record_list'),
			{'amr_id': self.amr.amr_id, 'format': 'json'},
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['points'][0]['x'], 44.0)

	def test_empty_path_page_still_enables_refresh(self):
		response = self.client.get(
			reverse('robotapp:task_record_list'), {'amr_id': self.amr.amr_id},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'id="path-data-json"')
		self.assertContains(response, 'window.setInterval(refreshPath, 3000)')

