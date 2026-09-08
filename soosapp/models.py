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

class Board(models.Model):    
    b_writer = models.CharField(max_length=14)
    b_email = models.EmailField(max_length=50)
    b_subject = models.CharField(max_length=50)
    b_date = models.DateTimeField()
    b_contents = models.CharField(max_length=50)  
    b_file = models.FileField(upload_to='uploads/%Y/%m/%d/', max_length=255)
    b_orgfile = models.CharField(max_length=255)
    b_filesize = models.IntegerField(default=0) 


class Upload(models.Model):
	title = models.CharField(max_length=200)
	file = models.FileField(upload_to='uploads/%Y/%m/%d/', max_length=255)
	orgfile = models.CharField(max_length=255)
	filesize = models.IntegerField(default=0)
	rdate = models.DateTimeField(auto_now_add=True)