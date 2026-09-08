from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def index(request):
    #return HttpResponse("<center><h2>안녕 장고^^</h2></center>")
    template = loader.get_template('index.html')
    #return HttpResponse(template.render()) #session핸들링불가
    return HttpResponse(template.render({}, request)) #나중을 위해서 

from .models import Address
from django.db.models import Q
def list(request):
    template = loader.get_template('list.html')
    #addresses = Address.objects.all().values()
    #addresses = Address.objects.filter(name='홍길동').values()
    #addresses = Address.objects.filter(name='홍길동', addr='서울시').values()
    #addresses = Address.objects.filter(name='홍길동').values() | Address.objects.filter(addr='서울시').values()
    #addresses = Address.objects.filter(Q(name='홍길동')|Q(addr='서울시')).values()
    #addresses = Address.objects.filter(name__startswith='홍').values()
    #addresses = Address.objects.all().order_by('name').values()
    addresses = Address.objects.all().order_by('-name').values()
    context = { 'addresses':addresses, }
    return HttpResponse(template.render(context, request))

def write(request):
    template = loader.get_template('write.html')
    return HttpResponse(template.render({}, request))

from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
def write_ok(request):
    x = request.POST['name']
    y = request.POST['addr']
    nowDatetime = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    address = Address(name=x, addr=y, rdate=nowDatetime)
    address.save()
    return HttpResponseRedirect(reverse('list'))

def delete(request, id):
    address = Address.objects.get(id=id)
    address.delete()
    return HttpResponseRedirect(reverse('list')) 

def update(request, id):
    template = loader.get_template('update.html')
    address = Address.objects.get(id=id)
    context = { 'address':address, }
    return HttpResponse(template.render(context, request))

def update_ok(request, id):
    x = request.POST['name']
    y = request.POST['addr']
    address = Address.objects.get(id=id)
    address.name = x
    address.addr = y
    nowDatetime = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    address.rdate = nowDatetime
    address.save()
    return HttpResponseRedirect(reverse('list'))

def login(request):
    template = loader.get_template('login.html')
    return HttpResponse(template.render({}, request))

from .models import Member
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
        else:
            print('비밀번호 틀림')
            result = 1
    else:
        print('해당 email회원 존재하지 않음')
        result = 0

    temlate = loader.get_template("login_ok.html")
    context = {'result':result,}
    return HttpResponse(temlate.render(context, request))

def logout(request):
    if request.session.get('login_ok_user'):
        del request.session['login_ok_user']
        request.session.clear() # 서버측의 해당 user의 session방을 초기화
        request.session.flush() # 서버측의 해당 user의 session방을 삭제
    return HttpResponseRedirect('../')


#######################################################################################
# 회원가입
def join(request):
    template = loader.get_template('join.html')
    return HttpResponse(template.render({}, request))

from django.http import JsonResponse
def check_email(request):
    email = request.GET.get('email', None)
    is_exists = Member.objects.filter(email=email).exists()
    data = {'is_exists':is_exists} #dict
    return JsonResponse(data)

def test1(request):
    addresses = Address.objects.all().values()
    template = loader.get_template('template1.html')
    context = {
        'yourname':'길동',
        'addresses':addresses,
    }
    return HttpResponse(template.render(context, request))

def test2(request):
    template = loader.get_template('template2.html')
    list = ['apple', 'orange']
    context = {
        'x': 1,
        'y': 'tiger',
        'fruits': list,
        'fruits2': list,
    }
    return HttpResponse(template.render(context, request))

def test3(request):
    addresses = Address.objects.all().values()
    template = loader.get_template('template3.html')
    context = {
        'fruits': ['apple', 'orange', 'melon'],
        'cars':[{'brand':'현대','model':'그랜저', 'year':'2026'},
                {'brand':'테슬라','model':'모델Y', 'year':'2025'}
        ],
        'addresses':addresses,
    }
    return HttpResponse(template.render(context, request))



#######################################################################################
# 게시판 - Start
from .models import Board
#Create
def board_write(request):
    template = loader.get_template('board/write.html')
    return HttpResponse(template.render({}, request))

def board_write_ok(request):
    writer = request.POST['writer']
    email = request.POST['email']       
    subject = request.POST['subject']
    nowDatetime = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    content = request.POST['content']
    board = Board(b_writer=writer, b_email=email, b_subject=subject, b_date=nowDatetime, b_contents=content)
    board.save()    
    return HttpResponseRedirect(reverse('board_list'))

#Read
def board_list(request):
    template = loader.get_template('board/list.html')
    boards = Board.objects.all().values()
    #addresses = Address.objects.filter(name='홍길동').values() #filter로 조건검색
    #addresses = Address.objects.filter(name='홍길동', addr='서울시').values() #filter로 조건검색
    #addresses = Address.objects.filter(Q(name='홍길동') & Q(addr='서울시')).values()
    #addresses = Address.objects.filter(name='홍길동').values() | Address.objects.filter(addr='서울시').values()
    #addresses = Address.objects.filter(Q(name='홍길동') | Q(addr='서울시')).values()
    #addresses = Address.objects.filter(name__startswith='홍').values() #name이 홍으로 시작하는 사람
    #addresses = Address.objects.filter(addr__contains='서울').values() #name이 홍으로 시작하는 사람
    #addresses = Address.objects.all().order_by('-name').values()
    #board = Board.objects.all().order_by('-name', 'addr', '-id').values()
    # -> select * from address order by name desc, addr asc, id desc;
    context = { 'boards':boards, }
    return HttpResponse(template.render(context, request))

def board_content(request, id):
    template = loader.get_template('board/content.html')    
    board = Board.objects.get(id=id)     
    context = { 'board':board, }   
    return HttpResponse(template.render(context, request))

#Update
def board_update(request, id):
    template = loader.get_template('board/update.html')
    board = Board.objects.get(id=id)      
    context = { 'board':board, }   
    return HttpResponse(template.render(context, request))

def board_update_ok(request, id):    
    board = Board.objects.get(id=id)
    board.b_writer = request.POST['writer']
    board.b_email = request.POST['email']
    board.b_subject = request.POST['subject']
    board.b_contents = request.POST['content']
    #board.b_file = request.POST['file']
    #board.b_file = request.FILES.get('file', None)  # Optional file upload
    nowDatetime = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    board.b_date = nowDatetime
    board.save()
    return HttpResponseRedirect(reverse('board_list'))

def board_delete(request, id):
    board = Board.objects.get(id=id)
    board.delete()
    return HttpResponseRedirect(reverse('board_list')) 

# File Upload
def board_upload(request, id):
    template = loader.get_template('board/upload.html')
    board = Board.objects.get(id=id)
    return HttpResponse(template.render({'board': board}, request))

def board_upload_ok(request, id):
    if request.method != 'POST':
        return HttpResponseRedirect('../')

    t = request.POST['title']
    f = request.FILES['file']
    ext = os.path.splitext(f.name)[1].lower() #'보고서.XLSX' -> .xlsx

    if ext not in ALLOWED:
        return error_back('허용하지 않는 확장자입니다 : ' + ext)
    if f.size > MAX_SIZE:
        return error_back('파일이 너무 큽니다 (5MB 이하)')

    board = Board.objects.get(id=id)
    board.b_file = f
    board.b_orgfile = f.name
    board.b_filesize = f.size    
    board.save()

    # row = Upload(title=t, file=f, orgfile=f.name, filesize=f.size)
    # row.save()

    template = loader.get_template('board/upload_ok.html')
    return HttpResponse(template.render({'board': board}, request))
#######################################################################################
# 게시판 - End



import os
from .models import Upload
ALLOWED = ['.jpg', '.jpeg', '.png', '.gif', '.txt', '.pdf', '.docx', '.csv', '.xlsx']

#<1> MAX_SIZE 조정
#MAX_SIZE = 5 * 1024 * 1024 # 5MB
from pj_django import settings
MAX_SIZE = settings.MAX_UPLOAD_MB * 1024 * 1024

def upload(request):
    template = loader.get_template('upload.html')
    return HttpResponse(template.render({'max_mb': settings.MAX_UPLOAD_MB}, request))

#views.py
def upload_ok(request):
    if request.method != 'POST':
        return HttpResponseRedirect('../')

    t = request.POST['title']
    f = request.FILES['file']
    ext = os.path.splitext(f.name)[1].lower() #'보고서.XLSX' -> .xlsx

    if ext not in ALLOWED:
        return error_back('허용하지 않는 확장자입니다 : ' + ext)
    if f.size > MAX_SIZE:
        #<2> 변경
        return error_back('파일이 너무 큽니다 (' + str(settings.MAX_UPLOAD_MB) + 'MB 이하)')

    row = Upload(title=t, file=f, orgfile=f.name, filesize=f.size)
    row.save()

    template = loader.get_template('upload_ok.html')
    return HttpResponse(template.render({'row':row}, request))

def error_back(msg):
    html = "<meta charset='utf-8'><script>alert('" + msg + "'); history.back();</script>"
    return HttpResponse(html)


def upload_list(request):
    rows = Upload.objects.all().order_by('-id')
    template = loader.get_template('upload_list.html')
    return HttpResponse(template.render({'rows':rows}, request))

from django.shortcuts import get_object_or_404
def upload_delete(request, id):
    row = get_object_or_404(Upload, id=id)
    row.file.delete(save=False)  #실제 파일 삭제
    row.delete()  #DB 레코드 삭제    
    return HttpResponseRedirect('../../list/')

def chart(request):
    template = loader.get_template('chart.html')
    return HttpResponse(template.render({}, request))

from django.db.models import Count
def chart_data(request):
    #select addr, count(id) as cnt from soosapp_address group by addr order by cnt desc;
    rows = Address.objects.values('addr').annotate(cnt=Count('id')).order_by('-cnt')
    labels = [r['addr'] for r in rows] #['서울시', '부산시', '대구시', ...]
    data = [r['cnt']for r in rows] #[4, 2, 1, ...]
    return JsonResponse({'labels':labels, 'data':data})

from django.db.models.functions import TruncDate
def chart_data2(request):
    #select date(rdate) as d, count(id) as cnt from soosapp_address group by d order by d;
    rows = (Address.objects
    .annotate(d=TruncDate('rdate'))
    .values('d')
    .annotate(cnt=Count('id'))
    .order_by('d'))
    #labels = [ r['d'].strftime('%Y:%m:%d')for r in rows]
    labels = [ r['d'] for r in rows]
    data = [r['cnt']for r in rows] #[4, 2, 1, ...]
    return JsonResponse({'labels':labels, 'data':data})

