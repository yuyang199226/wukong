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




""" Redis数据库 """
import redis
pool =redis.ConnectionPool(host='192.168.16.43', port=6379)
r = redis.Redis(connection_pool=pool)

"""价格与有课程效期表序列化"""
class ShopPriceJson(serializers.ModelSerializer):  # 模板
    valid_period = serializers.CharField(source='get_valid_period_display')
    class Meta:
        model = models.PricePolicy
        fields = ['valid_period','id','price']

""" 购物车API """
class Shopping(APIView):
    # obj = models.Course.objects.get(pk=1).price_policy #根据可能,或许关联的可能(多)
    # obj = models.PricePolicy.objects.get(pk=2).content_type #根据 价格与有课程效期表 找关联课程
    def get(self,request,*args,**kwargs):
        """ 获取购物车信息 """

        nid = 1 #用户id
        info = {'code': 200, 'msg': '', 'content': {'course':{}}} #返回的数据

        if not nid:
            info = {'code': 401, 'msg': '尚未登陆', 'content': ''}  # 状态信息
            return Response(info)

        course_list = r.hkeys('price_user_%s'%nid)   #所有的课程对象
        try:
            for i in course_list:
                i = str(i,encoding='utf-8')
                course_obj = models.Course.objects.get(id=i)#课程对象
                info['content']['course']['%s'%course_obj.pk] = {'name':course_obj.name,'default':i,'policy':ShopPriceJson(instance=course_obj.price_policy,many=True).data}
        except:
            info = {'code': 400, 'msg': '获取数据错误', 'content': {'course': {}}}  # 返回的数据
        return Response(info)

    def post(self,request,*args,**kwargs):
        """ 增加购物车信息 """

        info = {'code':200,'msg':'','content':''}   #状态信息
        nid = '1'   #用户id
        pid = '1'   #价格与课程表id
        if not nid:
            info = {'code': 401, 'msg': '尚未登陆', 'content': ''}  # 状态信息
            return Response(info)
        try:
            obj = models.PricePolicy.objects.get(pk=pid) #课程对象
            if r.hget('price_user_%s'%nid,str(obj.pk)):
                info = {'code': 204, 'msg': '', 'content': '更新数据'}  # 状态信息
            r.hset('price_user_%s'%nid,obj.pk,pid)  #增加数据格式：price_user_用户id；课程id；价格与课程表id
        except:
            info = {'code': 400, 'msg': '添加出错', 'content': ''}

        return Response(info)

    def delete(self,request,*args,**kwargs):
        """ 删除购物车信息 """
        info = {'code': 200, 'msg': '', 'content': '删除数据'}  # 状态信息
        nid = '1' #用户id
        pid = '3' #课程与课程表id
        try:
            obj = models.PricePolicy.objects.get(pk=pid)  # 课程对象
            r.hdel('price_user_%s'%nid,obj.pk)  #删除数据
        except:
            info = {'code': 400, 'msg': '删除出错', 'content': ''}  # 状态信息
        return Response(info)

    def put(self,request,*args,**kwargs):
        """ 更新购物车信息 """
        nid = '1'   #用户id
        pid = '1'   #价格与课程表id
        info = {'code': 200, 'msg': '', 'content': '更新数据'}  # 状态信息
        try:
            obj = models.PricePolicy.objects.get(pk=pid)  # 课程对象
            if r.hget('price_user_%s' % nid, str(obj.pk)):  #数据存在,则更新操作
                r.hset('price_user_%s' % nid, obj.pk, pid)  # 增加数据格式：price_user_用户id；课程id；价格与课程表id
            else:
                info = {'code': 410, 'msg': '数据不存在', 'content': ''}
        except:
            info = {'code': 400, 'msg': '更新出错', 'content': ''}

        return Response(info)