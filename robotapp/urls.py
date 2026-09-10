from django.urls import path
from . import views

app_name = 'robotapp'

urlpatterns = [
    path('', views.index, name='index'), 
    path('digital-twin/', views.digital_twin, name='digital_twin'),
    path('monitor/', views.realtime_monitor, name='realtime_monitor'),
    path('login/', views.login, name='login'),
    path('login/', views.login, name='login'),
    path('login/login_ok/', views.login_ok, name='login_ok'),
    # 회원가입
    path('join/', views.join, name='join'),    
    path('check_email/', views.check_email, name='check_email'), 
    path('inventory/', views.inventory, name='inventory'),
    path('inventory/status/', views.inventory_status, name='inventory_status'),
    path('inventory/inbound/', views.order_create, {'order_type': 1}, name='inbound_create'),
    path('inventory/outbound/', views.order_create, {'order_type': 2}, name='outbound_create'),
    path('inventory/orders/<int:order_id>/status/', views.order_status_update, name='order_status_update'),
    path('inventory/items/', views.item_list, name='item_list'),
    path('inventory/items/create/', views.item_create, name='item_create'),
    path('inventory/items/<int:item_id>/edit/', views.item_edit, name='item_edit'),
    path('inventory/items/<int:item_id>/delete/', views.item_delete, name='item_delete'),
    path('inventory/zones/', views.zone_list, name='zone_list'),
    path('inventory/zones/create/', views.zone_create, name='zone_create'),
    path('inventory/zones/<int:zone_id>/edit/', views.zone_edit, name='zone_edit'),
    path('inventory/zones/<int:zone_id>/delete/', views.zone_delete, name='zone_delete'),
    path('inventory/locations/', views.location_list, name='location_list'),
    path('inventory/locations/create/', views.location_create, name='location_create'),
    path('inventory/locations/<int:location_id>/edit/', views.location_edit, name='location_edit'),
    path('inventory/locations/<int:location_id>/delete/', views.location_delete, name='location_delete'),
    path('amr/', views.amr_list, name='amr_list'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:task_id>/assign/', views.task_assign, name='task_assign'),
    path('tasks/<int:task_id>/status/', views.task_status_update, name='task_status_update'),
    path('tasks/records/', views.task_record_list, name='task_record_list'),
    path('api/amr/<int:amr_id>/location/', views.amr_location_update_api, name='amr_location_api'),
]