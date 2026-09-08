from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), 
    path('list/', views.list, name='list'),
    path('write/', views.write, name='write'), # 회원 생성
    path('write/write_ok/', views.write_ok, name='write_ok'),
    path('delete/<int:id>', views.delete, name='delete'),
    path('update/<int:id>', views.update, name='update'),
    path('update/update_ok/<int:id>', views.update_ok, name='update_ok'),
    path('login/', views.login, name='login'),
    path('login/login_ok/', views.login_ok, name='login_ok'),
    path('logout/', views.logout, name='logout'),

    # 회원가입
    path('join/', views.join, name='join'),    
    path('check_email/', views.check_email, name='check_email'), 

    path('template1/', views.test1, name='template1'),
    path('template2/', views.test2, name='template2'),
    path('template3/', views.test3, name='template3'),

    
    # 게시판
    path('board/write/', views.board_write, name='board_write'),  #Create
    path('board/write/write_ok/', views.board_write_ok, name='board_write_ok'),  #Create
    path('board/list/', views.board_list, name='board_list'),   #Read List
    path('board/content/<int:id>', views.board_content, name='board_content'),
    path('board/update/<int:id>', views.board_update, name='board_update'),
    path('board/update/update_ok/<int:id>', views.board_update_ok, name='board_update_ok'),
    path('board/delete/<int:id>', views.board_delete, name='board_delete'),
    path('board/upload/<int:id>', views.board_upload, name='board_upload'),
    path('board/upload/upload_ok/<int:id>', views.board_upload_ok, name='board_upload_ok'),


    # file upload
    path('upload/', views.upload, name='upload'),
    path('upload/upload_ok/', views.upload_ok, name='upload_ok'),
    path('upload/list/', views.upload_list, name='upload_list'),
    path('upload/delete/<int:id>/', views.upload_delete, name='upload_delete'),

    path('chart/', views.chart, name='chart'),
    path('chart/chart_data/', views.chart_data, name='chart_data'),
    path('chart/chart_data2/', views.chart_data2, name='chart_data2'),
]