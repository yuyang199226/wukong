import json
from . import models
from django.shortcuts import render,HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
# Create your views here.

from monkey.utils.authentication import token,CustomAuthentication
class LoginView(APIView):
    # self.dispatch
    def post(self,request,*args,**kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        account_obj = models.Account.objects.filter(username=username,password=password).first()
        if account_obj:
            # 用户名密码正确
            tk = token(account_obj.username)
            models.Token.objects.update_or_create(user=account_obj,defaults={
                'token_value':tk
            })
            data = {
                'status': 1000,
                'data':{
                    'username': account_obj.username,
                    'token': tk,
                    'userid': account_obj.pk
                }
            }
            response = HttpResponse(json.dumps(data),status=200)
            response.set_cookie('token_value',tk)
        else:
            data = {
                'status':1001,
                'error':'用户名或者密码错误'
            }
            response = HttpResponse(json.dumps(data))
        return response

    def options(self, request, *args, **kwargs):
        response = HttpResponse('ok')
        return response

#
# class MtoMField(serializers.CharField):
#     def get_attribute(self, instance):
#        return instance.objects.values('name','title')
#     def to_representation(self,value):
#
#         return list(value)

class MyField(serializers.CharField):
    def get_attribute(self, instance):
        #instance 是数据库对应的每行数据，即model 实例对象
        data_list = instance.recommend_courses.all()
        return data_list

    def to_representation(self, value):
        ret = []
        for row in value:
            ret.append({'id': row.id, 'name': row.name})
        return ret

class CourseSerializer(serializers.Serializer):
    '''课程'''
    level_name = serializers.CharField(source='get_level_display')
    id = serializers.IntegerField()
    name = serializers.CharField()
    brief = serializers.CharField()


class CourseDetailSerializer(serializers.Serializer):
    '''课程详情'''
    id = serializers.IntegerField()
    course = serializers.CharField(source='course.name')
    hours = serializers.IntegerField()
    why_study = serializers.CharField()
    what_to_study_brief = serializers.CharField()
    career_improvement = serializers.CharField()
    prerequisite = serializers.CharField()
    # recommend_courses = serializers.HyperlinkedIdentityField(view_name='coursedetail_json')
    recommend_courses = MyField()
    teachers = serializers.ListField(child=serializers.CharField(),source='teachers.all')

    # teacher_ls = MtoMField()


        # super(CourseDetailSerializer,self).to_representation(instance)

class CoursesView(APIView):
    authentication_classes = [CustomAuthentication]
    def get(self,request,*args,**kwargs):
        print('user', request.user)
        pk = self.kwargs.get('pk',None)
        if pk:
            course_obj = models.CourseDetail.objects.get(course=pk)
            ser = CourseDetailSerializer(instance=course_obj, many=False)
            print(ser.data)
        else:
            course_ls = models.Course.objects.all()
            ser = CourseSerializer(instance=course_ls,many=True)
        print(ser.data)
        #拿到所有课程
        response = HttpResponse(json.dumps(ser.data))
        return response
