from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
from django.utils import timezone
from django.template import loader
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Count
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import AMR, Address, Inventory, Item, Location, Order, OrderDetail, Member, Task, TaskRecord, Zone

def get_item_volume(item):
    return item.width * item.length * item.height

def refresh_location_storage(location_id):
    location = Location.objects.get(pk=location_id)
    inventories = Inventory.objects.filter(location=location).select_related('item')
    location.cur_storage = sum(
        inventory.cur_item_num * get_item_volume(inventory.item)
        for inventory in inventories
    )
    location.save(update_fields=['cur_storage'])
    return location

def index(request):
    template = loader.get_template('robotapp/index.html')
    today = timezone.now().date()
    today_orders = Order.objects.filter(req_time__date=today)
    hourly_orders = []
    for start_hour in range(0, 24, 6):
        end_hour = start_hour + 6
        period_orders = [order for order in today_orders if start_hour <= order.req_time.hour < end_hour]
        inbound_count = sum(order.order_type == Order.OrderType.INBOUND for order in period_orders)
        outbound_count = sum(order.order_type == Order.OrderType.OUTBOUND for order in period_orders)
        count = inbound_count + outbound_count
        hourly_orders.append({
            'label': f'{start_hour:02d}-{end_hour:02d}',
            'count': count,
            'inbound_count': inbound_count,
            'outbound_count': outbound_count,
        })
    max_hourly_count = max((item['count'] for item in hourly_orders), default=0)
    for item in hourly_orders:
        item['height'] = round(item['count'] * 100 / max_hourly_count) if max_hourly_count else 0
        item['inbound_percent'] = round(item['inbound_count'] * 100 / item['count']) if item['count'] else 0
        item['outbound_percent'] = round(item['outbound_count'] * 100 / item['count']) if item['count'] else 0
    inventories = Inventory.objects.all()
    total_stock = sum(inventory.cur_item_num for inventory in inventories)
    shortage_count = sum(inventory.cur_item_num <= inventory.min_item_num for inventory in inventories)
    warning_count = sum(inventory.min_item_num < inventory.cur_item_num <= inventory.min_item_num * 2 for inventory in inventories)
    normal_count = inventories.count() - shortage_count - warning_count
    inventory_count = inventories.count() or 1
    zones = list(Zone.objects.order_by('zone_id'))
    twin_zones = [
        {
            'name': zone.name,
            'state': zone.state,
            'width': zone.width,
            'length': zone.length,
            'height': zone.height,
        }
        for zone in zones
    ]
    amrs = AMR.objects.select_related('location__zone').prefetch_related('tasks').order_by('amr_id')
    completed_task_counts = dict(
        Task.objects.filter(
            status=Task.Status.COMPLETED,
            end_time__date=today,
            amr__isnull=False,
        ).values('amr_id').annotate(count=Count('task_id')).values_list('amr_id', 'count')
    )
    max_completed_task_count = max(completed_task_counts.values(), default=0)
    robot_states = {0: '정지', 1: '정상'}
    operation_states = {0: '대기', 1: '운행 중', 2: '충전 중', 3: '작업 중', 4: '점검 중'}
    for amr in amrs:
        amr.robot_state_label = robot_states.get(amr.robot_state, '알 수 없음')
        amr.operation_state_label = operation_states.get(amr.operation_state, '알 수 없음')
        amr.completed_task_count = completed_task_counts.get(amr.amr_id, 0)
        amr.completed_task_height = round(amr.completed_task_count * 100 / max_completed_task_count) if max_completed_task_count else 0
        amr.current_task = next((task for task in amr.tasks.all() if task.status in [Task.Status.WAITING, Task.Status.IN_PROGRESS]), None)
    amr_data = [
        {
            'id': amr.amr_id,
            'battery': amr.battery,
            'x': amr.location.x_coord if amr.location else 0,
            'y': amr.location.y_coord if amr.location else 0,
            'z': amr.location.z_coord if amr.location else 0,
            'operation_state': amr.operation_state,
            'operation_state_label': amr.operation_state_label,
            'task_id': amr.current_task.task_id if amr.current_task else None,
            'left': max(8, min(88, 8 + ((amr.location.x_coord if amr.location else 0) / 70) * 84)),
            'top': max(22, min(78, 22 + ((amr.location.y_coord if amr.location else 0) / 30) * 56)),
        }
        for amr in amrs
    ]
    context = {
        'admin_name': request.session.get('login_ok_user_name', '관리자'),
        'inbound_count': today_orders.filter(order_type=Order.OrderType.INBOUND).count(),
        'outbound_count': today_orders.filter(order_type=Order.OrderType.OUTBOUND).count(),
        'order_count': today_orders.count(),
        'hourly_orders': hourly_orders,
        'total_stock': total_stock,
        'normal_count': normal_count,
        'normal_percent': round(normal_count * 100 / inventory_count),
        'warning_count': warning_count,
        'warning_percent': round(warning_count * 100 / inventory_count),
        'shortage_count': shortage_count,
        'shortage_percent': round(shortage_count * 100 / inventory_count),
        'zones': zones,
        'twin_zones': twin_zones,
        'amrs': amrs,
        'amr_data': amr_data,
    }
    return HttpResponse(template.render(context, request))

def login(request):
    template = loader.get_template('robotapp/login.html')
    return HttpResponse(template.render({}, request))

def login_ok(request):
    #email = request.POST['email']
    #pwd = request.POST['pwd']
    email = request.POST.get('email', None)
    pwd = request.POST.get('pwd', None)
    #print('email:', email, ', pwd:', pwd)

    try:
        member = Member.objects.get(email=email)
    except Member.DoesNotExist:
        member = None
    #print('member:', member)
    if member != None:
        print('해당 email회원 존재함')
        if member.pwd == pwd:
            print('비밀번호까지 일치')
            result = 2

            request.session['login_ok_user'] = member.email
            request.session['login_ok_user_name'] = member.name
        else:
            print('비밀번호 틀림')
            result = 1
    else:
        print('해당 email회원 존재하지 않음')
        result = 0

    template = loader.get_template('robotapp/login_ok.html')
    context = {'result':result,}
    return HttpResponse(template.render(context, request))

def write(request):
    template = loader.get_template('robotapp/write.html')
    return HttpResponse(template.render({}, request))

def write_ok(request):
    x = request.POST['name']
    y = request.POST['addr']
    nowDatetime = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    address = Address(name=x, addr=y, rdate=nowDatetime)
    address.save()
    return HttpResponseRedirect(reverse('robotapp:index'))


#######################################################################################
# 회원가입
def join(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        name = request.POST.get('name', '').strip()
        pwd = request.POST.get('password', '')
        phone = request.POST.get('phone', '').strip()

        if Member.objects.filter(email=email).exists():
            context = {'error': '이미 가입된 이메일입니다.'}
        else:
            Member.objects.create(email=email, name=name, pwd=pwd, phone=phone)
            return HttpResponseRedirect(reverse('robotapp:login'))

        template = loader.get_template('robotapp/join.html')
        return HttpResponse(template.render(context, request))

    template = loader.get_template('robotapp/join.html')
    return HttpResponse(template.render({}, request))

from django.http import JsonResponse
def check_email(request):
    email = request.GET.get('email', None)
    is_exists = Member.objects.filter(email=email).exists()
    data = {'is_exists':is_exists} #dict
    return JsonResponse(data)

def inventory(request):
    orders = Order.objects.prefetch_related('details__item').order_by('-req_time', '-order_id')
    context = {
        'orders': orders,
        'inbound_count': orders.filter(order_type=Order.OrderType.INBOUND).count(),
        'outbound_count': orders.filter(order_type=Order.OrderType.OUTBOUND).count(),
        'order_type': request.GET.get('type', ''),
        'today': timezone.now().date(),
        'status_choices': Order.Status.choices,
    }
    template = loader.get_template('robotapp/inventory.html')
    return HttpResponse(template.render(context, request))

def amr_list(request):
    amrs = AMR.objects.select_related('location__zone').prefetch_related('tasks').order_by('amr_id')
    robot_states = {0: '정지', 1: '정상'}
    operation_states = {0: '대기', 1: '운행 중', 2: '충전 중', 3: '작업 중', 4: '점검 중'}
    for amr in amrs:
        amr.robot_state_label = robot_states.get(amr.robot_state, '알 수 없음')
        amr.operation_state_label = operation_states.get(amr.operation_state, '알 수 없음')
        amr.current_task = next((task for task in amr.tasks.all() if task.status in [Task.Status.WAITING, Task.Status.IN_PROGRESS]), None)
    template = loader.get_template('robotapp/amr_list.html')
    return HttpResponse(template.render({'amrs': amrs}, request))

def task_list(request):
    tasks = Task.objects.select_related('order', 'item', 'amr', 'start_location', 'end_location').order_by('status', '-task_time')
    # 이미 대기/진행 중인 작업을 배정받은 AMR은 후보에서 제외해 동시 작업 배정을 막는다
    busy_amr_ids = Task.objects.filter(
        status__in=[Task.Status.WAITING, Task.Status.IN_PROGRESS],
        amr__isnull=False,
    ).values_list('amr_id', flat=True)
    available_amrs = AMR.objects.filter(operation_state=0).exclude(amr_id__in=busy_amr_ids).order_by('amr_id')
    template = loader.get_template('robotapp/task_list.html')
    return HttpResponse(template.render({'tasks': tasks, 'available_amrs': available_amrs, 'status_choices': Task.Status.choices}, request))

def task_assign(request, task_id):
    if request.method == 'POST':
        with transaction.atomic():
            task = get_object_or_404(Task, pk=task_id)
            amr = get_object_or_404(AMR, pk=request.POST.get('amr_id'), operation_state=0)
            # 배정 시점에 해당 AMR이 다른 대기/진행 중 작업을 갖고 있는지 재확인
            has_active_task = Task.objects.filter(
                amr=amr,
                status__in=[Task.Status.WAITING, Task.Status.IN_PROGRESS],
            ).exclude(pk=task.pk).exists()
            if not has_active_task:
                task.amr = amr
                task.start_location = amr.location
                task.save(update_fields=['amr', 'start_location'])
                amr.operation_state = 3
                amr.save(update_fields=['operation_state'])
    return HttpResponseRedirect(reverse('robotapp:task_list'))

def task_status_update(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=task_id)
        status = request.POST.get('status')
        valid_statuses = {str(choice.value) for choice in Task.Status}
        if status in valid_statuses:
            task.status = int(status)
            if task.status == Task.Status.IN_PROGRESS and not task.start_time:
                task.start_time = timezone.now()
            if task.status == Task.Status.COMPLETED and not task.end_time:
                task.end_time = timezone.now()
            if task.status != Task.Status.COMPLETED:
                task.end_time = None
            task.save(update_fields=['status', 'start_time', 'end_time'])
            # 작업이 종료/취소되면 다른 활성 작업이 없을 때 AMR을 대기 상태로 되돌린다
            if task.amr and task.status in (Task.Status.COMPLETED, Task.Status.CANCELLED):
                has_other_active_task = Task.objects.filter(
                    amr=task.amr,
                    status__in=[Task.Status.WAITING, Task.Status.IN_PROGRESS],
                ).exclude(pk=task.pk).exists()
                if not has_other_active_task:
                    task.amr.operation_state = 0
                    task.amr.save(update_fields=['operation_state'])
    return HttpResponseRedirect(reverse('robotapp:task_list'))

def task_record_list(request):
    records = TaskRecord.objects.select_related('task__amr').order_by('-record_time', '-task_record_id')
    task_id = request.GET.get('task_id', '').strip()
    amr_id = request.GET.get('amr_id', '').strip()
    if task_id:
        records = records.filter(task_id=task_id)
    if amr_id:
        records = records.filter(task__amr_id=amr_id)
    status_labels = {0: '대기', 1: '진행', 2: '완료', 3: '취소'}
    for record in records:
        record.status_label = status_labels.get(record.task_status, '알 수 없음')
    context = {
        'records': records,
        'task_id': task_id,
        'amr_id': amr_id,
        'amrs': AMR.objects.order_by('amr_id'),
    }
    template = loader.get_template('robotapp/task_record_list.html')
    return HttpResponse(template.render(context, request))

def inventory_status(request):
    inventories = Inventory.objects.select_related('item', 'location__zone').order_by('item__name')
    for inventory in inventories:
        if inventory.cur_item_num <= inventory.min_item_num:
            inventory.stock_status = '부족'
        elif inventory.cur_item_num <= inventory.min_item_num * 2:
            inventory.stock_status = '주의'
        else:
            inventory.stock_status = '정상'
    context = {
        'inventories': inventories,
        'total_stock': sum(inventory.cur_item_num for inventory in inventories),
    }
    template = loader.get_template('robotapp/inventory_status.html')
    return HttpResponse(template.render(context, request))

def order_create(request, order_type):
    items = Item.objects.order_by('name')
    destinations = Location.objects.filter(state=0, zone__state=0).select_related('zone').order_by('location_code')
    if request.method == 'POST':
        now = timezone.now()
        due_time = request.POST.get('due_time')
        due_time = datetime.fromisoformat(due_time) if due_time else now
        item = get_object_or_404(Item, pk=request.POST.get('item_id'))
        destination = get_object_or_404(
            Location.objects.select_related('zone'),
            pk=request.POST.get('destination_id'),
            state=0,
            zone__state=0,
        )
        quantity = int(request.POST.get('quantity', 0))
        inventory = get_object_or_404(Inventory, item=item)
        if order_type == Order.OrderType.OUTBOUND and inventory.cur_item_num < quantity:
            context = {'order_type': order_type, 'items': items, 'destinations': destinations, 'error': '현재 재고보다 출고 수량이 많습니다.'}
            template = loader.get_template('robotapp/order_form.html')
            return HttpResponse(template.render(context, request))
        if order_type == Order.OrderType.INBOUND:
            added_storage = quantity * get_item_volume(item)
            if inventory.location.max_storage < inventory.location.cur_storage + added_storage:
                context = {'order_type': order_type, 'items': items, 'destinations': destinations, 'error': '입고 후 보관 공간이 최대 보관량을 초과합니다.'}
                template = loader.get_template('robotapp/order_form.html')
                return HttpResponse(template.render(context, request))
        with transaction.atomic():
            order = Order.objects.create(
                order_type=order_type,
                req_time=now,
                due_time=due_time,
                priority=request.POST.get('priority', Order.Priority.NORMAL),
                status=Order.Status.WAITING,
            )
            OrderDetail.objects.create(item_num=quantity, order=order, item=item)
            Task.objects.create(
                task_time=now,
                priority=order.priority,
                status=Task.Status.WAITING,
                start_location=item.location,
                end_location=destination,
                order=order,
                item=item,
            )
            inventory.cur_item_num += quantity if order_type == Order.OrderType.INBOUND else -quantity
            inventory.save(update_fields=['cur_item_num'])
            refresh_location_storage(inventory.location_id)
        return HttpResponseRedirect(reverse('robotapp:inventory'))

    context = {'order_type': order_type, 'items': items, 'destinations': destinations}
    template = loader.get_template('robotapp/order_form.html')
    return HttpResponse(template.render(context, request))

def order_status_update(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=order_id)
        status = request.POST.get('status')
        valid_statuses = {str(choice.value) for choice in Order.Status}
        if status in valid_statuses:
            order.status = int(status)
            if order.status == Order.Status.COMPLETED and not order.end_time:
                order.end_time = timezone.now()
            elif order.status != Order.Status.COMPLETED:
                order.end_time = None
            order.save(update_fields=['status', 'end_time'])
    return HttpResponseRedirect(reverse('robotapp:inventory'))

def item_list(request):
    items = Item.objects.select_related('location__zone').prefetch_related('inventories').order_by('item_id')
    template = loader.get_template('robotapp/item_list.html')
    return HttpResponse(template.render({'items': items}, request))

def item_create(request):
    locations = Location.objects.select_related('zone').order_by('location_code')
    if request.method == 'POST':
        item = Item.objects.create(
            name=request.POST.get('name', '').strip(),
            width=request.POST.get('width'),
            length=request.POST.get('length'),
            height=request.POST.get('height'),
            item_class=request.POST.get('item_class'),
            incoming_date=datetime.fromisoformat(request.POST.get('incoming_date')),
            location_id=request.POST.get('location_id') or None,
        )
        inventory = Inventory.objects.create(
            cur_item_num=request.POST.get('cur_item_num', 0),
            min_item_num=request.POST.get('min_item_num', 0),
            item=item,
            location_id=request.POST.get('location_id'),
        )
        location = inventory.location
        if location.cur_storage + inventory.cur_item_num * get_item_volume(item) > location.max_storage:
            inventory.delete()
            item.delete()
            context = {'locations': locations, 'item': None, 'error': '물품 부피가 선택한 위치의 최대 보관부피를 초과합니다.'}
            template = loader.get_template('robotapp/item_form.html')
            html = template.render(context, request)
            error = '<div style="margin-bottom:12px;color:#fca5a5;font-weight:600;">물품 부피가 선택한 위치의 최대 보관부피를 초과합니다.</div>'
            return HttpResponse(html.replace('<form method="post">', error + '<form method="post">', 1))
        refresh_location_storage(inventory.location_id)
        return HttpResponseRedirect(reverse('robotapp:item_list'))
    context = {'locations': locations, 'item': None}
    template = loader.get_template('robotapp/item_form.html')
    return HttpResponse(template.render(context, request))

def item_edit(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    inventory = item.inventories.first()
    locations = Location.objects.select_related('zone').order_by('location_code')
    if request.method == 'POST':
        old_location_id = item.location_id
        old_volume = get_item_volume(item) * (inventory.cur_item_num if inventory else 0)
        item.name = request.POST.get('name', '').strip()
        item.width = request.POST.get('width')
        item.length = request.POST.get('length')
        item.height = request.POST.get('height')
        item.item_class = request.POST.get('item_class')
        item.incoming_date = datetime.fromisoformat(request.POST.get('incoming_date'))
        item.location_id = request.POST.get('location_id') or None
        if inventory:
            new_volume = get_item_volume(item) * int(request.POST.get('cur_item_num', 0))
            target_location = Location.objects.get(pk=request.POST.get('location_id'))
            available_storage = target_location.cur_storage
            if old_location_id == target_location.pk:
                available_storage -= old_volume
            if available_storage + new_volume > target_location.max_storage:
                context = {'locations': locations, 'item': item, 'inventory': inventory, 'error': '수정 후 물품 부피가 위치의 최대 보관부피를 초과합니다.'}
                template = loader.get_template('robotapp/item_form.html')
                html = template.render(context, request)
                error = '<div style="margin-bottom:12px;color:#fca5a5;font-weight:600;">수정 후 물품 부피가 위치의 최대 보관부피를 초과합니다.</div>'
                return HttpResponse(html.replace('<form method="post">', error + '<form method="post">', 1))
            item.save()
            inventory.cur_item_num = request.POST.get('cur_item_num', 0)
            inventory.min_item_num = request.POST.get('min_item_num', 0)
            inventory.location_id = request.POST.get('location_id')
            inventory.save()
            refresh_location_storage(inventory.location_id)
            if old_location_id and old_location_id != inventory.location_id:
                refresh_location_storage(old_location_id)
        else:
            item.save()
        return HttpResponseRedirect(reverse('robotapp:item_list'))
    context = {'locations': locations, 'item': item, 'inventory': inventory}
    template = loader.get_template('robotapp/item_form.html')
    return HttpResponse(template.render(context, request))

def item_delete(request, item_id):
    if request.method == 'POST':
        get_object_or_404(Item, pk=item_id).delete()
    return HttpResponseRedirect(reverse('robotapp:item_list'))

def zone_list(request):
    zones = Zone.objects.order_by('zone_id')
    for zone in zones:
        zone.state_label = '사용 가능' if zone.state == 0 else '사용 불가'
    template = loader.get_template('robotapp/zone_list.html')
    html = template.render({'zones': zones}, request)
    html = html.replace('규격 (W × L × H)', '규격 (W × L × H, m)').replace('너비', '너비 (m)').replace('길이', '길이 (m)').replace('높이', '높이 (m)')
    return HttpResponse(html)

def zone_create(request):
    if request.method == 'POST':
        Zone.objects.create(
            name=request.POST.get('name', '').strip(),
            state=request.POST.get('state', 0),
            org_x=request.POST.get('org_x'),
            org_y=request.POST.get('org_y'),
            org_z=request.POST.get('org_z'),
            width=request.POST.get('width'),
            length=request.POST.get('length'),
            height=request.POST.get('height'),
        )
        return HttpResponseRedirect(reverse('robotapp:zone_list'))
    template = loader.get_template('robotapp/zone_form.html')
    html = template.render({'zone': None}, request)
    html = html.replace('너비', '너비 (m)').replace('길이', '길이 (m)').replace('높이', '높이 (m)')
    return HttpResponse(html)

def zone_edit(request, zone_id):
    zone = get_object_or_404(Zone, pk=zone_id)
    if request.method == 'POST':
        for field in ['name', 'state', 'org_x', 'org_y', 'org_z', 'width', 'length', 'height']:
            setattr(zone, field, request.POST.get(field))
        zone.save()
        return HttpResponseRedirect(reverse('robotapp:zone_list'))
    template = loader.get_template('robotapp/zone_form.html')
    html = template.render({'zone': zone}, request)
    html = html.replace('너비', '너비 (m)').replace('길이', '길이 (m)').replace('높이', '높이 (m)')
    return HttpResponse(html)

def zone_delete(request, zone_id):
    if request.method == 'POST':
        zone = get_object_or_404(Zone, pk=zone_id)
        has_items = zone.locations.filter(items__isnull=False).exists()
        has_inventory = zone.locations.filter(inventories__isnull=False).exists()
        if has_items or has_inventory:
            zones = Zone.objects.order_by('zone_id')
            for current_zone in zones:
                current_zone.state_label = '사용 가능' if current_zone.state == 0 else '사용 불가'
            template = loader.get_template('robotapp/zone_list.html')
            html = template.render({'zones': zones}, request)
            error = '<div style="margin-bottom:12px;padding:11px 13px;border:1px solid #7f1d1d;border-radius:4px;background:#3f1218;color:#fca5a5;font-weight:600;">해당 구역에 물품이 있어서 삭제할 수 없습니다.</div>'
            return HttpResponse(html.replace('<section class="card">', error + '<section class="card">', 1))
        zone.delete()
    return HttpResponseRedirect(reverse('robotapp:zone_list'))

def location_list(request):
    locations = Location.objects.select_related('zone').order_by('location_code')
    for location in locations:
        location.state_label = '사용 가능' if location.state == 0 else '사용 불가'
    template = loader.get_template('robotapp/location_list.html')
    html = template.render({'locations': locations}, request)
    html = html.replace('최대보관량', '최대보관부피 (m³)').replace('현재보관량', '현재사용부피 (m³)')
    for location in locations:
        html = html.replace(
            f'>{location.max_storage}</td><td>{location.cur_storage}</td>',
            f'>{location.max_storage:.2f}</td><td>{location.cur_storage:.2f}</td>',
        )
    return HttpResponse(html)

def location_create(request):
    zones = Zone.objects.order_by('name')
    if request.method == 'POST':
        Location.objects.create(
            location_code=request.POST.get('location_code'),
            x_coord=request.POST.get('x_coord'),
            y_coord=request.POST.get('y_coord'),
            z_coord=request.POST.get('z_coord'),
            state=request.POST.get('state', 0),
            max_storage=request.POST.get('max_storage'),
            cur_storage=request.POST.get('cur_storage', 0),
            zone_id=request.POST.get('zone_id'),
        )
        return HttpResponseRedirect(reverse('robotapp:location_list'))
    template = loader.get_template('robotapp/location_form.html')
    html = template.render({'location': None, 'zones': zones}, request)
    html = html.replace('최대보관량', '최대보관부피 (m³)').replace('현재보관량', '현재사용부피 (m³)')
    return HttpResponse(html)

def location_edit(request, location_id):
    location = get_object_or_404(Location, pk=location_id)
    zones = Zone.objects.order_by('name')
    if request.method == 'POST':
        for field in ['location_code', 'x_coord', 'y_coord', 'z_coord', 'state', 'max_storage', 'cur_storage']:
            setattr(location, field, request.POST.get(field))
        location.zone_id = request.POST.get('zone_id')
        location.save()
        return HttpResponseRedirect(reverse('robotapp:location_list'))
    template = loader.get_template('robotapp/location_form.html')
    html = template.render({'location': location, 'zones': zones}, request)
    html = html.replace('최대보관량', '최대보관부피 (m³)').replace('현재보관량', '현재사용부피 (m³)')
    return HttpResponse(html)

def location_delete(request, location_id):
    if request.method == 'POST':
        location = get_object_or_404(Location, pk=location_id)
        if location.items.exists() or location.inventories.exists():
            locations = Location.objects.select_related('zone').order_by('location_code')
            for current_location in locations:
                current_location.state_label = '사용 가능' if current_location.state == 0 else '사용 불가'
            template = loader.get_template('robotapp/location_list.html')
            html = template.render({'locations': locations}, request)
            error = '<div style="margin-bottom:12px;padding:11px 13px;border:1px solid #7f1d1d;border-radius:4px;background:#3f1218;color:#fca5a5;font-weight:600;">해당 위치에 물품이 있어서 삭제할 수 없습니다.</div>'
            return HttpResponse(html.replace('<section class="card">', error + '<section class="card">', 1))
        location.delete()
    return HttpResponseRedirect(reverse('robotapp:location_list'))