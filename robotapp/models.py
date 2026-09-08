from django.db import models

class Address(models.Model):
    name = models.CharField(max_length=200)
    addr = models.TextField()
    rdate = models.DateTimeField()

class Member(models.Model):
    email = models.EmailField(max_length=254, primary_key=True)
    name = models.CharField(max_length=30)
    pwd = models.CharField(max_length=128)  
    phone = models.CharField(max_length=20) 

    # 생성 시 자동으로 현재 시간 저장
    rdate = models.DateTimeField(auto_now_add=True)
    # 수정/save() 시마다 자동으로 현재 시간갱신
    udate = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

class Order(models.Model):
    class OrderType(models.IntegerChoices):
        INBOUND = 1, '입고'
        OUTBOUND = 2, '출고'

    class Priority(models.IntegerChoices):
        NORMAL = 1, '일반'
        URGENT = 2, '긴급'

    class Status(models.IntegerChoices):
        WAITING = 0, '대기'
        IN_PROGRESS = 1, '진행'
        COMPLETED = 2, '완료'
        CANCELLED = 3, '취소'
        DELAYED = 4, '지연'

    order_id = models.AutoField(primary_key=True, db_column='ORDER_ID')
    order_type = models.IntegerField(choices=OrderType.choices, db_column='TYPE')
    req_time = models.DateTimeField(db_column='REQ_TIME')
    end_time = models.DateTimeField(null=True, blank=True, db_column='END_TIME')
    due_time = models.DateTimeField(db_column='DUE_TIME')
    priority = models.IntegerField(choices=Priority.choices, default=Priority.NORMAL, db_column='PRIORITY')
    status = models.IntegerField(choices=Status.choices, default=Status.WAITING, db_column='STATUS')

    class Meta:
        db_table = 'robotapp_order'

class Zone(models.Model):
    zone_id = models.AutoField(primary_key=True, db_column='ZONE_ID')
    name = models.CharField(max_length=50, db_column='NAME')
    state = models.IntegerField(db_column='STATE')
    org_x = models.FloatField(db_column='ORG_X')
    org_y = models.FloatField(db_column='ORG_Y')
    org_z = models.FloatField(db_column='ORG_Z')
    width = models.FloatField(db_column='WIDTH')
    length = models.FloatField(db_column='LENGTH')
    height = models.FloatField(db_column='HEIGHT')

    class Meta:
        db_table = 'robotapp_zone'

class Location(models.Model):
    location_id = models.AutoField(primary_key=True, db_column='LOCATION_ID')
    location_code = models.IntegerField(db_column='LOCATION_CODE')
    x_coord = models.FloatField(db_column='X_COORD')
    y_coord = models.FloatField(db_column='Y_COORD')
    z_coord = models.FloatField(db_column='Z_COORD')
    state = models.IntegerField(db_column='STATE')
    max_storage = models.FloatField(db_column='MAX_STORAGE')
    cur_storage = models.FloatField(db_column='CUR_STORAGE')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, db_column='ZONE_ID', related_name='locations')

    class Meta:
        db_table = 'robotapp_location'

class AMR(models.Model):
    amr_id = models.AutoField(primary_key=True, db_column='AMR_ID')
    robot_state = models.IntegerField(db_column='ROBOT_STATE')
    operation_state = models.IntegerField(db_column='OPERATION_STATE')
    battery = models.FloatField(db_column='BATTERY')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, db_column='LOCATION_ID', related_name='amrs')

    class Meta:
        db_table = 'robotapp_amr'
        constraints = [
            models.UniqueConstraint(
                fields=['location'],
                condition=models.Q(location__isnull=False),
                name='unique_amr_location',
            ),
        ]

class Item(models.Model):
    item_id = models.AutoField(primary_key=True, db_column='ITEM_ID')
    name = models.CharField(max_length=50, db_column='NAME')
    width = models.FloatField(db_column='WIDTH')
    length = models.FloatField(db_column='LENGTH')
    height = models.FloatField(db_column='HEIGHT')
    item_class = models.IntegerField(db_column='CLASS')
    incoming_date = models.DateTimeField(db_column='INCOMING_DATE')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, db_column='LOCATION_ID', related_name='items')

    class Meta:
        db_table = 'robotapp_item'

class Task(models.Model):
    class Priority(models.IntegerChoices):
        NORMAL = 1, '일반'
        URGENT = 2, '긴급'

    class Status(models.IntegerChoices):
        WAITING = 0, '대기'
        IN_PROGRESS = 1, '진행'
        COMPLETED = 2, '완료'
        CANCELLED = 3, '취소'

    task_id = models.AutoField(primary_key=True, db_column='TASK_ID')
    task_time = models.DateTimeField(db_column='TASK_TIME')
    amr = models.ForeignKey(AMR, on_delete=models.SET_NULL, null=True, blank=True, db_column='AMR_ID', related_name='tasks')
    priority = models.IntegerField(choices=Priority.choices, default=Priority.NORMAL, db_column='PRIORITY')
    status = models.IntegerField(choices=Status.choices, default=Status.WAITING, db_column='STATUS')
    start_time = models.DateTimeField(null=True, blank=True, db_column='START_TIME')
    end_time = models.DateTimeField(null=True, blank=True, db_column='END_TIME')
    start_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, db_column='START_LOCATION_ID', related_name='start_tasks')
    end_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, db_column='END_LOCATION_ID', related_name='end_tasks')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, db_column='ORDER_ID', related_name='tasks')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, db_column='ITEM_ID', related_name='tasks')

    class Meta:
        db_table = 'robotapp_task'

class TaskRecord(models.Model):
    task_record_id = models.AutoField(primary_key=True, db_column='TASK_RECORD_ID')
    x_coord = models.FloatField(db_column='X_COORD')
    y_coord = models.FloatField(db_column='Y_COORD')
    z_coord = models.FloatField(db_column='Z_COORD')
    record_time = models.DateTimeField(db_column='RECORD_TIME')
    task_status = models.IntegerField(db_column='TASK_STATUS')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, db_column='TASK_ID', related_name='records')

    class Meta:
        db_table = 'robotapp_task_record'

class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True, db_column='INVENTORY_ID')
    cur_item_num = models.IntegerField(db_column='CUR_ITEM_NUM')
    min_item_num = models.IntegerField(db_column='MIN_ITEM_NUM')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, db_column='ITEM_ID', related_name='inventories')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, db_column='LOCATION_ID', related_name='inventories')

    class Meta:
        db_table = 'robotapp_inventory'

class OrderHistory(models.Model):
    order_history_id = models.AutoField(primary_key=True, db_column='ORDER_HISTORY_ID')
    pre_state = models.IntegerField(db_column='PRE_STATE')
    change_state = models.IntegerField(db_column='CHANGE_STATE')
    status = models.IntegerField(db_column='STATUS')
    order_date = models.DateTimeField(db_column='ORDER_DATE')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='ORDER_ID', related_name='histories')

    class Meta:
        db_table = 'robotapp_order_history'

class OrderDetail(models.Model):
    order_detail_id = models.AutoField(primary_key=True, db_column='ORDER_DETAIL_ID')
    item_num = models.IntegerField(db_column='ITEM_NUM')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='ORDER_ID', related_name='details')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, db_column='ITEM_ID', related_name='order_details')

    class Meta:
        db_table = 'robotapp_order_detail'