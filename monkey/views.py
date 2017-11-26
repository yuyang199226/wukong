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

        print(username,password)
        account_obj = models.Account.objects.filter(username=username,password=password).first()
        if account_obj:
            # 用户名密码正确
            tk = token(account_obj.username)
            models.Token.objects.update_or_create(user=account_obj,defaults={
                'token_value':tk
            })
            response = HttpResponse('ok',status=200)
            response.set_cookie('token_value',tk)


        else:
            data = {
                'status':1001,
                'error':'用户名或者密码错误'
            }
            response = HttpResponse(json.dumps(data))

        response['Access-Control-Allow-Origin']='http://127.0.0.1:8090'
        response['Access-Control-Allow-Credentials'] = "true"
        return response

    def options(self, request, *args, **kwargs):
        response = HttpResponse('ok')
        response['Access-Control-Allow-Methods'] = "POST"  # 允许跨域访问的 请求方式
        response['Access-Control-Allow-Origin']="http://127.0.0.1:8090"
        response['Access-Control-Allow-Headers'] = "X-Custom-Header,Content-Type"  # 允许请求头 值为 请求头的key
        response['Access-Control-Allow-Credentials'] = "true"  #
        return response



class CourseSerializer(serializers.Serializer):
    '''课程'''
    id = serializers.IntegerField()
    name = serializers.CharField()
    brief = serializers.CharField()
    level = serializers.CharField()


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
    # recommend_courses = serializers.CharField()
    # teachers = serializers.CharField(source='teachers.all')

class CoursesView(APIView):
    authentication_classes = [CustomAuthentication]
    def get(self,request,*args,**kwargs):
        print('user', request.user)
        pk = self.kwargs.get('pk',None)
        if pk:
            course_obj = models.CourseDetail.objects.get(course=pk)
            ser = CourseDetailSerializer(instance=course_obj, many=False)
        else:
            course_ls = models.Course.objects.all()
            ser = CourseSerializer(instance=course_ls,many=True)
        # print(ser.data)
        #拿到所有课程
        response = HttpResponse(json.dumps(ser.data))
        response['Access-Control-Allow-Origin'] = "http://127.0.0.1:8090"
        response['Access-Control-Allow-Credentials'] = "true"
        return response
